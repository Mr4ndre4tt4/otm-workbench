import { Activity, AlertCircle, Archive, CheckCircle2, ChevronRight, Moon, Sun } from "lucide-react";
import { type FormEvent, useState } from "react";

import { ApiError } from "../platform/api";
import { login, useCockpitSummary, useNavigation, useUserPreferences } from "../platform/hooks";
import { useAuth } from "../platform/useAuth";
import { Button, IconButton, StatusChip } from "../ui/components";
import type { AvailableAction, NavigationItem } from "../platform/types";

function navIcon(moduleId: string) {
  if (moduleId === "home") return <Activity aria-hidden="true" />;
  if (moduleId === "evidence") return <Archive aria-hidden="true" />;
  return <ChevronRight aria-hidden="true" />;
}

function SidebarNav({ items }: { items: NavigationItem[] }) {
  return (
    <nav className="sidebar-nav" aria-label="Workbench modules">
      {items.map((item) => (
        <a className={item.id === "home" ? "nav-item nav-item-active" : "nav-item"} href={item.path} key={item.id}>
          <span className="nav-icon">{navIcon(item.id)}</span>
          <span>{item.label}</span>
          <StatusChip status={item.status} />
        </a>
      ))}
    </nav>
  );
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
      <header className="page-header">
        <div>
          <p className="section-label">Workbench home</p>
          <h1>{data.title}</h1>
          <p>{data.description}</p>
        </div>
        <ActionBar actions={data.available_actions} />
      </header>

      <ContextSummary context={data.active_context} />

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

      <section className="metrics-grid" aria-label="Project activity">
        <div className="metric">
          <span>Visible modules</span>
          <strong>{data.module_summary.total}</strong>
        </div>
        <div className="metric">
          <span>Recent jobs</span>
          <strong>{data.counts.recent_jobs}</strong>
        </div>
        <div className="metric">
          <span>Artifacts</span>
          <strong>{data.counts.recent_artifacts}</strong>
        </div>
        <div className="metric">
          <span>Evidence</span>
          <strong>{data.counts.recent_evidence}</strong>
        </div>
      </section>

      <section className="activity-layout">
        <div className="panel">
          <div className="panel-header">
            <h2>Recent jobs</h2>
            <StatusChip status={data.counts.recent_jobs ? "ACTIVE" : "EMPTY"} />
          </div>
          {data.recent_jobs.length ? (
            data.recent_jobs.map((job) => (
              <div className="activity-row" key={job.id}>
                <strong>{job.job_type}</strong>
                <span>{job.source_module}</span>
                <StatusChip status={job.status} />
              </div>
            ))
          ) : (
            <p className="empty-text">No recent jobs for the active project.</p>
          )}
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>Recent evidence</h2>
            <StatusChip status={data.counts.recent_evidence ? "ACTIVE" : "EMPTY"} />
          </div>
          {data.recent_evidence.length ? (
            data.recent_evidence.map((evidence) => (
              <div className="activity-row" key={evidence.id}>
                <strong>{evidence.evidence_type}</strong>
                <span>{evidence.source_module}</span>
                <StatusChip status={evidence.status} />
              </div>
            ))
          ) : (
            <p className="empty-text">No client-safe evidence for the active project.</p>
          )}
        </div>
      </section>
    </>
  );
}

export function App() {
  const auth = useAuth();
  const navigation = useNavigation(auth.token);
  const preferences = useUserPreferences(auth.token);
  const themeMode = preferences.data?.theme_mode ?? "light";

  return (
    <div className="app-shell" data-theme={themeMode}>
      <aside className="sidebar">
        <div className="brand-lockup">
          <span className="brand-mark">OTM</span>
          <div>
            <strong>Workbench</strong>
            <span>Implementation cockpit</span>
          </div>
        </div>
        <SidebarNav items={navigation.data?.items ?? []} />
      </aside>

      <main className="main-area">
        <div className="topbar">
          <span>Backend-owned contracts</span>
          <div className="topbar-actions">
            {auth.isAuthenticated ? (
              <Button onClick={auth.signOut}>Sign out</Button>
            ) : null}
            <IconButton label="Light mode">
              <Sun aria-hidden="true" />
            </IconButton>
            <IconButton label="Dark mode">
              <Moon aria-hidden="true" />
            </IconButton>
          </div>
        </div>
        {auth.token ? <CockpitContent token={auth.token} /> : <LoginPanel />}
      </main>
    </div>
  );
}
