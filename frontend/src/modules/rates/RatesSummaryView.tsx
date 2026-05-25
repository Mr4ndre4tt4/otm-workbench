import { useState, type FormEvent } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { ApiError } from "../../platform/api";
import {
  addRateBatchTables,
  approveRateBatch,
  createRateBatch,
  downloadBackendArtifact,
  executeBackendAction,
  exportRateBatchCsv,
  previewRateBatchCsv,
  useRateBatchArtifacts,
  useRateBatchDetail,
  useRateBatchEvidence,
  useRatesSummary
} from "../../platform/hooks";
import type { AvailableAction, RateBatchCsvPreview, RatesSummaryItem } from "../../platform/types";
import { ActionBar, PageHeader } from "../../app/shell";
import {
  ArtifactList,
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
} from "../../ui/components";

function severityStatus(severity: string) {
  if (severity === "success") return "READY";
  if (severity === "warning") return "BLOCKED";
  if (severity === "danger") return "ERROR";
  return "INFO";
}

function rateBatchMeta(batch: RatesSummaryItem) {
  const issueCount = Object.values(batch.summary.issue_summary).reduce((total, value) => total + value, 0);
  return [`${batch.summary.table_count} table(s)`, `${batch.summary.row_count} row(s)`, `${issueCount} issue(s)`];
}

export function RatesSummaryView({ token }: { token: string }) {
  const queryClient = useQueryClient();
  const rates = useRatesSummary(token);
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [isCreateFormOpen, setIsCreateFormOpen] = useState(false);
  const [newBatchScenario, setNewBatchScenario] = useState("RATE_GEO_ONLY");
  const [newBatchName, setNewBatchName] = useState("Synthetic rate package");
  const [newBatchDomain, setNewBatchDomain] = useState("OTM1");
  const [tableName, setTableName] = useState("X_LANE");
  const [rowGid, setRowGid] = useState("OTM1.XL_SYN_001");
  const [rowValue, setRowValue] = useState("XL_SYN_001");
  const [csvPreviews, setCsvPreviews] = useState<RateBatchCsvPreview[]>([]);
  const [approvalAction, setApprovalAction] = useState<AvailableAction | null>(null);
  const [approvalNote, setApprovalNote] = useState("");
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [runningActionKey, setRunningActionKey] = useState<string | null>(null);
  const [downloadingArtifactId, setDownloadingArtifactId] = useState<string | null>(null);
  const recentObjects = rates.data?.recent_objects ?? [];
  const effectiveBatchId = selectedBatchId ?? recentObjects[0]?.id ?? null;
  const batchDetail = useRateBatchDetail(token, effectiveBatchId);
  const batchArtifacts = useRateBatchArtifacts(token, effectiveBatchId);
  const batchEvidence = useRateBatchEvidence(token, effectiveBatchId);

  if (rates.isLoading) {
    return <StatePanel>Loading Rates Studio...</StatePanel>;
  }

  if (rates.isError || !rates.data) {
    return <StatePanel tone="error">Rates Studio summary is unavailable.</StatePanel>;
  }

  const data = rates.data;

  function clearBatchWorkspaceState() {
    setCsvPreviews([]);
    setApprovalAction(null);
    setApprovalNote("");
    setActionMessage(null);
    setActionError(null);
    setRunningActionKey(null);
    setDownloadingArtifactId(null);
  }

  function selectBatch(batchId: string) {
    if (batchId === effectiveBatchId) return;
    setSelectedBatchId(batchId);
    clearBatchWorkspaceState();
  }

  function runModuleAction(action: AvailableAction) {
    if (action.key === "create_batch" && !action.disabled) {
      setActionMessage(null);
      setActionError(null);
      setIsCreateFormOpen(true);
    }
  }

  async function runBatchAction(action: AvailableAction) {
    if (action.method !== "POST" || action.disabled) return;
    setActionMessage(null);
    setActionError(null);
    if (action.key === "approve" && action.requires_confirmation) {
      setApprovalAction(action);
      setApprovalNote("");
      return;
    }
    setRunningActionKey(action.key);
    try {
      await executeBackendAction(token, action.href);
      setActionMessage(`${action.label} completed.`);
      if (action.result_hint === "refresh_object" || action.result_hint === "refresh_list") {
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: ["modules", "rates", "summary"] }),
          queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches", effectiveBatchId] })
        ]);
      }
    } catch (caught) {
      if (caught instanceof ApiError) {
        setActionError(caught.message);
      } else {
        setActionError(`${action.label} failed.`);
      }
    } finally {
      setRunningActionKey(null);
    }
  }

  async function downloadArtifact(artifactId: string, href: string, fallbackName: string) {
    setActionMessage(null);
    setActionError(null);
    setDownloadingArtifactId(artifactId);
    try {
      const result = await downloadBackendArtifact(token, href);
      const objectUrl = URL.createObjectURL(result.blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = result.filename ?? fallbackName;
      link.click();
      URL.revokeObjectURL(objectUrl);
      setActionMessage(`Download started: ${result.filename ?? fallbackName}.`);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setActionError(caught.message);
      } else {
        setActionError("Download failed.");
      }
    } finally {
      setDownloadingArtifactId(null);
    }
  }

  async function createBatch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionMessage(null);
    setActionError(null);
    setRunningActionKey("create_batch");
    try {
      const created = await createRateBatch(token, {
        scenario_code: newBatchScenario,
        name: newBatchName.trim(),
        domain_name: newBatchDomain.trim(),
        description: "",
        source_type: "api"
      });
      setSelectedBatchId(created.id);
      setCsvPreviews([]);
      setIsCreateFormOpen(false);
      setActionMessage("Rate batch created.");
      await queryClient.invalidateQueries({ queryKey: ["modules", "rates", "summary"] });
    } catch (caught) {
      if (caught instanceof ApiError) {
        setActionError(caught.message);
      } else {
        setActionError("Create rate batch failed.");
      }
    } finally {
      setRunningActionKey(null);
    }
  }

  async function approveBatch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!effectiveBatchId || !approvalAction) return;
    setActionMessage(null);
    setActionError(null);
    setRunningActionKey(approvalAction.key);
    try {
      await approveRateBatch(token, effectiveBatchId, { approval_note: approvalNote.trim() });
      setApprovalAction(null);
      setApprovalNote("");
      setActionMessage(`${approvalAction.label} completed.`);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "summary"] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches", effectiveBatchId] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches", effectiveBatchId, "evidence"] })
      ]);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setActionError(caught.message);
      } else {
        setActionError(`${approvalAction.label} failed.`);
      }
    } finally {
      setRunningActionKey(null);
    }
  }

  function stagedRowPayload(): Record<string, string | number | null> {
    if (tableName === "ACCESSORIAL_COST") {
      return {
        ACCESSORIAL_COST_GID: rowGid.trim(),
        COST_CODE_GID: rowValue.trim()
      };
    }
    return {
      X_LANE_GID: rowGid.trim(),
      X_LANE_XID: rowValue.trim()
    };
  }

  async function addTableRow(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!effectiveBatchId) return;
    setActionMessage(null);
    setActionError(null);
    setRunningActionKey("add_table_row");
    try {
      await addRateBatchTables(token, effectiveBatchId, {
        tables: [
          {
            table_name: tableName,
            rows: [stagedRowPayload()]
          }
        ]
      });
      setCsvPreviews([]);
      setActionMessage("Table row staged.");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "summary"] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches", effectiveBatchId] })
      ]);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setActionError(caught.message);
      } else {
        setActionError("Add table row failed.");
      }
    } finally {
      setRunningActionKey(null);
    }
  }

  async function previewCsv() {
    if (!effectiveBatchId) return;
    setActionMessage(null);
    setActionError(null);
    setRunningActionKey("preview_csv");
    try {
      const result = await previewRateBatchCsv(token, effectiveBatchId);
      setCsvPreviews(result.previews);
      setActionMessage("CSV preview ready.");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "summary"] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches", effectiveBatchId] })
      ]);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setActionError(caught.message);
      } else {
        setActionError("CSV preview failed.");
      }
    } finally {
      setRunningActionKey(null);
    }
  }

  async function exportCsv() {
    if (!effectiveBatchId) return;
    setActionMessage(null);
    setActionError(null);
    setRunningActionKey("export_csv");
    try {
      const result = await exportRateBatchCsv(token, effectiveBatchId);
      setActionMessage(`CSV export created: ${result.file_name}.`);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "summary"] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches", effectiveBatchId] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches", effectiveBatchId, "artifacts"] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches", effectiveBatchId, "evidence"] })
      ]);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setActionError(caught.message);
      } else {
        setActionError("CSV export failed.");
      }
    } finally {
      setRunningActionKey(null);
    }
  }

  return (
    <>
      <PageHeader
        actions={data.available_actions}
        description={data.description}
        label="Module workspace"
        onAction={runModuleAction}
        title={data.title}
      />

      {isCreateFormOpen ? (
        <section className="panel rate-batch-form-panel" aria-label="New rate batch form">
          <div className="panel-header">
            <h2>New rate batch</h2>
          </div>
          <form className="rate-batch-form" onSubmit={(event) => void createBatch(event)}>
            <label>
              Scenario
              <select value={newBatchScenario} onChange={(event) => setNewBatchScenario(event.target.value)}>
                <option value="RATE_GEO_ONLY">RATE_GEO_ONLY</option>
                <option value="ACCESSORIAL_ONLY">ACCESSORIAL_ONLY</option>
              </select>
            </label>
            <label>
              Batch name
              <input
                required
                value={newBatchName}
                onChange={(event) => setNewBatchName(event.target.value)}
              />
            </label>
            <label>
              Domain
              <input required value={newBatchDomain} onChange={(event) => setNewBatchDomain(event.target.value)} />
            </label>
            <div className="rate-batch-form-actions">
              <Button disabled={runningActionKey === "create_batch"} type="submit" variant="primary">
                {runningActionKey === "create_batch" ? "Creating..." : "Create batch"}
              </Button>
              <Button disabled={runningActionKey === "create_batch"} onClick={() => setIsCreateFormOpen(false)}>
                Cancel
              </Button>
            </div>
          </form>
        </section>
      ) : null}

      <MetricGrid
        ariaLabel="Rates summary metrics"
        items={data.counts.map((count) => ({
          key: count.key,
          label: count.label,
          status: severityStatus(count.severity),
          value: count.value
        }))}
      />

      <ModuleWorkspaceLayout
        ariaLabel="Rates Studio workspace"
        side={
          <SelectedObjectPanel
            ariaLabel="Selected rate batch"
            actions={
              batchDetail.data ? (
                <ActionBar
                  actions={batchDetail.data.available_actions}
                  onAction={(action) => void runBatchAction(action)}
                  runningActionKey={runningActionKey}
                />
              ) : null
            }
            emptyText="Select a rate batch to inspect backend-owned details."
            fields={
              batchDetail.data
                ? [
                    { label: "Domain", value: batchDetail.data.domain_name },
                    { label: "Macro object", value: batchDetail.data.catalog_macro_object_code },
                    { label: "Tables", value: batchDetail.data.tables.length }
                  ]
                : []
            }
            isLoading={batchDetail.isLoading && Boolean(effectiveBatchId)}
            loadingText="Loading selected batch..."
            status={batchDetail.data?.status ?? "PENDING"}
            subtitle={batchDetail.data?.scenario_code}
            title={batchDetail.data?.name}
          >
            {actionMessage ? <FeedbackMessage tone="success">{actionMessage}</FeedbackMessage> : null}
            {actionError ? <FeedbackMessage tone="error">{actionError}</FeedbackMessage> : null}
            {approvalAction ? (
              <form className="rate-batch-form rate-approval-form" onSubmit={(event) => void approveBatch(event)}>
                <h2>Confirm rate batch approval</h2>
                <label>
                  Approval note
                  <textarea
                    required
                    rows={3}
                    value={approvalNote}
                    onChange={(event) => setApprovalNote(event.target.value)}
                  />
                </label>
                <div className="rate-batch-form-actions">
                  <Button disabled={runningActionKey === approvalAction.key} type="submit" variant="primary">
                    {runningActionKey === approvalAction.key ? "Approving..." : "Confirm approval"}
                  </Button>
                  <Button
                    disabled={runningActionKey === approvalAction.key}
                    onClick={() => {
                      setApprovalAction(null);
                      setApprovalNote("");
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            ) : null}
            <DetailList
              ariaLabel="Selected batch tables"
              emptyText="No tables have been staged for this batch."
              items={(batchDetail.data?.tables ?? []).map((table) => ({
                id: table.id,
                meta: [`${table.row_count} row(s)`],
                status: table.status,
                title: table.table_name
              }))}
            />
            {batchDetail.data ? (
              <form className="rate-batch-form rate-table-form" onSubmit={(event) => void addTableRow(event)}>
                <h2>Stage table row</h2>
                <label>
                  Table
                  <select value={tableName} onChange={(event) => setTableName(event.target.value)}>
                    <option value="X_LANE">X_LANE</option>
                    <option value="ACCESSORIAL_COST">ACCESSORIAL_COST</option>
                  </select>
                </label>
                <label>
                  Row GID
                  <input required value={rowGid} onChange={(event) => setRowGid(event.target.value)} />
                </label>
                <label>
                  Row value
                  <input required value={rowValue} onChange={(event) => setRowValue(event.target.value)} />
                </label>
                <div className="rate-batch-form-actions">
                  <Button disabled={runningActionKey === "add_table_row"} type="submit" variant="primary">
                    {runningActionKey === "add_table_row" ? "Adding..." : "Add table row"}
                  </Button>
                </div>
              </form>
            ) : null}
            {batchDetail.data ? (
              <div className="rate-preview-actions">
                <Button
                  disabled={runningActionKey === "preview_csv" || batchDetail.data.tables.length === 0}
                  onClick={() => void previewCsv()}
                  variant="secondary"
                >
                  {runningActionKey === "preview_csv" ? "Previewing..." : "Preview CSV"}
                </Button>
                <Button
                  disabled={runningActionKey === "export_csv" || csvPreviews.length === 0}
                  onClick={() => void exportCsv()}
                  variant="secondary"
                >
                  {runningActionKey === "export_csv" ? "Exporting..." : "Export CSV"}
                </Button>
              </div>
            ) : null}
            {csvPreviews.length ? (
              <div className="csv-preview-stack" aria-label="CSV preview output">
                {csvPreviews.map((preview) => (
                  <div className="csv-preview-item" key={preview.table_name}>
                    <strong>{preview.table_name}</strong>
                    <pre>{preview.content}</pre>
                  </div>
                ))}
              </div>
            ) : null}
          </SelectedObjectPanel>
        }
        status={data.recent_objects.length ? "ACTIVE" : "EMPTY"}
        title="Recent rate batches"
      >
        <ModuleObjectList
          ariaLabel="Rate batches"
          emptyText="No rate batches available for the current context."
          items={data.recent_objects.map((batch) => ({
            id: batch.id,
            meta: rateBatchMeta(batch),
            status: batch.status,
            subtitle: batch.code,
            title: batch.display_name
          }))}
          onSelect={selectBatch}
          selectedId={effectiveBatchId}
        />
      </ModuleWorkspaceLayout>

      <BlockerPanel
        emptyText="No open blockers in the current rates summary."
        items={data.open_blockers.map((blocker) => ({
          codes: blocker.codes,
          id: `${blocker.object_type}-${blocker.object_id}`,
          message: blocker.message
        }))}
        title="Open blockers"
      />

      <section className="activity-layout">
        <OperationalPanel
          ariaLabel="Rate batch export artifacts"
          emptyText="No export artifacts registered for this batch."
          hasItems={(batchArtifacts.data?.items.length ?? 0) > 0}
          isLoading={batchArtifacts.isLoading && Boolean(effectiveBatchId)}
          loadingText="Loading artifacts..."
          status={batchArtifacts.data?.total ? "ACTIVE" : "EMPTY"}
          title="Batch artifacts"
        >
          <ArtifactList
            items={(batchArtifacts.data?.items ?? []).map((artifact) => ({
              action: artifact.download_url ? (
                  <Button
                    disabled={downloadingArtifactId === artifact.id}
                    onClick={() => void downloadArtifact(artifact.id, artifact.download_url!, artifact.file_name)}
                  >
                    {downloadingArtifactId === artifact.id ? "Downloading..." : "Download"}
                  </Button>
                ) : undefined,
              id: artifact.id,
              meta: [artifact.content_type, `${artifact.size_bytes} bytes`],
              status: artifact.download_url ? undefined : artifact.sensitivity_level,
              subtitle: artifact.artifact_type,
              title: artifact.file_name
            }))}
          />
        </OperationalPanel>

        <OperationalPanel
          ariaLabel="Rate batch evidence"
          emptyText="No evidence registered for this batch."
          hasItems={(batchEvidence.data?.items.length ?? 0) > 0}
          isLoading={batchEvidence.isLoading && Boolean(effectiveBatchId)}
          loadingText="Loading evidence..."
          status={batchEvidence.data?.total ? "ACTIVE" : "EMPTY"}
          title="Batch evidence"
        >
          <ArtifactList
            items={(batchEvidence.data?.items ?? []).map((evidence) => ({
              id: evidence.id,
              meta: [evidence.artifact_id ? "Artifact linked" : "No artifact", evidence.client_safe ? "Client safe" : "Internal"],
              status: evidence.status,
              subtitle: evidence.sensitivity_level,
              title: evidence.evidence_type
            }))}
          />
        </OperationalPanel>
      </section>
    </>
  );
}
