import { AlertCircle, CheckCircle2 } from "lucide-react";
import { type FormEvent, useState } from "react";
import { useLocation } from "react-router-dom";

import { ApiError } from "../platform/api";
import { MODULE_DESCRIPTIONS } from "./routes/moduleDescriptions";
import { isNavigationItemActive } from "./routes/routeUtils";
import { ContextSummary, ContextSwitcher, PageHeader, PreferenceControls, SidebarNav } from "./shell";
import {
  AssetsLibraryView,
  CatalogCoreView,
  EvidenceHubView,
  IntegrationMappingView,
  LoadPlanView,
  MasterDataView,
  OrderReleaseGeneratorView,
  RatesSummaryView
} from "../modules";
import { booleanStatus } from "../modules/moduleStatus";
import { login, useCockpitSummary, useNavigation, useUserPreferences } from "../platform/hooks";
import { useAuth } from "../platform/useAuth";
import { Button, MetricGrid, OperationalPanel, StatePanel, StatusChip } from "../ui/components";
import type { NavigationItem } from "../platform/types";

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
    return <StatePanel>Loading Project Cockpit...</StatePanel>;
  }

  if (cockpit.isError || !cockpit.data) {
    return <StatePanel tone="error">Project Cockpit is unavailable.</StatePanel>;
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
      <StatePanel tone="error">Use the backend-owned navigation menu to open an available module.</StatePanel>
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
  if (item?.id === "evidence") {
    return <EvidenceHubView token={token} />;
  }
  if (item?.id === "load_plan") {
    return <LoadPlanView token={token} />;
  }
  if (item?.id === "catalog") {
    return <CatalogCoreView token={token} />;
  }
  if (item?.id === "master_data") {
    return <MasterDataView token={token} />;
  }
  if (item?.id === "order_release_generator") {
    return <OrderReleaseGeneratorView token={token} />;
  }
  if (item?.id === "integration_mapping") {
    return <IntegrationMappingView token={token} />;
  }
  return item ? <ModulePlaceholder item={item} /> : <UnknownRoute />;
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
