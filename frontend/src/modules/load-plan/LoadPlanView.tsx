import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import {
  buildCsvutilFromCutoverChecklist,
  commitCutoverHandoff,
  createEvidenceArchivePackage,
  createCutoverChecklistFromPackage,
  decideCutoverGoNoGo,
  decideLoadPlanReviewItem,
  downloadEvidenceArtifact,
  exportCutoverChecklistPackage,
  exportLoadPlanCutoverReadiness,
  generateCutoverChecklistReadiness,
  generateLoadPlanCutoverReadiness,
  generateLoadPlanSequenceSnapshot,
  generateReviewQueueFromZipAnalysis,
  runLoadPlanZipAnalysis,
  updateCutoverChecklistItem,
  useCutoverHandoffEligibility,
  useLoadPlanPackageDetail,
  useLoadPlanPackages,
  useLoadPlanReviewQueue,
  useLoadPlanSummary
} from '../../platform/hooks';
import type {
  CsvutilBuild,
  CutoverGoNoGoDecision,
  CutoverHandoffCommit,
  CutoverPackageExport,
  CutoverChecklist,
  CutoverChecklistReadiness,
  EvidenceArchivePackageResponse,
  LoadPlanCutoverReadiness,
  LoadPlanPackage,
  LoadPlanReadinessExport,
  LoadPlanReviewItem,
  LoadPlanSequenceSnapshot,
  LoadPlanZipAnalysis
} from '../../platform/types';
import { PageHeader } from '../../app/shell';
import {
  BlockerPanel,
  Button,
  DetailList,
  ArtifactList,
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
  { id: "zip-review", title: "ZIP review", status: "5" },
  { id: "sequence", title: "Sequence", status: "6" },
  { id: "exports", title: "Exports", status: "7" },
  { id: "handoff", title: "Handoff", status: "8" }
] as const;

type LoadPlanWorkflowStage = (typeof loadPlanWorkflowStages)[number]["id"];

const defaultEvidenceId = "SYN_EVIDENCE_001";

export function LoadPlanView({ token }: { token: string }) {
  const queryClient = useQueryClient();
  const summary = useLoadPlanSummary(token);
  const packages = useLoadPlanPackages(token);
  const [selectedPackageId, setSelectedPackageId] = useState<string | null>(null);
  const [activeStage, setActiveStage] = useState<LoadPlanWorkflowStage>("packages");
  const [checklist, setChecklist] = useState<CutoverChecklist | null>(null);
  const [readiness, setReadiness] = useState<CutoverChecklistReadiness | null>(null);
  const [csvutilBuild, setCsvutilBuild] = useState<CsvutilBuild | null>(null);
  const [zipAnalysis, setZipAnalysis] = useState<LoadPlanZipAnalysis | null>(null);
  const [reviewItems, setReviewItems] = useState<LoadPlanReviewItem[]>([]);
  const [sequenceSnapshot, setSequenceSnapshot] = useState<LoadPlanSequenceSnapshot | null>(null);
  const [packageReadiness, setPackageReadiness] = useState<LoadPlanCutoverReadiness | null>(null);
  const [readinessExport, setReadinessExport] = useState<LoadPlanReadinessExport | null>(null);
  const [cutoverPackageExport, setCutoverPackageExport] = useState<CutoverPackageExport | null>(null);
  const [goNoGoDecision, setGoNoGoDecision] = useState<CutoverGoNoGoDecision | null>(null);
  const [handoffCommit, setHandoffCommit] = useState<CutoverHandoffCommit | null>(null);
  const [readinessArchivePackage, setReadinessArchivePackage] = useState<EvidenceArchivePackageResponse | null>(null);
  const [operationMessage, setOperationMessage] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [isMutating, setIsMutating] = useState(false);
  const [downloadingArtifactId, setDownloadingArtifactId] = useState<string | null>(null);
  const [evidenceId, setEvidenceId] = useState(defaultEvidenceId);
  const packageItems = packages.data?.items ?? [];
  const effectivePackageId = selectedPackageId ?? packageItems[0]?.id ?? null;
  const packageDetail = useLoadPlanPackageDetail(token, effectivePackageId);
  const handoffEligibility = useCutoverHandoffEligibility(token, effectivePackageId);
  const reviewQueue = useLoadPlanReviewQueue(token, effectivePackageId);
  const selectedPackage = packageDetail.data;
  const sourceModuleCount = Object.keys(summary.data?.by_source_module ?? {}).length;
  const catalogMacroCount = Object.keys(summary.data?.by_catalog_macro_object ?? {}).length;
  const registeredCount = summary.data?.registered_packages ?? 0;
  const sequenceRowCount =
    selectedPackage?.summary.row_count ??
    selectedPackage?.load_sequence.reduce((total, sequenceItem) => total + sequenceItem.row_count, 0) ??
    0;
  const effectiveReviewItems = reviewItems.length ? reviewItems : reviewQueue.data?.items ?? [];
  const sequenceNextActions = Array.isArray(sequenceSnapshot?.summary.next_actions)
    ? sequenceSnapshot.summary.next_actions.map(String)
    : [];

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

  const resetEvidenceDraft = () => {
    setEvidenceId(defaultEvidenceId);
    setOperationMessage(null);
    setOperationError(null);
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

  const handleRunZipAnalysis = async () => {
    if (!effectivePackageId) return;
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await runLoadPlanZipAnalysis(token, effectivePackageId);
      setZipAnalysis(result);
      setOperationMessage(`ZIP analysis ${result.id} is ${result.status}.`);
      setActiveStage("zip-review");
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not run ZIP analysis.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleGenerateReviewQueue = async () => {
    if (!zipAnalysis) return;
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await generateReviewQueueFromZipAnalysis(token, zipAnalysis.id);
      setReviewItems(result.items);
      await queryClient.invalidateQueries({ queryKey: ["modules", "load-plan", "review-queue", effectivePackageId] });
      setOperationMessage(`Review queue generated with ${result.created_count} new item(s).`);
      setActiveStage("zip-review");
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not generate review queue.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleConfirmReviewItem = async (itemId: string) => {
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await decideLoadPlanReviewItem(token, itemId, {
        decision_note: "Synthetic UI review.",
        decision_status: "CONFIRMED"
      });
      setReviewItems((items) => items.map((item) => (item.id === result.review_item_id ? result.review_item : item)));
      await queryClient.invalidateQueries({ queryKey: ["modules", "load-plan", "review-queue", effectivePackageId] });
      setOperationMessage(`Review item ${result.review_item_id} decided as ${result.decision_status}.`);
      setActiveStage("zip-review");
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not decide review item.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleGeneratePackageReadiness = async () => {
    if (!effectivePackageId) return;
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await generateLoadPlanCutoverReadiness(token, effectivePackageId);
      const item = result.items[0] ?? null;
      setPackageReadiness(item);
      if (item) {
        setOperationMessage(`Package readiness ${item.id} is ${item.status}.`);
      } else {
        setOperationMessage("Package readiness generation returned no items.");
      }
      setActiveStage("exports");
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not generate package readiness.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleGenerateSequenceSnapshot = async () => {
    if (!effectivePackageId) return;
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await generateLoadPlanSequenceSnapshot(token, effectivePackageId);
      setSequenceSnapshot(result);
      setOperationMessage(`Sequence snapshot ${result.id} is ${result.status}.`);
      setActiveStage("sequence");
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not generate sequence snapshot.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleExportReadiness = async () => {
    if (!packageReadiness) return;
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await exportLoadPlanCutoverReadiness(token, packageReadiness.id);
      setReadinessExport(result);
      await queryClient.invalidateQueries({
        queryKey: ["modules", "load-plan", "cutover-handoff", "eligibility", effectivePackageId]
      });
      setOperationMessage(`Readiness export ${result.id} is ${result.status}.`);
      setActiveStage("exports");
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not export readiness.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleExportCutoverPackage = async () => {
    if (!checklist) return;
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await exportCutoverChecklistPackage(token, checklist.id);
      setCutoverPackageExport(result);
      setOperationMessage(`Cutover package export is ${result.status}.`);
      setActiveStage("exports");
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not export cutover package.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleArchiveReadinessExport = async () => {
    if (!readinessExport) return;
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await createEvidenceArchivePackage(token, {
        evidence_type: "load_plan_readiness_export",
        sensitivity_level: "client_safe",
        source_module: "load_plan",
        status: "CREATED"
      });
      setReadinessArchivePackage(result);
      await queryClient.invalidateQueries({
        queryKey: ["modules", "load-plan", "cutover-handoff", "eligibility", effectivePackageId]
      });
      setOperationMessage(`Readiness export archive ${result.file_name} created.`);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not archive readiness export evidence.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleDownloadArtifact = async (artifactId: string | null, fallbackName: string) => {
    if (!artifactId) return;
    setIsMutating(true);
    setDownloadingArtifactId(artifactId);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await downloadEvidenceArtifact(token, artifactId);
      const objectUrl = URL.createObjectURL(result.blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = result.filename ?? fallbackName;
      anchor.click();
      URL.revokeObjectURL(objectUrl);
      setOperationMessage(`Download started: ${result.filename ?? fallbackName}.`);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not download Load Plan artifact.");
    } finally {
      setDownloadingArtifactId(null);
      setIsMutating(false);
    }
  };

  const handleDecideGoNoGo = async () => {
    if (!checklist) return;
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await decideCutoverGoNoGo(token, checklist.id);
      setGoNoGoDecision(result);
      await queryClient.invalidateQueries({
        queryKey: ["modules", "load-plan", "cutover-handoff", "eligibility", effectivePackageId]
      });
      setOperationMessage(`Go/No-Go decision is ${result.decision}.`);
      setActiveStage("handoff");
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not decide Go/No-Go.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCommitCutoverHandoff = async () => {
    if (!effectivePackageId) return;
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await commitCutoverHandoff(token, effectivePackageId);
      setHandoffCommit(result);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["modules", "load-plan", "packages"] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "load-plan", "package", effectivePackageId] }),
        queryClient.invalidateQueries({
          queryKey: ["modules", "load-plan", "cutover-handoff", "eligibility", effectivePackageId]
        })
      ]);
      setOperationMessage(`Cutover handoff ${result.id} committed.`);
      setActiveStage("handoff");
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not commit cutover handoff.");
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
              <Button disabled={isMutating} onClick={resetEvidenceDraft}>
                Reset evidence draft
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
              <>
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
                <ArtifactList
                  items={[
                    ...(csvutilBuild.ctl_artifact_id
                      ? [
                          {
                            action: (
                              <Button
                                disabled={downloadingArtifactId === csvutilBuild.ctl_artifact_id}
                                onClick={() =>
                                  void handleDownloadArtifact(csvutilBuild.ctl_artifact_id, "csvutil_control_file.ctl")
                                }
                              >
                                {downloadingArtifactId === csvutilBuild.ctl_artifact_id ? "Downloading..." : "Download"}
                              </Button>
                            ),
                            id: csvutilBuild.ctl_artifact_id,
                            meta: [csvutilBuild.ctl_artifact_id],
                            subtitle: "CSVUTIL control file",
                            title: "CTL artifact"
                          }
                        ]
                      : []),
                    ...(csvutilBuild.cl_artifact_id
                      ? [
                          {
                            action: (
                              <Button
                                disabled={downloadingArtifactId === csvutilBuild.cl_artifact_id}
                                onClick={() =>
                                  void handleDownloadArtifact(csvutilBuild.cl_artifact_id, "csvutil_command_line.cl")
                                }
                              >
                                {downloadingArtifactId === csvutilBuild.cl_artifact_id ? "Downloading..." : "Download"}
                              </Button>
                            ),
                            id: csvutilBuild.cl_artifact_id,
                            meta: [csvutilBuild.cl_artifact_id],
                            subtitle: "CSVUTIL command file",
                            title: "CL artifact"
                          }
                        ]
                      : [])
                  ]}
                />
              </>
            ) : null}
          </OperationalPanel>
        ) : null}

        {activeStage === "zip-review" ? (
          <OperationalPanel
            ariaLabel="ZIP analysis and review queue"
            emptyText="Run ZIP analysis on the selected package before generating review items."
            hasItems
            status={zipAnalysis?.status ?? "PENDING"}
            title="ZIP review"
          >
            <div className="load-plan-action-bar">
              <Button disabled={!effectivePackageId || isMutating} onClick={() => void handleRunZipAnalysis()} variant="primary">
                Run ZIP analysis
              </Button>
              <Button disabled={!zipAnalysis || isMutating} onClick={() => void handleGenerateReviewQueue()} variant="secondary">
                Generate review queue
              </Button>
            </div>
            {zipAnalysis ? (
              <DetailList
                ariaLabel="ZIP analysis findings"
                emptyText="ZIP analysis returned no findings."
                items={
                  zipAnalysis.findings.length
                    ? zipAnalysis.findings.map((finding) => ({
                        id: `${finding.code}-${finding.table_name ?? "package"}-${finding.file_name ?? "zip"}`,
                        meta: [finding.table_name ?? "Package", finding.file_name ?? "No file", finding.message],
                        status: finding.severity,
                        title: finding.code
                      }))
                    : [
                        {
                          id: "zip-analysis-clean",
                          meta: [
                            `${zipAnalysis.summary.csv_file_count ?? 0} CSV file(s)`,
                            `${zipAnalysis.summary.row_count ?? 0} row(s)`
                          ],
                          status: zipAnalysis.status,
                          title: "No findings"
                        }
                      ]
                }
              />
            ) : null}
            <div className="table-list" aria-label="Load Plan review queue">
              {effectiveReviewItems.length ? (
                effectiveReviewItems.map((item) => (
                  <div className="table-list-item" key={item.id}>
                    <strong className="table-list-main">{item.title}</strong>
                    <div className="table-list-meta">
                      <span>{item.source_code}</span>
                      <span>{item.table_name ?? "Package"}</span>
                      <span>{item.file_name ?? "No file"}</span>
                    </div>
                    <div className="table-list-status">
                      <span className="status-chip">{item.latest_decision_status ?? item.status}</span>
                      {item.status === "PENDING_REVIEW" ? (
                        <Button disabled={isMutating} onClick={() => void handleConfirmReviewItem(item.id)} variant="secondary">
                          Confirm finding
                        </Button>
                      ) : null}
                    </div>
                  </div>
                ))
              ) : (
                <p className="empty-text">
                  {reviewQueue.isLoading ? "Loading review queue..." : "No review items for the selected package."}
                </p>
              )}
            </div>
          </OperationalPanel>
        ) : null}

        {activeStage === "sequence" ? (
          <OperationalPanel
            ariaLabel="Load Plan sequence snapshot"
            emptyText="Generate a sequence snapshot before export and handoff."
            hasItems
            status={sequenceSnapshot?.status ?? "PENDING"}
            title="Sequence"
          >
            <div className="load-plan-action-bar">
              <Button disabled={!effectivePackageId || isMutating} onClick={() => void handleGenerateSequenceSnapshot()} variant="primary">
                Generate sequence snapshot
              </Button>
            </div>
            <DetailList
              ariaLabel="Load Plan sequence blockers"
              emptyText="No sequence blockers found for the selected package."
              items={[
                ...(sequenceSnapshot?.blockers ?? []).map((blocker, index) => ({
                  id: `${blocker.code}-${blocker.table_name ?? "package"}-${index}`,
                  meta: [blocker.table_name ?? "Package", blocker.message],
                  status: blocker.severity,
                  title: blocker.code
                })),
                ...(sequenceNextActions.length
                  ? [
                      {
                        id: "sequence-next-actions",
                        meta: sequenceNextActions,
                        status: "NEXT",
                        title: "Next actions"
                      }
                    ]
                  : [])
              ]}
            />
          </OperationalPanel>
        ) : null}

        {activeStage === "exports" ? (
          <OperationalPanel
            ariaLabel="Load Plan export artifacts"
            emptyText="Generate package readiness before exporting readiness and cutover package artifacts."
            hasItems
            status={cutoverPackageExport?.status ?? readinessExport?.status ?? packageReadiness?.status ?? "PENDING"}
            title="Exports"
          >
            <div className="load-plan-action-bar">
              <Button disabled={!effectivePackageId || isMutating} onClick={() => void handleGeneratePackageReadiness()} variant="primary">
                Generate package readiness
              </Button>
              <Button disabled={!packageReadiness || isMutating} onClick={() => void handleExportReadiness()} variant="secondary">
                Export readiness
              </Button>
              <Button disabled={!checklist || isMutating} onClick={() => void handleExportCutoverPackage()} variant="secondary">
                Export cutover package
              </Button>
              <Button disabled={!readinessExport || isMutating} onClick={() => void handleArchiveReadinessExport()} variant="secondary">
                Archive readiness export
              </Button>
            </div>
            <DetailList
              ariaLabel="Load Plan export ids"
              emptyText="No export artifacts generated for this route session."
              items={[
                ...(packageReadiness
                  ? [
                      {
                        id: "package-readiness",
                        meta: [packageReadiness.evidence_id ?? "Missing readiness evidence"],
                        status: packageReadiness.status,
                        title: "Package readiness"
                      }
                    ]
                  : []),
                ...(readinessExport
                  ? [
                      {
                        id: "readiness-export",
                        meta: [
                          readinessExport.artifact_id ?? "Missing artifact",
                          readinessExport.manifest_id ?? "Missing manifest",
                          readinessExport.evidence_id ?? "Missing evidence"
                        ],
                        status: readinessExport.status,
                        title: "Readiness export"
                      }
                    ]
                  : []),
                ...(cutoverPackageExport
                  ? [
                      {
                        id: "cutover-package-export",
                        meta: [
                          cutoverPackageExport.artifact_id ?? "Missing artifact",
                          cutoverPackageExport.manifest_id ?? "Missing manifest",
                          cutoverPackageExport.evidence_id ?? "Missing evidence"
                        ],
                        status: cutoverPackageExport.status,
                        title: "Cutover package"
                      }
                    ]
                  : [])
              ]}
            />
            {readinessArchivePackage ? (
              <DetailList
                ariaLabel="Load Plan readiness archive package"
                items={[
                  {
                    id: readinessArchivePackage.archive_id,
                    meta: [
                      readinessArchivePackage.evidence_id,
                      readinessArchivePackage.manifest_id,
                      `${readinessArchivePackage.summary.evidence_count ?? 0} evidence item(s)`
                    ],
                    status: "CREATED",
                    title: readinessArchivePackage.file_name
                  }
                ]}
              />
            ) : null}
            <ArtifactList
              items={[
                ...(readinessExport?.artifact_id
                  ? [
                      {
                        action: (
                          <Button
                            disabled={downloadingArtifactId === readinessExport.artifact_id}
                            onClick={() =>
                              void handleDownloadArtifact(readinessExport.artifact_id, "load_plan_readiness_export.zip")
                            }
                          >
                            {downloadingArtifactId === readinessExport.artifact_id ? "Downloading..." : "Download"}
                          </Button>
                        ),
                        id: readinessExport.artifact_id,
                        meta: [readinessExport.evidence_id ?? "Missing evidence", readinessExport.status],
                        subtitle: "Readiness ZIP",
                        title: "Readiness export"
                      }
                    ]
                  : []),
                ...(cutoverPackageExport?.artifact_id
                  ? [
                      {
                        action: (
                          <Button
                            disabled={downloadingArtifactId === cutoverPackageExport.artifact_id}
                            onClick={() =>
                              void handleDownloadArtifact(
                                cutoverPackageExport.artifact_id,
                                cutoverPackageExport.file_name ?? "load_plan_cutover_package.zip"
                              )
                            }
                          >
                            {downloadingArtifactId === cutoverPackageExport.artifact_id ? "Downloading..." : "Download"}
                          </Button>
                        ),
                        id: cutoverPackageExport.artifact_id,
                        meta: [
                          cutoverPackageExport.evidence_id ?? "Missing evidence",
                          cutoverPackageExport.content_type ?? "application/octet-stream"
                        ],
                        subtitle: "Cutover package",
                        title: cutoverPackageExport.file_name ?? "Cutover package"
                      }
                    ]
                  : [])
              ]}
            />
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
            <div className="load-plan-action-bar">
              <Button disabled={!checklist || isMutating} onClick={() => void handleDecideGoNoGo()} variant="primary">
                Decide Go/No-Go
              </Button>
              <Button
                disabled={!handoffEligibility.data?.eligible || isMutating}
                onClick={() => void handleCommitCutoverHandoff()}
                variant="secondary"
              >
                Commit cutover handoff
              </Button>
            </div>
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
                {goNoGoDecision ? (
                  <DetailList
                    ariaLabel="Cutover go no-go decision"
                    items={[
                      {
                        id: "go-no-go-decision",
                        meta: [
                          goNoGoDecision.evidence_id ?? "Missing decision evidence",
                          goNoGoDecision.readiness_status ?? "No checklist readiness",
                          goNoGoDecision.cutover_package_evidence_id ?? "No cutover package evidence"
                        ],
                        status: goNoGoDecision.decision,
                        title: "Decision"
                      }
                    ]}
                  />
                ) : null}
                {handoffCommit ? (
                  <DetailList
                    ariaLabel="Cutover handoff commit"
                    items={[
                      {
                        id: handoffCommit.id,
                        meta: [
                          handoffCommit.evidence_id ?? "Missing handoff evidence",
                          handoffCommit.archive_evidence_id,
                          handoffCommit.committed_by ?? "Unknown committer"
                        ],
                        status: handoffCommit.status,
                        title: handoffCommit.package_id
                      }
                    ]}
                  />
                ) : null}
              </>
            ) : null}
          </OperationalPanel>
        ) : null}
      </ModuleWorkspaceLayout>
    </>
  );
}
