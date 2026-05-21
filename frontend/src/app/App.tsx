import {
  Activity,
  AlertCircle,
  Archive,
  CheckCircle2,
  ChevronRight,
  Monitor,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Rows3,
  Sun
} from "lucide-react";
import { type FormEvent, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { NavLink, useLocation } from "react-router-dom";

import { ApiError } from "../platform/api";
import {
  downloadBackendArtifact,
  executeBackendAction,
  login,
  updateActiveContext,
  updateUserPreferences,
  useAssetDetail,
  useAssets,
  useAssetVersions,
  useCockpitSummary,
  useEnvironments,
  useNavigation,
  useRateBatchArtifacts,
  useProfiles,
  useProjects,
  useRateBatchDetail,
  useRateBatchEvidence,
  useRatesSummary,
  useUserPreferences
} from "../platform/hooks";
import { useAuth } from "../platform/useAuth";
import {
  Button,
  DetailList,
  IconButton,
  MetricGrid,
  ModuleObjectList,
  OperationalPanel,
  SelectedObjectPanel,
  StatusChip
} from "../ui/components";
import type { AssetItem, AvailableAction, NavigationItem, RatesSummaryItem } from "../platform/types";
import type { UserPreferences } from "../platform/types";

function navIcon(moduleId: string) {
  if (moduleId === "home") return <Activity aria-hidden="true" />;
  if (moduleId === "evidence") return <Archive aria-hidden="true" />;
  return <ChevronRight aria-hidden="true" />;
}

function SidebarNav({
  currentPath,
  items,
  sidebarMode
}: {
  currentPath: string;
  items: NavigationItem[];
  sidebarMode: UserPreferences["sidebar_mode"];
}) {
  return (
    <nav className="sidebar-nav" aria-label="Workbench modules">
      {items.map((item) => (
        <NavLink
          className={isNavigationItemActive(item, currentPath) ? "nav-item nav-item-active" : "nav-item"}
          key={item.id}
          to={item.path}
        >
          <span className="nav-icon">{navIcon(item.id)}</span>
          <span className="nav-label">{item.label}</span>
          {sidebarMode === "expanded" ? <StatusChip status={item.status} /> : null}
        </NavLink>
      ))}
    </nav>
  );
}

function isNavigationItemActive(item: NavigationItem, currentPath: string) {
  if (item.id === "home" && (currentPath === "/" || currentPath === "/home")) return true;
  return currentPath === item.path || currentPath.startsWith(`${item.path}/`);
}

function ContextSummary({ context }: { context: Record<string, unknown> }) {
  const projectId = context.project_id as string | null;
  const profileId = context.profile_id as string | null;
  const environmentId = context.environment_id as string | null;
  const domainName = context.domain_name as string | null;
  return (
    <div className="context-summary" aria-label="Active context">
      <span>{projectId ? "Project selected" : "No project selected"}</span>
      <span>{profileId ? "Profile selected" : "Profile pending"}</span>
      <span>{environmentId ? "Environment selected" : "Environment pending"}</span>
      <span>{domainName ?? "PUBLIC"}</span>
    </div>
  );
}

function ActionBar({ actions }: { actions: AvailableAction[] }) {
  return (
    <div className="action-bar">
      {actions.map((action) => (
        <Button disabled={action.disabled} key={action.key} variant={action.variant === "primary" ? "primary" : "secondary"}>
          {action.label}
        </Button>
      ))}
    </div>
  );
}

function PageHeader({
  actions,
  description,
  label,
  title
}: {
  actions?: AvailableAction[];
  description: string;
  label: string;
  title: string;
}) {
  return (
    <header className="page-header">
      <div>
        <p className="section-label">{label}</p>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {actions ? <ActionBar actions={actions} /> : null}
    </header>
  );
}

function LoginPanel() {
  const auth = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const response = await login(email, password);
      auth.signIn(response.access_token);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Unable to sign in.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="login-panel" aria-label="Workbench sign in">
      <div>
        <p className="section-label">Backend session</p>
        <h1>Sign in to OTM Workbench</h1>
        <p>Use a backend session so navigation, permissions, preferences, and cockpit data stay API-owned.</p>
      </div>
      <form className="login-form" onSubmit={handleSubmit}>
        <label>
          <span>Email</span>
          <input
            autoComplete="email"
            name="email"
            onChange={(event) => setEmail(event.target.value)}
            required
            type="email"
            value={email}
          />
        </label>
        <label>
          <span>Password</span>
          <input
            autoComplete="current-password"
            name="password"
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
        </label>
        {error ? <p className="form-error">{error}</p> : null}
        <Button disabled={isSubmitting} type="submit" variant="primary">
          {isSubmitting ? "Signing in..." : "Sign in"}
        </Button>
      </form>
    </section>
  );
}

function CockpitContent({ token }: { token: string }) {
  const cockpit = useCockpitSummary(token);

  if (cockpit.isLoading) {
    return <section className="state-panel">Loading Project Cockpit...</section>;
  }

  if (cockpit.isError || !cockpit.data) {
    return (
      <section className="state-panel state-panel-error">
        <AlertCircle aria-hidden="true" />
        <span>Project Cockpit is unavailable.</span>
      </section>
    );
  }

  const data = cockpit.data;

  return (
    <>
      <PageHeader
        actions={data.available_actions}
        description={data.description}
        label="Workbench home"
        title={data.title}
      />

      <ContextSummary context={data.active_context} />
      <ContextSwitcher token={token} />

      <section className={data.status === "ready" ? "readiness readiness-ready" : "readiness"}>
        {data.status === "ready" ? <CheckCircle2 aria-hidden="true" /> : <AlertCircle aria-hidden="true" />}
        <div>
          <strong>{data.status === "ready" ? "Project context ready" : "Select an active project context"}</strong>
          <span>
            {data.setup_status
              ? `${data.setup_status.profile_count} profile(s), ${data.setup_status.environment_count} environment(s)`
              : "The shell is waiting for project, profile, and environment context."}
          </span>
        </div>
      </section>

      <MetricGrid
        ariaLabel="Project activity"
        items={[
          {
            key: "visible_modules",
            label: "Visible modules",
            status: booleanStatus(data.module_summary.total),
            value: data.module_summary.total
          },
          {
            key: "recent_jobs",
            label: "Recent jobs",
            status: booleanStatus(data.counts.recent_jobs),
            value: data.counts.recent_jobs
          },
          {
            key: "recent_artifacts",
            label: "Artifacts",
            status: booleanStatus(data.counts.recent_artifacts),
            value: data.counts.recent_artifacts
          },
          {
            key: "recent_evidence",
            label: "Evidence",
            status: booleanStatus(data.counts.recent_evidence),
            value: data.counts.recent_evidence
          }
        ]}
      />

      <section className="activity-layout">
        <OperationalPanel
          emptyText="No recent jobs for the active project."
          hasItems={data.recent_jobs.length > 0}
          status={data.counts.recent_jobs ? "ACTIVE" : "EMPTY"}
          title="Recent jobs"
        >
          {data.recent_jobs.map((job) => (
            <div className="activity-row" key={job.id}>
              <strong>{job.job_type}</strong>
              <span>{job.source_module}</span>
              <StatusChip status={job.status} />
            </div>
          ))}
        </OperationalPanel>

        <OperationalPanel
          emptyText="No client-safe evidence for the active project."
          hasItems={data.recent_evidence.length > 0}
          status={data.counts.recent_evidence ? "ACTIVE" : "EMPTY"}
          title="Recent evidence"
        >
          {data.recent_evidence.map((evidence) => (
            <div className="activity-row" key={evidence.id}>
              <strong>{evidence.evidence_type}</strong>
              <span>{evidence.source_module}</span>
              <StatusChip status={evidence.status} />
            </div>
          ))}
        </OperationalPanel>
      </section>
    </>
  );
}

function ContextSwitcher({ token }: { token: string }) {
  const queryClient = useQueryClient();
  const projects = useProjects(token);
  const [projectId, setProjectId] = useState<string>("");
  const [profileId, setProfileId] = useState<string>("");
  const [environmentId, setEnvironmentId] = useState<string>("");
  const [domainName, setDomainName] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setSubmitting] = useState(false);
  const profiles = useProfiles(token, projectId || null);
  const environments = useEnvironments(token, projectId || null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setError(null);
    setSubmitting(true);
    try {
      await updateActiveContext(token, {
        project_id: projectId || null,
        profile_id: profileId || null,
        environment_id: environmentId || null,
        domain_name: domainName || null,
        can_view_all_domains: false
      });
      await queryClient.invalidateQueries({ queryKey: ["platform"] });
      setMessage("Context updated.");
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Unable to update context.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="context-switcher" onSubmit={handleSubmit}>
      <label>
        <span>Project</span>
        <select
          disabled={projects.isLoading}
          onChange={(event) => {
            setProjectId(event.target.value);
            setProfileId("");
            setEnvironmentId("");
            setMessage(null);
          }}
          value={projectId}
        >
          <option value="">Select project</option>
          {(projects.data?.items ?? []).map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span>Profile</span>
        <select disabled={!projectId || profiles.isLoading} onChange={(event) => setProfileId(event.target.value)} value={profileId}>
          <option value="">Select profile</option>
          {(profiles.data?.items ?? []).map((profile) => (
            <option key={profile.id} value={profile.id}>
              {profile.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span>Environment</span>
        <select
          disabled={!projectId || environments.isLoading}
          onChange={(event) => setEnvironmentId(event.target.value)}
          value={environmentId}
        >
          <option value="">Select environment</option>
          {(environments.data?.items ?? []).map((environment) => (
            <option key={environment.id} value={environment.id}>
              {environment.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span>Domain</span>
        <input onChange={(event) => setDomainName(event.target.value)} placeholder="PUBLIC" value={domainName} />
      </label>
      <Button disabled={isSubmitting || !projectId} type="submit" variant="primary">
        {isSubmitting ? "Applying..." : "Apply context"}
      </Button>
      {message ? <p className="form-success">{message}</p> : null}
      {error ? <p className="form-error">{error}</p> : null}
    </form>
  );
}

function severityStatus(severity: string) {
  if (severity === "success") return "READY";
  if (severity === "warning") return "BLOCKED";
  if (severity === "danger") return "ERROR";
  return "INFO";
}

function booleanStatus(value: number) {
  return value > 0 ? "ACTIVE" : "EMPTY";
}

function rateBatchMeta(batch: RatesSummaryItem) {
  const issueCount = Object.values(batch.summary.issue_summary).reduce((total, value) => total + value, 0);
  return [`${batch.summary.table_count} table(s)`, `${batch.summary.row_count} row(s)`, `${issueCount} issue(s)`];
}

function assetMeta(asset: AssetItem) {
  const scope = asset.module_id ? `${asset.scope_type} / ${asset.module_id}` : asset.scope_type;
  return [asset.asset_type, asset.category, scope];
}

function RatesSummaryView({ token }: { token: string }) {
  const queryClient = useQueryClient();
  const rates = useRatesSummary(token);
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
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
    return <section className="state-panel">Loading Rates Studio...</section>;
  }

  if (rates.isError || !rates.data) {
    return (
      <section className="state-panel state-panel-error">
        <AlertCircle aria-hidden="true" />
        <span>Rates Studio summary is unavailable.</span>
      </section>
    );
  }

  const data = rates.data;

  async function runBatchAction(action: AvailableAction) {
    if (action.method !== "POST" || action.disabled) return;
    setActionMessage(null);
    setActionError(null);
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

  return (
    <>
      <PageHeader
        actions={data.available_actions}
        description={data.description}
        label="Module workspace"
        title={data.title}
      />

      <MetricGrid
        ariaLabel="Rates summary metrics"
        items={data.counts.map((count) => ({
          key: count.key,
          label: count.label,
          status: severityStatus(count.severity),
          value: count.value
        }))}
      />

      <section className="module-template" aria-label="Rates Studio workspace">
        <div className="module-template-main">
          <div className="panel-header">
            <h2>Recent rate batches</h2>
            <StatusChip status={data.recent_objects.length ? "ACTIVE" : "EMPTY"} />
          </div>
          <ModuleObjectList
            emptyText="No rate batches available for the current context."
            items={data.recent_objects.map((batch) => ({
              id: batch.id,
              meta: rateBatchMeta(batch),
              status: batch.status,
              subtitle: batch.code,
              title: batch.display_name
            }))}
            onSelect={setSelectedBatchId}
            selectedId={effectiveBatchId}
          />
        </div>

        <SelectedObjectPanel
          actions={
            batchDetail.data
              ? batchDetail.data.available_actions.map((action) => (
                  <Button
                    disabled={action.disabled}
                    key={action.key}
                    onClick={() => void runBatchAction(action)}
                    variant={action.variant === "primary" ? "primary" : "secondary"}
                  >
                    {runningActionKey === action.key ? "Running..." : action.label}
                  </Button>
                ))
              : null
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
          {actionMessage ? <p className="form-success">{actionMessage}</p> : null}
          {actionError ? <p className="form-error">{actionError}</p> : null}
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
        </SelectedObjectPanel>
      </section>

      <section className="panel blockers-panel">
        <div className="panel-header">
          <h2>Open blockers</h2>
          <StatusChip status={data.open_blockers.length ? "BLOCKED" : "READY"} />
        </div>
        {data.open_blockers.length ? (
          <div className="blocker-list">
            {data.open_blockers.map((blocker) => (
              <div className="blocker-item" key={`${blocker.object_type}-${blocker.object_id}`}>
                <strong>{blocker.codes.join(", ")}</strong>
                <span>{blocker.message}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="empty-text">No open blockers in the current rates summary.</p>
        )}
      </section>

      <section className="activity-layout">
        <OperationalPanel
          emptyText="No export artifacts registered for this batch."
          hasItems={(batchArtifacts.data?.items.length ?? 0) > 0}
          isLoading={batchArtifacts.isLoading && Boolean(effectiveBatchId)}
          loadingText="Loading artifacts..."
          status={batchArtifacts.data?.total ? "ACTIVE" : "EMPTY"}
          title="Batch artifacts"
        >
          <div className="artifact-list">
            {(batchArtifacts.data?.items ?? []).map((artifact) => (
              <div className="artifact-list-item" key={artifact.id}>
                <div>
                  <strong>{artifact.file_name}</strong>
                  <span>{artifact.artifact_type}</span>
                </div>
                <span>{artifact.content_type}</span>
                <span>{artifact.size_bytes} bytes</span>
                {artifact.download_url ? (
                  <Button
                    disabled={downloadingArtifactId === artifact.id}
                    onClick={() => void downloadArtifact(artifact.id, artifact.download_url!, artifact.file_name)}
                  >
                    {downloadingArtifactId === artifact.id ? "Downloading..." : "Download"}
                  </Button>
                ) : (
                  <StatusChip status={artifact.sensitivity_level} />
                )}
              </div>
            ))}
          </div>
        </OperationalPanel>

        <OperationalPanel
          emptyText="No evidence registered for this batch."
          hasItems={(batchEvidence.data?.items.length ?? 0) > 0}
          isLoading={batchEvidence.isLoading && Boolean(effectiveBatchId)}
          loadingText="Loading evidence..."
          status={batchEvidence.data?.total ? "ACTIVE" : "EMPTY"}
          title="Batch evidence"
        >
          <div className="artifact-list">
            {(batchEvidence.data?.items ?? []).map((evidence) => (
              <div className="artifact-list-item" key={evidence.id}>
                <div>
                  <strong>{evidence.evidence_type}</strong>
                  <span>{evidence.sensitivity_level}</span>
                </div>
                <span>{evidence.artifact_id ? "Artifact linked" : "No artifact"}</span>
                <span>{evidence.client_safe ? "Client safe" : "Internal"}</span>
                <StatusChip status={evidence.status} />
              </div>
            ))}
          </div>
        </OperationalPanel>
      </section>
    </>
  );
}

function AssetsLibraryView({ token }: { token: string }) {
  const assets = useAssets(token);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const assetItems = assets.data?.items ?? [];
  const effectiveAssetId = selectedAssetId ?? assetItems[0]?.id ?? null;
  const assetDetail = useAssetDetail(token, effectiveAssetId);
  const assetVersions = useAssetVersions(token, effectiveAssetId);
  const selectedAsset = assetDetail.data;
  const versionedCount = assetItems.filter((asset) => asset.current_version_id).length;
  const internalCount = assetItems.filter((asset) => asset.sensitivity === "INTERNAL").length;

  if (assets.isLoading) {
    return <section className="state-panel">Loading Assets Library...</section>;
  }

  if (assets.isError || !assets.data) {
    return (
      <section className="state-panel state-panel-error">
        <AlertCircle aria-hidden="true" />
        <span>Assets Library is unavailable.</span>
      </section>
    );
  }

  return (
    <>
      <PageHeader
        description="Shared library for templates, payloads, generated files, specs, and reusable implementation assets."
        label="Module workspace"
        title="Assets Library"
      />

      <MetricGrid
        ariaLabel="Assets Library metrics"
        items={[
          { key: "total", label: "Assets", status: booleanStatus(assets.data.total), value: assets.data.total },
          { key: "versioned", label: "Versioned", status: booleanStatus(versionedCount), value: versionedCount },
          { key: "internal", label: "Internal", status: booleanStatus(internalCount), value: internalCount },
          { key: "visible", label: "Visible rows", status: booleanStatus(assetItems.length), value: assetItems.length }
        ]}
      />

      <section className="module-template" aria-label="Assets Library workspace">
        <div className="module-template-main">
          <div className="panel-header">
            <h2>Assets</h2>
            <StatusChip status={assetItems.length ? "ACTIVE" : "EMPTY"} />
          </div>
          <ModuleObjectList
            emptyText="No assets available for the current context."
            items={assetItems.map((asset) => ({
              id: asset.id,
              meta: assetMeta(asset),
              status: asset.status,
              subtitle: asset.macro_object_code ?? asset.module_id ?? asset.scope_type,
              title: asset.name
            }))}
            onSelect={setSelectedAssetId}
            selectedId={effectiveAssetId}
          />
        </div>

        <SelectedObjectPanel
          emptyText="Select an asset to inspect backend-owned metadata."
          fields={
            selectedAsset
              ? [
                  { label: "Category", value: selectedAsset.category },
                  { label: "Sensitivity", value: selectedAsset.sensitivity },
                  { label: "Macro object", value: selectedAsset.macro_object_code ?? "None" },
                  { label: "OTM table", value: selectedAsset.otm_table_name ?? "None" }
                ]
              : []
          }
          isLoading={assetDetail.isLoading && Boolean(effectiveAssetId)}
          loadingText="Loading selected asset..."
          status={selectedAsset?.status ?? "PENDING"}
          subtitle={selectedAsset?.asset_type}
          title={selectedAsset?.name}
        >
          {selectedAsset?.description ? <p className="empty-text">{selectedAsset.description}</p> : null}
          <DetailList
            ariaLabel="Selected asset versions"
            emptyText="No versions uploaded for this asset."
            items={(assetVersions.data?.items ?? []).map((version) => ({
              id: version.id,
              meta: [`v${version.version_number}`, version.content_type, `${version.size_bytes} bytes`],
              status: version.status,
              title: version.file_name
            }))}
          />
        </SelectedObjectPanel>
      </section>
    </>
  );
}

const MODULE_DESCRIPTIONS: Record<string, string> = {
  admin: "Workspace, project, profile, environment, users, roles, capabilities, and feature flag administration.",
  assets: "Shared library for templates, payloads, generated files, specs, and reusable implementation assets.",
  catalog: "Canonical OTM catalog foundation for macro objects, load plans, data dictionary alignment, and module contracts.",
  dev_tools: "Internal diagnostics and development utilities exposed only behind admin and feature flag controls.",
  evidence: "Client-safe evidence, manifests, artifacts, and implementation audit trail across modules.",
  integration_mapping: "Table-first integration definitions, systems, endpoints, schema trees, mappings, joins, loops, and lookups.",
  load_plan: "Load package intake, CSVUtil planning, review queues, cutover readiness, and handoff controls.",
  master_data: "Template factory and master data batch preparation for backend-first OTM implementation flows.",
  order_release_generator: "Order release template, batch, XML preview, artifact, and job orchestration workspace.",
  rates: "Rate batch preparation, validation, approval, CSV preview, export artifacts, and load package handoff."
};

function ModulePlaceholder({ item }: { item: NavigationItem }) {
  const description = MODULE_DESCRIPTIONS[item.id] ?? "Module workspace prepared for backend-owned contracts.";
  return (
    <>
      <PageHeader description={description} label="Module workspace" title={item.label} />
      <section className="module-template" aria-label={`${item.label} module template`}>
        <div className="module-template-main">
          <div className="panel-header">
            <h2>Overview</h2>
            <StatusChip status={item.status} />
          </div>
          <p className="empty-text">
            This route is wired into the shared shell. The next slice can attach the module list, detail, filters,
            actions, and evidence panels without creating a custom page framework.
          </p>
        </div>
        <aside className="module-template-side">
          <h2>Expected panels</h2>
          <ul>
            <li>Primary list or work queue</li>
            <li>Selected object summary</li>
            <li>Available actions from backend</li>
            <li>Jobs, artifacts, and evidence links</li>
          </ul>
        </aside>
      </section>
    </>
  );
}

function UnknownRoute() {
  return (
    <>
      <PageHeader
        description="This route is not registered by the backend navigation contract for the current user."
        label="Route not available"
        title="Module unavailable"
      />
      <section className="state-panel state-panel-error">
        <AlertCircle aria-hidden="true" />
        <span>Use the backend-owned navigation menu to open an available module.</span>
      </section>
    </>
  );
}

function WorkbenchRoute({ items, token }: { items: NavigationItem[]; token: string }) {
  const location = useLocation();
  const currentPath = location.pathname;
  if (currentPath === "/" || currentPath === "/home") {
    return <CockpitContent token={token} />;
  }
  const item = items.find((candidate) => isNavigationItemActive(candidate, currentPath));
  if (item?.id === "rates") {
    return <RatesSummaryView token={token} />;
  }
  if (item?.id === "assets") {
    return <AssetsLibraryView token={token} />;
  }
  return item ? <ModulePlaceholder item={item} /> : <UnknownRoute />;
}

function PreferenceControls({
  preferences,
  token
}: {
  preferences: UserPreferences | undefined;
  token: string | null;
}) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const currentMode = preferences?.theme_mode ?? "light";
  const currentDensity = preferences?.density ?? "comfortable";
  const currentSidebarMode = preferences?.sidebar_mode ?? "expanded";

  async function applyPreferences(nextValues: Partial<UserPreferences>) {
    if (!token) return;
    setError(null);
    const nextPreferences: UserPreferences = {
      theme_mode: preferences?.theme_mode ?? "light",
      follow_system_theme: preferences?.follow_system_theme ?? false,
      density: preferences?.density ?? "comfortable",
      sidebar_mode: preferences?.sidebar_mode ?? "expanded",
      ...nextValues
    };
    if (nextPreferences.theme_mode === "system") {
      nextPreferences.follow_system_theme = true;
    }
    if (nextPreferences.theme_mode !== "system") {
      nextPreferences.follow_system_theme = false;
    }
    try {
      await updateUserPreferences(token, nextPreferences);
      queryClient.setQueryData(["platform", "user-preferences"], nextPreferences);
      await queryClient.invalidateQueries({ queryKey: ["platform", "user-preferences"] });
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Unable to update preference.");
      }
    }
  }

  return (
    <div className="preference-controls" aria-label="Workbench preferences">
      <IconButton
        aria-pressed={currentMode === "light"}
        className={currentMode === "light" ? "icon-button-active" : ""}
        disabled={!token}
        label="Use light mode"
        onClick={() => void applyPreferences({ theme_mode: "light" })}
      >
        <Sun aria-hidden="true" />
      </IconButton>
      <IconButton
        aria-pressed={currentMode === "dark"}
        className={currentMode === "dark" ? "icon-button-active" : ""}
        disabled={!token}
        label="Use dark mode"
        onClick={() => void applyPreferences({ theme_mode: "dark" })}
      >
        <Moon aria-hidden="true" />
      </IconButton>
      <IconButton
        aria-pressed={currentMode === "system"}
        className={currentMode === "system" ? "icon-button-active" : ""}
        disabled={!token}
        label="Follow system theme"
        onClick={() => void applyPreferences({ theme_mode: "system" })}
      >
        <Monitor aria-hidden="true" />
      </IconButton>
      <IconButton
        aria-pressed={currentDensity === "compact"}
        className={currentDensity === "compact" ? "icon-button-active" : ""}
        disabled={!token}
        label={currentDensity === "compact" ? "Use comfortable density" : "Use compact density"}
        onClick={() =>
          void applyPreferences({ density: currentDensity === "compact" ? "comfortable" : "compact" })
        }
      >
        <Rows3 aria-hidden="true" />
      </IconButton>
      <IconButton
        aria-pressed={currentSidebarMode === "collapsed"}
        className={currentSidebarMode === "collapsed" ? "icon-button-active" : ""}
        disabled={!token}
        label={currentSidebarMode === "collapsed" ? "Expand sidebar" : "Collapse sidebar"}
        onClick={() =>
          void applyPreferences({ sidebar_mode: currentSidebarMode === "collapsed" ? "expanded" : "collapsed" })
        }
      >
        {currentSidebarMode === "collapsed" ? <PanelLeftOpen aria-hidden="true" /> : <PanelLeftClose aria-hidden="true" />}
      </IconButton>
      {error ? <span className="preference-error">{error}</span> : null}
    </div>
  );
}

export function App() {
  const auth = useAuth();
  const navigation = useNavigation(auth.token);
  const preferences = useUserPreferences(auth.token);
  const location = useLocation();
  const themeMode = preferences.data?.theme_mode ?? "light";
  const density = preferences.data?.density ?? "comfortable";
  const sidebarMode = preferences.data?.sidebar_mode ?? "expanded";

  return (
    <div className="app-shell" data-density={density} data-sidebar={sidebarMode} data-theme={themeMode}>
      <aside className="sidebar">
        <div className="brand-lockup">
          <span className="brand-mark">OTM</span>
          <div className="brand-text">
            <strong>Workbench</strong>
            <span>Implementation cockpit</span>
          </div>
        </div>
        <SidebarNav currentPath={location.pathname} items={navigation.data?.items ?? []} sidebarMode={sidebarMode} />
      </aside>

      <main className="main-area">
        <div className="topbar">
          <span>Backend-owned contracts</span>
          <div className="topbar-actions">
            {auth.isAuthenticated ? (
              <Button onClick={auth.signOut}>Sign out</Button>
            ) : null}
            <PreferenceControls preferences={preferences.data} token={auth.token} />
          </div>
        </div>
        {auth.token ? <WorkbenchRoute items={navigation.data?.items ?? []} token={auth.token} /> : <LoginPanel />}
      </main>
    </div>
  );
}
