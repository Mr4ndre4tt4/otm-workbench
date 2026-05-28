import { useState, type FormEvent } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Link, useLocation, useNavigate } from "react-router-dom";

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
  useRateBatches,
  useRateBatchDetail,
  useRateBatchEvidence,
  useRateBatchIssues,
  useRateBatchTableDetail,
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
  const location = useLocation();
  const navigate = useNavigate();
  const rates = useRatesSummary(token);
  const isBatchLibraryRoute = location.pathname === "/rates/batches";
  const isNewBatchRoute = location.pathname === "/rates/batches/new";
  const routeBatchMatch = isBatchLibraryRoute || isNewBatchRoute
    ? null
    : location.pathname.match(/^\/rates\/batches\/([^/]+)(?:\/([^/]+)(?:\/([^/]+))?)?$/);
  const routeBatchId = routeBatchMatch ? decodeURIComponent(routeBatchMatch[1]) : null;
  const routeBatchSuffix = routeBatchMatch?.[2];
  const routeTableName = routeBatchSuffix === "tables" && routeBatchMatch?.[3]
    ? decodeURIComponent(routeBatchMatch[3])
    : null;
  const routeBatchMode = isBatchLibraryRoute
    ? "library"
    : isNewBatchRoute
      ? "new"
      : routeTableName
        ? "table-detail"
        : routeBatchSuffix && ["stage", "issues", "csv-preview", "export", "approve", "artifacts", "evidence", "load-plan"].includes(routeBatchSuffix)
          ? routeBatchSuffix
          : routeBatchId
            ? "overview"
            : "summary";
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
  const [isExportReviewOpen, setIsExportReviewOpen] = useState(false);
  const [batchSearch, setBatchSearch] = useState("");
  const [batchStatusFilter, setBatchStatusFilter] = useState("ALL");
  const [batchDomainFilter, setBatchDomainFilter] = useState("ALL");
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [runningActionKey, setRunningActionKey] = useState<string | null>(null);
  const [downloadingArtifactId, setDownloadingArtifactId] = useState<string | null>(null);
  const [loadPlanPackageId, setLoadPlanPackageId] = useState<string | null>(null);
  const [loadPlanPackageStatus, setLoadPlanPackageStatus] = useState<string | null>(null);
  const recentObjects = rates.data?.recent_objects ?? [];
  const effectiveBatchId = routeBatchId ?? (isBatchLibraryRoute || isNewBatchRoute ? null : selectedBatchId ?? recentObjects[0]?.id ?? null);
  const batchLibrary = useRateBatches(token);
  const batchDetail = useRateBatchDetail(token, effectiveBatchId);
  const batchArtifacts = useRateBatchArtifacts(token, effectiveBatchId);
  const batchEvidence = useRateBatchEvidence(token, effectiveBatchId);
  const batchIssues = useRateBatchIssues(token, routeBatchMode === "issues" ? effectiveBatchId : null);
  const batchTableDetail = useRateBatchTableDetail(
    token,
    effectiveBatchId,
    routeBatchMode === "table-detail" ? routeTableName : null
  );

  if (rates.isLoading) {
    return <StatePanel>Loading Rates Studio...</StatePanel>;
  }

  if (rates.isError || !rates.data) {
    return <StatePanel tone="error">Rates Studio summary is unavailable.</StatePanel>;
  }

  const data = rates.data;
  const libraryItems = batchLibrary.data?.items ?? [];
  const domainOptions = Array.from(new Set(libraryItems.map((batch) => batch.domain_name).filter(Boolean))).sort();
  const statusOptions = Array.from(new Set(libraryItems.map((batch) => batch.status).filter(Boolean))).sort();
  const normalizedBatchSearch = batchSearch.trim().toLowerCase();
  const filteredLibraryItems = libraryItems.filter((batch) => {
    const haystack = [
      batch.id,
      batch.name,
      batch.scenario_code,
      batch.status,
      batch.domain_name,
      batch.catalog_macro_object_code,
      batch.catalog_load_plan_path
    ]
      .join(" ")
      .toLowerCase();
    const matchesSearch = !normalizedBatchSearch || haystack.includes(normalizedBatchSearch);
    const matchesStatus = batchStatusFilter === "ALL" || batch.status === batchStatusFilter;
    const matchesDomain = batchDomainFilter === "ALL" || batch.domain_name === batchDomainFilter;
    return matchesSearch && matchesStatus && matchesDomain;
  });

  function clearBatchWorkspaceState() {
    setCsvPreviews([]);
    setApprovalAction(null);
    setApprovalNote("");
    setIsExportReviewOpen(false);
    setActionMessage(null);
    setActionError(null);
    setRunningActionKey(null);
    setDownloadingArtifactId(null);
    setLoadPlanPackageId(null);
    setLoadPlanPackageStatus(null);
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
    if (action.key === "export_csv") {
      setIsExportReviewOpen(true);
      return;
    }
    setRunningActionKey(action.key);
    try {
      await executeBackendAction(token, action.href);
      setActionMessage(`${action.label} completed.`);
      if (action.result_hint === "refresh_object" || action.result_hint === "refresh_list") {
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: ["modules", "rates", "summary"] }),
          queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches"] }),
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
      setIsExportReviewOpen(false);
      setIsCreateFormOpen(false);
      setActionMessage("Rate batch created.");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "summary"] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches"] })
      ]);
      if (isNewBatchRoute) {
        void navigate(`/rates/batches/${created.id}`);
      }
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
    if (!effectiveBatchId || (!approvalAction && routeBatchMode !== "approve")) return;
    const actionKey = approvalAction?.key ?? "approve";
    const actionLabel = approvalAction?.label ?? "Approve";
    setActionMessage(null);
    setActionError(null);
    setRunningActionKey(actionKey);
    try {
      await approveRateBatch(token, effectiveBatchId, { approval_note: approvalNote.trim() });
      setApprovalAction(null);
      setApprovalNote("");
      setActionMessage(`${actionLabel} completed.`);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "summary"] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches"] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches", effectiveBatchId] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches", effectiveBatchId, "evidence"] })
      ]);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setActionError(caught.message);
      } else {
        setActionError(`${actionLabel} failed.`);
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
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches"] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches", effectiveBatchId] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches", effectiveBatchId, "issues"] })
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
      setIsExportReviewOpen(false);
      setActionMessage("CSV preview ready.");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "summary"] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches"] }),
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
      setIsExportReviewOpen(false);
      setActionMessage(`CSV export created: ${result.file_name}.`);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "summary"] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches"] }),
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

  async function registerLoadPlanPackage() {
    if (!effectiveBatchId) return;
    setActionMessage(null);
    setActionError(null);
    setRunningActionKey("register_load_plan_package");
    try {
      const result = await executeBackendAction<Record<string, unknown>>(
        token,
        `/api/v1/modules/load-plan/packages/from-rates/${effectiveBatchId}`
      );
      const packageId = typeof result.id === "string" ? result.id : "registered";
      const packageStatus = typeof result.status === "string" ? result.status : "REGISTERED";
      setLoadPlanPackageId(packageId);
      setLoadPlanPackageStatus(packageStatus);
      setActionMessage(`Load Plan package registered: ${packageId}.`);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "summary"] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches"] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "rates", "batches", effectiveBatchId] }),
        queryClient.invalidateQueries({ queryKey: ["modules", "load-plan"] })
      ]);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setActionError(caught.message);
      } else {
        setActionError("Load Plan package registration failed.");
      }
    } finally {
      setRunningActionKey(null);
    }
  }

  const batchLibraryFilters = (
    <div className="rates-batch-library-filters">
      <label>
        Search
        <input
          aria-label="Rate batch search"
          placeholder="Batch, scenario, domain"
          value={batchSearch}
          onChange={(event) => setBatchSearch(event.target.value)}
        />
      </label>
      <label>
        Status
        <select
          aria-label="Rate batch status filter"
          value={batchStatusFilter}
          onChange={(event) => setBatchStatusFilter(event.target.value)}
        >
          <option value="ALL">ALL</option>
          {statusOptions.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </label>
      <label>
        Domain filter
        <select
          aria-label="Rate batch domain filter"
          value={batchDomainFilter}
          onChange={(event) => setBatchDomainFilter(event.target.value)}
        >
          <option value="ALL">ALL</option>
          {domainOptions.map((domain) => (
            <option key={domain} value={domain}>
              {domain}
            </option>
          ))}
        </select>
      </label>
    </div>
  );

  const batchLibraryList = (ariaLabel: string, onSelect: (batchId: string) => void) => (
    <ModuleObjectList
      ariaLabel={ariaLabel}
      emptyText={batchLibrary.isLoading ? "Loading rate batch library..." : "No rate batches match the current filters."}
      items={filteredLibraryItems.map((batch) => ({
        id: batch.id,
        meta: [batch.domain_name, batch.catalog_macro_object_code, `${batch.tables?.length ?? 0} table(s)`],
        status: batch.status,
        subtitle: batch.scenario_code,
        title: batch.name
      }))}
      maxVisibleItems={12}
      onSelect={onSelect}
      selectedId={effectiveBatchId}
    />
  );

  const newBatchForm = (
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
        {isNewBatchRoute ? (
          <Link className="button button-secondary" to="/rates/batches">
            Cancel
          </Link>
        ) : (
          <Button disabled={runningActionKey === "create_batch"} onClick={() => setIsCreateFormOpen(false)}>
            Cancel
          </Button>
        )}
      </div>
    </form>
  );

  if (routeBatchId) {
    const routeTitle =
      routeBatchMode === "stage"
        ? "Stage rate batch tables"
        : routeBatchMode === "issues"
          ? "Rate batch issues"
          : routeBatchMode === "csv-preview"
            ? "Rate CSV preview"
            : routeBatchMode === "export"
              ? "Rate export review"
              : routeBatchMode === "approve"
                ? "Rate approval review"
                : routeBatchMode === "table-detail"
                  ? "Rate batch table detail"
                  : routeBatchMode === "artifacts"
                    ? "Rate batch artifacts"
                    : routeBatchMode === "evidence"
                      ? "Rate batch evidence"
                      : routeBatchMode === "load-plan"
                        ? "Rate Load Plan handoff"
                        : "Rate batch overview";
    const routeDescription =
      routeBatchMode === "stage"
        ? "Route-level staging workspace for OTM rate table rows."
        : routeBatchMode === "issues"
          ? "Route-level inspection for validation findings and blockers."
          : routeBatchMode === "csv-preview"
            ? "Route-level OTM CSV preview before export packaging."
            : routeBatchMode === "export"
              ? "Route-level export review before creating client-safe artifacts."
              : routeBatchMode === "approve"
                ? "Route-level approval review with explicit approver note."
                : routeBatchMode === "table-detail"
                  ? "Route-level table inspection with staged rows and table-scoped issues."
                  : routeBatchMode === "artifacts"
                    ? "Route-level export artifacts with backend-owned sensitivity and download controls."
                    : routeBatchMode === "evidence"
                      ? "Route-level evidence inspection for export and approval records."
                      : routeBatchMode === "load-plan"
                        ? "Route-level handoff from approved Rates package into Load Plan intake."
                        : "Route-level batch inspection with backend-owned status, scope, and tables.";

    if (batchDetail.isLoading) {
      return <StatePanel>Loading rate batch route...</StatePanel>;
    }

    if (batchDetail.isError || !batchDetail.data) {
      return (
        <>
          <PageHeader description="The selected rate batch could not be loaded." label="Rates / Route recovery" title={routeTitle} />
          <StatePanel tone="error">
            Rate batch route is unavailable.
            <div className="state-actions">
              <Link className="button button-primary" to="/rates">
                Back to Rates
              </Link>
            </div>
          </StatePanel>
        </>
      );
    }

    const routeBatch = batchDetail.data;

    return (
      <>
        <PageHeader description={routeDescription} label="Rates / Batch" title={routeTitle} />

        <section aria-label="Rate batch route destinations" className="module-route-recovery-panel">
          <div className="module-route-recovery-actions">
            <Link className="button button-primary" to="/rates">
              Back to Rates
            </Link>
            <Link className="button button-secondary" to={`/rates/batches/${routeBatch.id}`}>
              Batch overview
            </Link>
            <Link className="button button-secondary" to={`/rates/batches/${routeBatch.id}/stage`}>
              Stage tables
            </Link>
            {routeBatchMode === "table-detail" ? (
              <Link className="button button-secondary" to={`/rates/batches/${routeBatch.id}`}>
                Back to Batch
              </Link>
            ) : null}
            <Link className="button button-secondary" to={`/rates/batches/${routeBatch.id}/issues`}>
              Review issues
            </Link>
            <Link className="button button-secondary" to={`/rates/batches/${routeBatch.id}/csv-preview`}>
              CSV preview
            </Link>
            <Link className="button button-secondary" to={`/rates/batches/${routeBatch.id}/export`}>
              Export review
            </Link>
            <Link className="button button-secondary" to={`/rates/batches/${routeBatch.id}/approve`}>
              Approval review
            </Link>
            <Link className="button button-secondary" to={`/rates/batches/${routeBatch.id}/artifacts`}>
              Artifacts
            </Link>
            <Link className="button button-secondary" to={`/rates/batches/${routeBatch.id}/evidence`}>
              Evidence
            </Link>
            <Link className="button button-secondary" to={`/rates/batches/${routeBatch.id}/load-plan`}>
              Load Plan handoff
            </Link>
          </div>
        </section>

        <section className="panel rate-route-panel" aria-label="Route batch summary">
          <div className="panel-header">
            <h2>{routeBatch.name}</h2>
            <span className={`status-chip status-${routeBatch.status.toLowerCase()}`}>{routeBatch.status}</span>
          </div>
          <div className="detail-grid">
            <span className="detail-field">
              <span>Scenario</span>
              <strong>{routeBatch.scenario_code}</strong>
            </span>
            <span className="detail-field">
              <span>Domain</span>
              <strong>{routeBatch.domain_name}</strong>
            </span>
            <span className="detail-field">
              <span>Macro object</span>
              <strong>{routeBatch.catalog_macro_object_code}</strong>
            </span>
            <span className="detail-field">
              <span>Tables</span>
              <strong>{routeBatch.tables.length}</strong>
            </span>
          </div>
        </section>

        {actionMessage ? <FeedbackMessage tone="success">{actionMessage}</FeedbackMessage> : null}
        {actionError ? <FeedbackMessage tone="error">{actionError}</FeedbackMessage> : null}

        {routeBatchMode === "stage" ? (
          <section className="panel rate-route-panel" aria-label="Route stage table row">
            <div className="panel-header">
              <h2>Stage table row</h2>
              <span className="status-chip">AUTHORING</span>
            </div>
            <form className="rate-batch-form rate-table-form" onSubmit={(event) => void addTableRow(event)}>
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
          </section>
        ) : null}

        {routeBatchMode === "table-detail" ? (
          <>
            <section className="panel rate-route-panel" aria-label="Route table detail">
              <div className="panel-header">
                <h2>{routeTableName}</h2>
                <span className={`status-chip status-${(batchTableDetail.data?.table.status ?? "pending").toLowerCase()}`}>
                  {batchTableDetail.data?.table.status ?? "PENDING"}
                </span>
              </div>
              {batchTableDetail.isLoading ? (
                <p className="empty-text">Loading table detail...</p>
              ) : batchTableDetail.isError || !batchTableDetail.data ? (
                <p className="empty-text">Table detail is unavailable.</p>
              ) : (
                <div className="detail-grid">
                  <span className="detail-field">
                    <span>Table</span>
                    <strong>{batchTableDetail.data.table.table_name}</strong>
                  </span>
                  <span className="detail-field">
                    <span>Role</span>
                    <strong>{batchTableDetail.data.table.requirement_level}</strong>
                  </span>
                  <span className="detail-field">
                    <span>Load order</span>
                    <strong>{batchTableDetail.data.table.sequence_index}</strong>
                  </span>
                  <span className="detail-field">
                    <span>Rows</span>
                    <strong>{batchTableDetail.data.total}</strong>
                  </span>
                  <span className="detail-field">
                    <span>Issues</span>
                    <strong>{batchTableDetail.data.issues.length}</strong>
                  </span>
                </div>
              )}
            </section>
            <section className="panel rate-route-panel" aria-label="Route table rows">
              <div className="panel-header">
                <h2>Table rows</h2>
                <span className="status-chip">{batchTableDetail.data?.rows.length ? "ACTIVE" : "EMPTY"}</span>
              </div>
              <div className="table-list">
                {(batchTableDetail.data?.rows ?? []).map((row) => (
                  <div className="table-list-item" key={row.row_index}>
                    <strong className="table-list-main">Row {row.row_index}</strong>
                    <div className="table-list-meta">
                      {Object.entries(row.payload).map(([key, value]) => (
                        <span key={key}>{key}: {String(value ?? "NULL")}</span>
                      ))}
                    </div>
                    <div className="table-list-status">
                      <span className={`status-chip status-${row.status.toLowerCase()}`}>{row.status}</span>
                    </div>
                  </div>
                ))}
              </div>
              {batchTableDetail.data && batchTableDetail.data.rows.length === 0 ? (
                <p className="empty-text">No rows have been staged for this table.</p>
              ) : null}
            </section>
            <OperationalPanel
              ariaLabel="Route table issues"
              emptyText="No table-scoped issues are registered."
              hasItems={(batchTableDetail.data?.issues.length ?? 0) > 0}
              isLoading={batchTableDetail.isLoading}
              loadingText="Loading table issues..."
              status={batchTableDetail.data?.issues.length ? "BLOCKED" : "READY"}
              title="Table issues"
            >
              <DetailList
                ariaLabel="Route table issue rows"
                items={(batchTableDetail.data?.issues ?? []).map((issue) => ({
                  id: issue.id,
                  meta: [issue.column_name ?? "No column", issue.message],
                  status: issue.severity,
                  title: issue.issue_code
                }))}
              />
            </OperationalPanel>
          </>
        ) : routeBatchMode === "issues" ? (
          <OperationalPanel
            ariaLabel="Route batch issues"
            emptyText="No issues are registered for this rate batch."
            hasItems={(batchIssues.data?.items.length ?? 0) > 0}
            isLoading={batchIssues.isLoading}
            loadingText="Loading issues..."
            status={batchIssues.data?.total ? "BLOCKED" : "READY"}
            title="Issue review"
          >
            <DetailList
              ariaLabel="Route batch issue rows"
              items={(batchIssues.data?.items ?? []).map((issue) => ({
                id: issue.id,
                meta: [
                  issue.table_name ?? "No table",
                  issue.column_name ?? "No column",
                  issue.message
                ],
                status: issue.severity,
                title: issue.issue_code
              }))}
            />
          </OperationalPanel>
        ) : routeBatchMode === "csv-preview" ? (
          <section className="panel rate-route-panel" aria-label="Route CSV preview">
            <div className="panel-header">
              <h2>CSV preview</h2>
              <span className="status-chip">{csvPreviews.length ? "READY" : "PENDING"}</span>
            </div>
            <div className="rate-preview-actions">
              <Button
                disabled={runningActionKey === "preview_csv" || routeBatch.tables.length === 0}
                onClick={() => void previewCsv()}
                variant="primary"
              >
                {runningActionKey === "preview_csv" ? "Previewing..." : "Preview CSV"}
              </Button>
              <Link className="button button-secondary" to={`/rates/batches/${routeBatch.id}/export`}>
                Export review
              </Link>
            </div>
            {csvPreviews.length ? (
              <div className="csv-preview-stack" aria-label="Route CSV preview output">
                {csvPreviews.map((preview) => (
                  <div className="csv-preview-item" key={preview.table_name}>
                    <strong>{preview.table_name}</strong>
                    <pre>{preview.content}</pre>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-text">Preview the staged tables before export review.</p>
            )}
          </section>
        ) : routeBatchMode === "export" ? (
          <section className="panel rate-route-panel" aria-label="Route export review">
            <div className="panel-header">
              <h2>Export review</h2>
              <span className="status-chip">{csvPreviews.length ? "READY" : "PENDING"}</span>
            </div>
            <div className="rate-review-gate">
              <span>{routeBatch.name}</span>
              <span>{routeBatch.scenario_code}</span>
              <span>{routeBatch.tables.length} table(s)</span>
              <span>{csvPreviews.length} preview file(s)</span>
              <span>client-safe artifact</span>
              <div className="rate-batch-form-actions">
                <Button disabled={runningActionKey === "preview_csv"} onClick={() => void previewCsv()} variant="secondary">
                  {runningActionKey === "preview_csv" ? "Previewing..." : "Preview CSV"}
                </Button>
                <Button
                  disabled={runningActionKey === "export_csv" || csvPreviews.length === 0}
                  onClick={() => void exportCsv()}
                  variant="primary"
                >
                  {runningActionKey === "export_csv" ? "Exporting..." : "Confirm export"}
                </Button>
              </div>
            </div>
          </section>
        ) : routeBatchMode === "approve" ? (
          <section className="panel rate-route-panel" aria-label="Route approval review">
            <div className="panel-header">
              <h2>Approval review</h2>
              <span className={`status-chip status-${routeBatch.status.toLowerCase()}`}>{routeBatch.status}</span>
            </div>
            <form className="rate-batch-form rate-approval-form" onSubmit={(event) => void approveBatch(event)}>
              <div className="rate-review-gate">
                <span>{routeBatch.name}</span>
                <span>{routeBatch.scenario_code}</span>
                <span>{routeBatch.status}</span>
                <span>{routeBatch.tables.length} table(s)</span>
                <span>{routeBatch.domain_name}</span>
              </div>
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
                <Button disabled={runningActionKey === "approve"} type="submit" variant="primary">
                  {runningActionKey === "approve" ? "Approving..." : "Confirm approval"}
                </Button>
              </div>
            </form>
          </section>
        ) : routeBatchMode === "artifacts" ? (
          <OperationalPanel
            ariaLabel="Route batch artifacts"
            emptyText="No export artifacts registered for this batch."
            hasItems={(batchArtifacts.data?.items.length ?? 0) > 0}
            isLoading={batchArtifacts.isLoading}
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
                meta: [artifact.content_type, `${artifact.size_bytes} bytes`, artifact.sensitivity_level],
                status: artifact.download_url ? "DOWNLOADABLE" : artifact.sensitivity_level,
                subtitle: artifact.artifact_type,
                title: artifact.file_name
              }))}
            />
          </OperationalPanel>
        ) : routeBatchMode === "evidence" ? (
          <OperationalPanel
            ariaLabel="Route batch evidence"
            emptyText="No evidence registered for this batch."
            hasItems={(batchEvidence.data?.items.length ?? 0) > 0}
            isLoading={batchEvidence.isLoading}
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
        ) : routeBatchMode === "load-plan" ? (
          <section className="panel rate-route-panel" aria-label="Route Load Plan handoff">
            <div className="panel-header">
              <h2>Load Plan handoff</h2>
              <span className={`status-chip status-${(loadPlanPackageStatus ?? routeBatch.status).toLowerCase()}`}>
                {loadPlanPackageStatus ?? routeBatch.status}
              </span>
            </div>
            <div className="detail-grid">
              <span className="detail-field">
                <span>Batch</span>
                <strong>{routeBatch.name}</strong>
              </span>
              <span className="detail-field">
                <span>Domain</span>
                <strong>{routeBatch.domain_name}</strong>
              </span>
              <span className="detail-field">
                <span>Macro object</span>
                <strong>{routeBatch.catalog_macro_object_code}</strong>
              </span>
              <span className="detail-field">
                <span>Catalog path</span>
                <strong>{routeBatch.catalog_load_plan_path}</strong>
              </span>
              <span className="detail-field">
                <span>Artifacts</span>
                <strong>{batchArtifacts.data?.total ?? 0} artifact(s)</strong>
              </span>
              <span className="detail-field">
                <span>Evidence</span>
                <strong>{batchEvidence.data?.total ?? 0} evidence record(s)</strong>
              </span>
              {loadPlanPackageId ? (
                <span className="detail-field">
                  <span>Package</span>
                  <strong>{loadPlanPackageId}</strong>
                </span>
              ) : null}
            </div>
            <div className="rate-batch-form-actions">
              <Button
                disabled={runningActionKey === "register_load_plan_package"}
                onClick={() => void registerLoadPlanPackage()}
                variant="primary"
              >
                {runningActionKey === "register_load_plan_package" ? "Registering..." : "Register Load Plan package"}
              </Button>
              <Link className="button button-secondary" to="/load-plan">
                Open Load Plan
              </Link>
            </div>
          </section>
        ) : (
          <section className="panel rate-route-panel" aria-label="Route batch tables">
            <div className="panel-header">
              <h2>Batch tables</h2>
              <span className="status-chip">{routeBatch.tables.length ? "ACTIVE" : "EMPTY"}</span>
            </div>
            {routeBatch.tables.length ? (
              <div className="table-list" aria-label="Route batch table rows">
                {routeBatch.tables.map((table) => (
                  <div className="table-list-item" key={table.id}>
                    <Link className="table-list-main" to={`/rates/batches/${routeBatch.id}/tables/${table.table_name}`}>
                      {table.table_name}
                    </Link>
                    <div className="table-list-meta">
                      <span>{table.row_count} row(s)</span>
                      <span>{table.requirement_level}</span>
                    </div>
                    <div className="table-list-status">
                      <span className={`status-chip status-${table.status.toLowerCase()}`}>{table.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-text">No tables have been staged for this batch.</p>
            )}
          </section>
        )}
      </>
    );
  }

  if (isBatchLibraryRoute) {
    return (
      <>
        <PageHeader
          description="Find rate batches by backend-owned batch, scenario, status, and domain metadata."
          label="Rates / Library"
          title="Rate batch library"
        />
        <section aria-label="Rate batch library route destinations" className="module-route-recovery-panel">
          <div className="module-route-recovery-actions">
            <Link className="button button-primary" to="/rates">
              Back to Rates
            </Link>
            <Link className="button button-secondary" to="/rates/batches/new">
              Create rate batch
            </Link>
          </div>
        </section>
        <section aria-label="Route rate batch library" className="rates-batch-library-panel">
          {batchLibraryFilters}
          {batchLibraryList("Route rate batch library results", (batchId) => void navigate(`/rates/batches/${batchId}`))}
        </section>
      </>
    );
  }

  if (isNewBatchRoute) {
    return (
      <>
        <PageHeader
          description="Create a rate batch with explicit scenario and domain context."
          label="Rates / New batch"
          title="New rate batch"
        />
        <section aria-label="New rate batch route destinations" className="module-route-recovery-panel">
          <div className="module-route-recovery-actions">
            <Link className="button button-primary" to="/rates/batches">
              Back to batch library
            </Link>
            <Link className="button button-secondary" to="/rates">
              Back to Rates
            </Link>
          </div>
        </section>
        {actionMessage ? <FeedbackMessage tone="success">{actionMessage}</FeedbackMessage> : null}
        {actionError ? <FeedbackMessage tone="error">{actionError}</FeedbackMessage> : null}
        <section className="panel rate-batch-form-panel" aria-label="New rate batch form">
          <div className="panel-header">
            <h2>Batch setup</h2>
          </div>
          {newBatchForm}
        </section>
      </>
    );
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
          {newBatchForm}
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

      <section aria-label="Rates lifecycle destinations" className="module-route-recovery-panel">
        <div className="module-route-recovery-actions">
          <a className="button button-secondary" href="/home">
            Back to Cockpit
          </a>
          <a className="button button-secondary" href="/rates">
            Back to Rates
          </a>
          <a className="button button-secondary" href="/rates/batches">
            Open batch library
          </a>
          <a className="button button-primary" href="/rates/batches/new">
            Create rate batch
          </a>
        </div>
        {effectiveBatchId ? (
          <div className="module-route-destination-grid">
            <a href={`/rates/batches/${effectiveBatchId}`}>Open selected batch</a>
            <a href={`/rates/batches/${effectiveBatchId}/stage`}>Stage tables</a>
            <a href={`/rates/batches/${effectiveBatchId}/issues`}>Review issues</a>
            <a href={`/rates/batches/${effectiveBatchId}/csv-preview`}>CSV preview</a>
            <a href={`/rates/batches/${effectiveBatchId}/export`}>Export review</a>
            <a href={`/rates/batches/${effectiveBatchId}/approve`}>Approval review</a>
            <a href={`/rates/batches/${effectiveBatchId}/artifacts`}>Artifacts</a>
            <a href={`/rates/batches/${effectiveBatchId}/evidence`}>Evidence</a>
            <a href={`/rates/batches/${effectiveBatchId}/load-plan`}>Load Plan handoff</a>
          </div>
        ) : (
          <p className="empty-text">Select a rate batch to reveal lifecycle destinations.</p>
        )}
      </section>

      <section aria-label="Rate batch library" className="rates-batch-library-panel">
        {batchLibraryFilters}
        {batchLibraryList("Rate batch library results", selectBatch)}
      </section>

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
                <div aria-label="Rate approval review" className="rate-review-gate">
                  <span>{batchDetail.data?.name}</span>
                  <span>{batchDetail.data?.scenario_code}</span>
                  <span>{batchDetail.data?.status}</span>
                  <span>{batchDetail.data?.tables.length ?? 0} table(s)</span>
                  <span>{batchDetail.data?.domain_name}</span>
                </div>
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
                  onClick={() => {
                    setActionMessage(null);
                    setActionError(null);
                    setIsExportReviewOpen(true);
                  }}
                  variant="secondary"
                >
                  Export CSV
                </Button>
              </div>
            ) : null}
            {isExportReviewOpen && batchDetail.data ? (
              <div aria-label="Rate export review" className="rate-review-gate">
                <span>{batchDetail.data.name}</span>
                <span>{batchDetail.data.scenario_code}</span>
                <span>{batchDetail.data.tables.length} table(s)</span>
                <span>{csvPreviews.length} preview file(s)</span>
                <span>client-safe artifact</span>
                <div className="rate-batch-form-actions">
                  <Button disabled={runningActionKey === "export_csv"} onClick={() => void exportCsv()} variant="primary">
                    {runningActionKey === "export_csv" ? "Exporting..." : "Confirm export"}
                  </Button>
                  <Button disabled={runningActionKey === "export_csv"} onClick={() => setIsExportReviewOpen(false)}>
                    Cancel
                  </Button>
                </div>
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
          maxVisibleItems={12}
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
