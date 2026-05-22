import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import {
  buildCsvutilFromCutoverChecklist,
  createCutoverChecklistFromPackage,
  generateCutoverChecklistReadiness,
  updateCutoverChecklistItem,
  useCutoverHandoffEligibility,
  useLoadPlanPackageDetail,
  useLoadPlanPackages,
  useLoadPlanSummary
} from '../../platform/hooks';
import type { CsvutilBuild, CutoverChecklist, CutoverChecklistReadiness, LoadPlanPackage } from '../../platform/types';
import { PageHeader } from '../../app/shell';
import {
  BlockerPanel,
  Button,
  DetailList,
  FeedbackMessage,
  MetricGrid,
  ModuleObjectList,
  ModuleWorkspaceLayout,
  OperationalPanel,
  SelectedObjectPanel,
  StatePanel
} from '../../ui/components';
import { booleanStatus } from '../moduleStatus';

function loadPlanPackageMeta(item: LoadPlanPackage) {
  const tableCount = item.summary.table_count ?? item.load_sequence.length;
  const rowCount =
    item.summary.row_count ?? item.load_sequence.reduce((total, sequenceItem) => total + sequenceItem.row_count, 0);
  return [item.source_module, item.summary.catalog_macro_object_code ?? "No catalog macro", `${tableCount} table(s)`, `${rowCount} row(s)`];
}

const loadPlanWorkflowStages = [
  { id: "packages", title: "Packages", status: "1" },
  { id: "checklist", title: "Checklist", status: "2" },
  { id: "readiness", title: "Readiness", status: "3" },
  { id: "csvutil", title: "CSVUTIL", status: "4" },
  { id: "handoff", title: "Handoff", status: "5" }
] as const;

type LoadPlanWorkflowStage = (typeof loadPlanWorkflowStages)[number]["id"];

export function LoadPlanView({ token }: { token: string }) {
  const queryClient = useQueryClient();
  const summary = useLoadPlanSummary(token);
  const packages = useLoadPlanPackages(token);
  const [selectedPackageId, setSelectedPackageId] = useState<string | null>(null);
  const [activeStage, setActiveStage] = useState<LoadPlanWorkflowStage>("packages");
  const [checklist, setChecklist] = useState<CutoverChecklist | null>(null);
  const [readiness, setReadiness] = useState<CutoverChecklistReadiness | null>(null);
  const [csvutilBuild, setCsvutilBuild] = useState<CsvutilBuild | null>(null);
  const [operationMessage, setOperationMessage] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [isMutating, setIsMutating] = useState(false);
  const [evidenceId, setEvidenceId] = useState("SYN_EVIDENCE_001");
  const packageItems = packages.data?.items ?? [];
  const effectivePackageId = selectedPackageId ?? packageItems[0]?.id ?? null;
  const packageDetail = useLoadPlanPackageDetail(token, effectivePackageId);
  const handoffEligibility = useCutoverHandoffEligibility(token, effectivePackageId);
  const selectedPackage = packageDetail.data;
  const sourceModuleCount = Object.keys(summary.data?.by_source_module ?? {}).length;
  const catalogMacroCount = Object.keys(summary.data?.by_catalog_macro_object ?? {}).length;
  const registeredCount = summary.data?.registered_packages ?? 0;
  const sequenceRowCount =
    selectedPackage?.summary.row_count ??
    selectedPackage?.load_sequence.reduce((total, sequenceItem) => total + sequenceItem.row_count, 0) ??
    0;

  const handleCreateChecklist = async () => {
    if (!effectivePackageId) return;
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const created = await createCutoverChecklistFromPackage(token, effectivePackageId);
      setChecklist(created);
      setOperationMessage(`Checklist ${created.template_code} created for selected package.`);
      setActiveStage("checklist");
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create checklist.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCompleteChecklistItem = async (itemId: string) => {
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const updated = await updateCutoverChecklistItem(token, itemId, {
        evidence_id: evidenceId.trim() || null,
        method: "CSVUTIL",
        status: "DONE"
      });
      setChecklist(updated);
      setOperationMessage("Checklist item updated.");
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not update checklist item.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleGenerateReadiness = async () => {
    if (!checklist) return;
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await generateCutoverChecklistReadiness(token, checklist.id);
      setReadiness(result);
      await queryClient.invalidateQueries({
        queryKey: ["modules", "load-plan", "cutover-handoff", "eligibility", effectivePackageId]
      });
      setOperationMessage(`Checklist readiness is ${result.status}.`);
      setActiveStage("readiness");
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not generate readiness.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleBuildCsvutil = async () => {
    if (!checklist) return;
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await buildCsvutilFromCutoverChecklist(token, checklist.id);
      setCsvutilBuild(result);
      setOperationMessage(`CSVUTIL build ${result.id} is ${result.status}.`);
      setActiveStage("csvutil");
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not build CSVUTIL artifacts.");
    } finally {
      setIsMutating(false);
    }
  };

  if (summary.isLoading || packages.isLoading) {
    return <StatePanel>Loading Load Plan...</StatePanel>;
  }

  if (summary.isError || packages.isError || !summary.data || !packages.data) {
    return <StatePanel tone="error">Load Plan is unavailable.</StatePanel>;
  }

  return (
    <>
      <PageHeader
        description="Load package intake, CSVUTIL planning, review queues, cutover readiness, and handoff controls."
        label="Module workspace"
        title="Load Plan"
      />

      <MetricGrid
        ariaLabel="Load Plan metrics"
        items={[
          { key: "registered", label: "Packages", status: booleanStatus(registeredCount), value: registeredCount },
          { key: "sources", label: "Sources", status: booleanStatus(sourceModuleCount), value: sourceModuleCount },
          { key: "catalog", label: "Catalog macros", status: booleanStatus(catalogMacroCount), value: catalogMacroCount },
          { key: "visible", label: "Visible rows", status: booleanStatus(packageItems.length), value: packageItems.length }
        ]}
      />

      <ModuleWorkspaceLayout
        ariaLabel="Load Plan workspace"
        side={
          <SelectedObjectPanel
            ariaLabel="Selected load plan package"
            emptyText="Select a Load Plan package to inspect backend-owned package metadata."
            fields={
              selectedPackage
                ? [
                    { label: "Source module", value: selectedPackage.source_module },
                    { label: "Source entity", value: selectedPackage.source_entity_type },
                    { label: "Catalog macro", value: selectedPackage.summary.catalog_macro_object_code ?? "None" },
                    { label: "Rows", value: sequenceRowCount }
                  ]
                : []
            }
            isLoading={packageDetail.isLoading && Boolean(effectivePackageId)}
            loadingText="Loading selected package..."
            status={selectedPackage?.status ?? "PENDING"}
            subtitle={selectedPackage?.summary.catalog_macro_object_code ?? selectedPackage?.source_module}
            title={selectedPackage?.package_type}
          >
            <DetailList
              ariaLabel="Selected package load sequence"
              emptyText="No load sequence available for this package."
              items={(selectedPackage?.load_sequence ?? []).map((item) => ({
                id: `${selectedPackage?.id ?? "package"}-${item.position}-${item.table_name}`,
                meta: [`Position ${item.position}`, `${item.row_count} rows`],
                status: item.requirement_level,
                title: item.table_name
              }))}
            />
          </SelectedObjectPanel>
        }
        status={packageItems.length ? "ACTIVE" : "EMPTY"}
        title="Cutover workflow"
      >
        <div className="load-plan-workflow" aria-label="Load Plan workflow">
          {loadPlanWorkflowStages.map((stage) => (
            <button
              aria-pressed={activeStage === stage.id}
              className={
                activeStage === stage.id
                  ? "load-plan-workflow-step load-plan-workflow-step-active"
                  : "load-plan-workflow-step"
              }
              key={stage.id}
              onClick={() => setActiveStage(stage.id)}
              type="button"
            >
              <span>{stage.status}</span>
              <strong>{stage.title}</strong>
            </button>
          ))}
        </div>

        {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
        {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

        {activeStage === "packages" ? (
          <ModuleObjectList
            ariaLabel="Load plan packages"
            emptyText="No Load Plan packages registered for the current context."
            items={packageItems.map((item) => ({
              id: item.id,
              meta: loadPlanPackageMeta(item),
              status: item.status,
              subtitle: item.summary.catalog_macro_object_code ?? item.source_module,
              title: item.package_type
            }))}
            onSelect={setSelectedPackageId}
            selectedId={effectivePackageId}
          />
        ) : null}

        {activeStage === "checklist" ? (
          <OperationalPanel
            ariaLabel="Cutover checklist review queue"
            emptyText="Create a checklist from the selected package to review cutover readiness items."
            hasItems
            status={checklist?.status ?? "DRAFT"}
            title="Checklist"
          >
            <div className="load-plan-action-bar">
              <label>
                Evidence id
                <input onChange={(event) => setEvidenceId(event.target.value)} value={evidenceId} />
              </label>
              <Button disabled={!effectivePackageId || isMutating} onClick={() => void handleCreateChecklist()} variant="primary">
                Create checklist
              </Button>
            </div>
            {checklist ? (
              <div className="table-list" aria-label="Cutover checklist items">
                {checklist.items.map((item) => (
                  <div className="table-list-item" key={item.id}>
                    <strong className="table-list-main">{item.title}</strong>
                    <div className="table-list-meta">
                      <span>{item.item_code}</span>
                      <span>{item.method}</span>
                      <span>{item.evidence_required ? "Evidence required" : "Evidence optional"}</span>
                    </div>
                    <div className="table-list-status">
                      {item.item_code === "TABLE_READY" ? (
                        <Button disabled={isMutating} onClick={() => void handleCompleteChecklistItem(item.id)} variant="secondary">
                          Mark CSVUTIL ready
                        </Button>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </OperationalPanel>
        ) : null}

        {activeStage === "readiness" ? (
          <OperationalPanel
            ariaLabel="Cutover readiness summary"
            emptyText="Create a checklist before generating readiness."
            hasItems
            status={readiness?.status ?? "PENDING"}
            title="Readiness"
          >
            <div className="load-plan-action-bar">
              <Button disabled={!checklist || isMutating} onClick={() => void handleGenerateReadiness()} variant="primary">
                Generate readiness
              </Button>
            </div>
            {readiness ? (
              <>
                <DetailList
                  ariaLabel="Cutover readiness counts"
                  items={[
                    {
                      id: "readiness-done",
                      meta: [`${readiness.summary.done_count} done`, `${readiness.summary.pending_count} pending`],
                      status: readiness.status,
                      title: "DONE"
                    },
                    {
                      id: "readiness-blockers",
                      meta: [`${readiness.summary.error_count} errors`, `${readiness.summary.warning_count} warnings`],
                      status: readiness.summary.ready ? "READY" : "BLOCKED",
                      title: "Blockers"
                    }
                  ]}
                />
                <BlockerPanel
                  emptyText="Checklist readiness has no blockers."
                  items={readiness.blockers.map((blocker) => ({
                    codes: [blocker.code],
                    id: blocker.item_id ?? blocker.code,
                    message: blocker.message
                  }))}
                  title="Checklist blockers"
                />
              </>
            ) : null}
          </OperationalPanel>
        ) : null}

        {activeStage === "csvutil" ? (
          <OperationalPanel
            ariaLabel="CSVUTIL build artifacts"
            emptyText="Create a cutover checklist before building CSVUTIL control artifacts."
            hasItems
            status={csvutilBuild?.status ?? "PENDING"}
            title="CSVUTIL"
          >
            <div className="load-plan-action-bar">
              <Button disabled={!checklist || isMutating} onClick={() => void handleBuildCsvutil()} variant="primary">
                Build CSVUTIL
              </Button>
            </div>
            {csvutilBuild ? (
              <DetailList
                ariaLabel="CSVUTIL artifact ids"
                items={[
                  {
                    id: "csvutil-ctl",
                    meta: [csvutilBuild.ctl_artifact_id ?? "Missing CTL artifact"],
                    status: csvutilBuild.ctl_artifact_id ? "READY" : "MISSING",
                    title: "CTL artifact"
                  },
                  {
                    id: "csvutil-cl",
                    meta: [csvutilBuild.cl_artifact_id ?? "Missing CL artifact"],
                    status: csvutilBuild.cl_artifact_id ? "READY" : "MISSING",
                    title: "CL artifact"
                  },
                  {
                    id: "csvutil-manifest",
                    meta: [csvutilBuild.manifest_id ?? "Missing manifest"],
                    status: csvutilBuild.manifest_id ? "READY" : "MISSING",
                    title: "Manifest"
                  },
                  {
                    id: "csvutil-evidence",
                    meta: [csvutilBuild.evidence_id ?? "Missing evidence"],
                    status: csvutilBuild.evidence_id ? "READY" : "MISSING",
                    title: "Evidence"
                  }
                ]}
              />
            ) : null}
          </OperationalPanel>
        ) : null}

        {activeStage === "handoff" ? (
          <OperationalPanel
            ariaLabel="Cutover handoff eligibility"
            emptyText="Select a package to inspect handoff eligibility."
            hasItems={Boolean(effectivePackageId)}
            isLoading={handoffEligibility.isLoading}
            loadingText="Loading handoff eligibility..."
            status={handoffEligibility.data?.status ?? "PENDING"}
            title="Handoff eligibility"
          >
            {handoffEligibility.data ? (
              <>
                <DetailList
                  ariaLabel="Cutover handoff eligibility facts"
                  items={[
                    {
                      id: "handoff-status",
                      meta: [
                        handoffEligibility.data.eligible ? "Eligible" : "Not eligible",
                        handoffEligibility.data.checklist_readiness_status ?? "No checklist readiness"
                      ],
                      status: handoffEligibility.data.status,
                      title: "Eligibility"
                    }
                  ]}
                />
                <BlockerPanel
                  emptyText="Handoff is eligible."
                  items={handoffEligibility.data.blockers.map((blocker) => ({
                    codes: [blocker.code],
                    id: blocker.code,
                    message: blocker.message
                  }))}
                  title="Handoff blockers"
                />
              </>
            ) : null}
          </OperationalPanel>
        ) : null}
      </ModuleWorkspaceLayout>
    </>
  );
}
