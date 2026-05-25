import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "../platform/auth";
import type { PlatformJob } from "../platform/types";

function renderFunctionalApp(initialPath = "/admin") {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false }
    }
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={[initialPath]}>
          <App />
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

function platformPreferences() {
  return {
    theme_mode: "light",
    follow_system_theme: false,
    density: "comfortable",
    sidebar_mode: "expanded"
  };
}

function cockpitSummary() {
  return {
    module_id: "home",
    title: "Project Cockpit",
    status: "ready",
    description: "Project-level operational overview.",
    active_context: {},
    setup_status: {
      status: "READY",
      profile_count: 1,
      environment_count: 1,
      active_context_selected: true,
      missing_requirements: []
    },
    counts: { recent_jobs: 0, recent_artifacts: 0, recent_evidence: 0 },
    module_summary: { total: 2, counts_by_status: { ACTIVE: 2 }, items: [] },
    recent_jobs: [],
    recent_artifacts: [],
    recent_evidence: [],
    available_actions: []
  };
}

describe("Functional Admin Console journey", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("surfaces setup, capabilities, jobs, audit, and demo job actions from platform APIs", async () => {
    const createRequests: unknown[] = [];
    const runRequests: string[] = [];
    const cancelRequests: string[] = [];
    const featureFlagRequests: unknown[] = [];
    const workspaceRequests: unknown[] = [];
    const projectRequests: unknown[] = [];
    const profileRequests: unknown[] = [];
    const environmentRequests: unknown[] = [];
    let featureFlags = [{ id: "flag_1", name: "dev_tools", enabled: false, scope: "global" }];
    let workspaces = [{ id: "workspace_1", name: "Default workspace" }];
    let projects = [{ id: "project_1", name: "Synthetic Project" }];
    const profilesByProject: Record<string, Array<{ id: string; name: string }>> = {
      project_1: [{ id: "profile_1", name: "Default profile" }]
    };
    const environmentsByProject: Record<string, Array<{ id: string; name: string }>> = {
      project_1: [{ id: "environment_1", name: "DEV environment" }]
    };
    let jobs: PlatformJob[] = [
      {
        id: "job_pending",
        job_type: "DEMO_ECHO",
        source_module: "platform",
        project_id: "project_1",
        profile_id: "profile_1",
        environment_id: "environment_1",
        domain_name: "OTM1",
        status: "PENDING",
        progress: 0,
        message: "Job created.",
        input: { value: "pending" },
        result: {},
        error: null,
        created_by: "admin@example.test",
        created_at: "2026-05-21T10:00:00",
        started_at: null,
        finished_at: null,
        cancelled_at: null
      }
    ];
    const jobEvents: Record<string, Array<Record<string, unknown>>> = {
      job_pending: [
        {
          id: "event_pending_created",
          job_id: "job_pending",
          event_type: "JOB_CREATED",
          status_before: null,
          status_after: "PENDING",
          message: "Job created.",
          payload: { job_id: "job_pending", job_type: "DEMO_ECHO", source_module: "platform" },
          created_by: "admin@example.test",
          created_at: "2026-05-21T10:00:00"
        }
      ]
    };
    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(jsonResponse({ access_token: "session_token", token_type: "bearer" }));
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            items: [
              { id: "home", label: "Project Cockpit", path: "/home", status: "ACTIVE" },
              { id: "admin", label: "Admin Console", path: "/admin", status: "PLANNED" }
            ],
            total: 2,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(cockpitSummary()));
      }
      if (url.endsWith("/api/v1/platform/session/me")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse({ id: "user_admin", email: "admin@example.test", is_admin: true }));
      }
      if (url.endsWith("/api/v1/platform/workspaces")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          workspaceRequests.push(body);
          expect(body).toEqual({ name: "Synthetic Workspace B" });
          const workspace = { id: "workspace_2", name: body.name };
          workspaces = [...workspaces, workspace];
          return Promise.resolve(jsonResponse(workspace));
        }
        return Promise.resolve(jsonResponse(workspaces));
      }
      if (url.endsWith("/api/v1/platform/projects")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          projectRequests.push(body);
          expect(body).toEqual({ workspace_id: "workspace_2", name: "Synthetic Project B" });
          const project = { id: "project_2", name: body.name };
          projects = [...projects, project];
          profilesByProject.project_2 = [];
          environmentsByProject.project_2 = [];
          return Promise.resolve(jsonResponse(project));
        }
        return Promise.resolve(
          jsonResponse({
            items: projects,
            total: projects.length,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.includes("/api/v1/platform/profiles")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          profileRequests.push(body);
          expect(body).toEqual({ project_id: "project_2", name: "Synthetic Profile B" });
          const profile = { id: "profile_2", name: body.name };
          profilesByProject.project_2 = [profile];
          return Promise.resolve(jsonResponse(profile));
        }
        const projectMatch = /project_id=([^&]+)/.exec(url);
        const projectKey = projectMatch?.[1] ?? "project_1";
        const items = profilesByProject[projectKey] ?? [];
        return Promise.resolve(jsonResponse({ items, total: items.length, page: 1, page_size: 50 }));
      }
      if (url.includes("/api/v1/platform/environments")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          environmentRequests.push(body);
          expect(body).toEqual({ project_id: "project_2", name: "Synthetic DEV B", environment_type: "DEV" });
          const environment = { id: "environment_2", name: body.name };
          environmentsByProject.project_2 = [environment];
          return Promise.resolve(jsonResponse(environment));
        }
        const projectMatch = /project_id=([^&]+)/.exec(url);
        const projectKey = projectMatch?.[1] ?? "project_1";
        const items = environmentsByProject[projectKey] ?? [];
        return Promise.resolve(jsonResponse({ items, total: items.length, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/platform/projects/project_1/setup-status")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            project_id: "project_1",
            project_name: "Synthetic Project",
            status: "READY",
            profile_count: 1,
            environment_count: 1,
            active_context_selected: true,
            missing_requirements: []
          })
        );
      }
      if (url.endsWith("/api/v1/platform/active-context/capabilities")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            user_id: "user_admin",
            project_id: "project_1",
            is_admin: true,
            roles: ["ADMIN"],
            capabilities: ["*"]
          })
        );
      }
      if (url.endsWith("/api/v1/platform/feature-flags")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          featureFlagRequests.push(body);
          expect(body).toEqual({ name: "dev_tools", enabled: true, scope: "global" });
          featureFlags = [{ id: "flag_1", name: "dev_tools", enabled: true, scope: "global" }];
          return Promise.resolve(jsonResponse(featureFlags[0]));
        }
        return Promise.resolve(jsonResponse({ items: featureFlags, total: featureFlags.length, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/platform/jobs")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          createRequests.push(body);
          expect(body).toEqual({
            job_type: "DEMO_ECHO",
            source_module: "platform",
            project_id: "project_1",
            profile_id: "profile_1",
            environment_id: "environment_1",
            domain_name: "OTM1",
            input: { value: "synthetic-admin-ui" },
            execute_now: false
          });
          const created = {
            ...jobs[0],
            id: "job_created",
            status: "PENDING",
            progress: 0,
            message: "Job created.",
            input: { value: "synthetic-admin-ui" },
            result: {},
            created_at: "2026-05-21T10:05:00",
            started_at: null,
            finished_at: null,
            cancelled_at: null
          };
          jobs = [created, ...jobs];
          jobEvents.job_created = [
            {
              id: "event_created",
              job_id: "job_created",
              event_type: "JOB_CREATED",
              status_before: null,
              status_after: "PENDING",
              message: "Job created.",
              payload: { job_id: "job_created", job_type: "DEMO_ECHO", source_module: "platform" },
              created_by: "admin@example.test",
              created_at: "2026-05-21T10:05:00"
            }
          ];
          return Promise.resolve(jsonResponse(created));
        }
        return Promise.resolve(jsonResponse({ items: jobs, total: jobs.length, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/platform/jobs/job_pending/cancel")) {
        expect(init?.method).toBe("POST");
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        cancelRequests.push(url);
        const cancelled = {
          ...jobs.find((job) => job.id === "job_pending")!,
          status: "CANCELLED",
          progress: 100,
          message: "Job cancelled.",
          cancelled_at: "2026-05-21T10:04:00"
        };
        jobs = jobs.map((job) => (job.id === "job_pending" ? cancelled : job));
        jobEvents.job_pending = [
          ...jobEvents.job_pending,
          {
            id: "event_pending_cancelled",
            job_id: "job_pending",
            event_type: "JOB_CANCELLED",
            status_before: "PENDING",
            status_after: "CANCELLED",
            message: "Job cancelled.",
            payload: { job_id: "job_pending", job_type: "DEMO_ECHO", source_module: "platform" },
            created_by: "admin@example.test",
            created_at: "2026-05-21T10:04:00"
          }
        ];
        return Promise.resolve(jsonResponse(cancelled));
      }
      if (url.endsWith("/api/v1/platform/jobs/job_created/run")) {
        expect(init?.method).toBe("POST");
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        runRequests.push(url);
        const updated = {
          ...jobs.find((job) => job.id === "job_created")!,
          status: "SUCCEEDED",
          progress: 100,
          message: "Demo job completed.",
          result: { echo: { value: "synthetic-admin-ui" } },
          started_at: "2026-05-21T10:05:01",
          finished_at: "2026-05-21T10:05:02"
        };
        jobs = jobs.map((job) => (job.id === "job_created" ? updated : job));
        jobEvents.job_created = [
          ...jobEvents.job_created,
          {
            id: "event_started",
            job_id: "job_created",
            event_type: "JOB_STARTED",
            status_before: "PENDING",
            status_after: "RUNNING",
            message: "Job started.",
            payload: { job_id: "job_created", job_type: "DEMO_ECHO", source_module: "platform" },
            created_by: "admin@example.test",
            created_at: "2026-05-21T10:05:01"
          },
          {
            id: "event_succeeded",
            job_id: "job_created",
            event_type: "JOB_SUCCEEDED",
            status_before: "RUNNING",
            status_after: "SUCCEEDED",
            message: "Demo job completed.",
            payload: { job_id: "job_created", job_type: "DEMO_ECHO", source_module: "platform" },
            created_by: "admin@example.test",
            created_at: "2026-05-21T10:05:02"
          }
        ];
        return Promise.resolve(jsonResponse(updated));
      }
      if (url.includes("/api/v1/platform/jobs/") && url.endsWith("/events")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const jobId = /\/api\/v1\/platform\/jobs\/([^/]+)\/events$/.exec(url)?.[1];
        return Promise.resolve(jsonResponse({ items: jobEvents[jobId ?? ""] ?? [], total: jobEvents[jobId ?? ""]?.length ?? 0, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/platform/audit-logs")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            items: [
              { id: "audit_1", action: "job.create", target_type: "job", target_id: "job_pending" },
              { id: "audit_2", action: "feature_flag.upsert", target_type: "feature_flag", target_id: "flag_1" }
            ],
            total: 2,
            page: 1,
            page_size: 50
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp();
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Admin Console" });
    expect(await screen.findByText("admin@example.test")).toBeInTheDocument();
    expect((await screen.findAllByText("Synthetic Project")).length).toBeGreaterThan(0);
    expect(await screen.findByText("Effective capabilities")).toBeInTheDocument();
    expect(await screen.findByText("*")).toBeInTheDocument();
    expect((await within(await screen.findByLabelText("Platform jobs")).findAllByText("job_pending")).length).toBeGreaterThan(0);
    expect(await within(await screen.findByLabelText("Audit trail")).findByText("feature_flag.upsert")).toBeInTheDocument();
    expect(await within(await screen.findByLabelText("Selected job events")).findByText("JOB_CREATED")).toBeInTheDocument();
    expect(await within(await screen.findByLabelText("Feature flags")).findByText("dev_tools")).toBeInTheDocument();
    expect(await within(await screen.findByLabelText("Feature flags")).findByText("DISABLED")).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Workspace name"), "Synthetic Workspace B");
    await userEvent.click(screen.getByRole("button", { name: "Create workspace" }));
    await waitFor(() => expect(workspaceRequests).toEqual([{ name: "Synthetic Workspace B" }]));
    expect((await within(await screen.findByLabelText("Setup authoring")).findAllByText("Synthetic Workspace B")).length).toBeGreaterThan(0);

    await userEvent.selectOptions(screen.getByLabelText("Project workspace"), "workspace_2");
    await userEvent.type(screen.getByLabelText("Project name"), "Synthetic Project B");
    await userEvent.click(screen.getByRole("button", { name: "Create project" }));
    await waitFor(() => expect(projectRequests).toEqual([{ workspace_id: "workspace_2", name: "Synthetic Project B" }]));
    expect((await within(await screen.findByLabelText("Setup authoring")).findAllByText("Synthetic Project B")).length).toBeGreaterThan(0);

    await userEvent.selectOptions(screen.getByLabelText("Profile project"), "project_2");
    await userEvent.type(screen.getByLabelText("Profile name"), "Synthetic Profile B");
    await userEvent.click(screen.getByRole("button", { name: "Create profile" }));
    await waitFor(() => expect(profileRequests).toEqual([{ project_id: "project_2", name: "Synthetic Profile B" }]));
    expect((await within(await screen.findByLabelText("Setup authoring")).findAllByText("Synthetic Profile B")).length).toBeGreaterThan(0);

    await userEvent.selectOptions(screen.getByLabelText("Environment project"), "project_2");
    await userEvent.selectOptions(screen.getByLabelText("Environment type"), "DEV");
    await userEvent.type(screen.getByLabelText("Environment name"), "Synthetic DEV B");
    await userEvent.click(screen.getByRole("button", { name: "Create environment" }));
    await waitFor(() => expect(environmentRequests).toEqual([{ project_id: "project_2", name: "Synthetic DEV B", environment_type: "DEV" }]));
    expect((await within(await screen.findByLabelText("Setup authoring")).findAllByText("Synthetic DEV B")).length).toBeGreaterThan(0);

    await userEvent.type(screen.getByLabelText("Workspace name"), "Temporary Workspace Draft");
    await userEvent.selectOptions(screen.getByLabelText("Project workspace"), "workspace_2");
    await userEvent.type(screen.getByLabelText("Project name"), "Temporary Project Draft");
    await userEvent.selectOptions(screen.getByLabelText("Profile project"), "project_2");
    await userEvent.type(screen.getByLabelText("Profile name"), "Temporary Profile Draft");
    await userEvent.selectOptions(screen.getByLabelText("Environment project"), "project_2");
    await userEvent.selectOptions(screen.getByLabelText("Environment type"), "UAT");
    await userEvent.type(screen.getByLabelText("Environment name"), "Temporary UAT Draft");
    await userEvent.click(screen.getByRole("button", { name: "Reset setup drafts" }));
    expect(screen.getByLabelText("Workspace name")).toHaveValue("");
    expect(screen.getByLabelText("Project workspace")).toHaveValue("workspace_1");
    expect(screen.getByLabelText("Project name")).toHaveValue("");
    expect(screen.getByLabelText("Profile project")).toHaveValue("project_1");
    expect(screen.getByLabelText("Profile name")).toHaveValue("");
    expect(screen.getByLabelText("Environment project")).toHaveValue("project_1");
    expect(screen.getByLabelText("Environment type")).toHaveValue("DEV");
    expect(screen.getByLabelText("Environment name")).toHaveValue("");
    expect(screen.queryByText("Created environment Synthetic DEV B.")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Enable feature flag dev_tools" }));
    await waitFor(() => expect(within(screen.getByLabelText("Feature flags")).getByText("ENABLED")).toBeInTheDocument());
    expect(featureFlagRequests).toEqual([{ name: "dev_tools", enabled: true, scope: "global" }]);

    await userEvent.click(screen.getByRole("button", { name: "Cancel job job_pending" }));
    await waitFor(() => expect(within(screen.getByLabelText("Platform jobs")).getAllByText("CANCELLED").length).toBeGreaterThan(0));
    expect(await within(await screen.findByLabelText("Selected job events")).findByText("JOB_CANCELLED")).toBeInTheDocument();
    expect(cancelRequests).toHaveLength(1);

    await userEvent.click(screen.getByRole("button", { name: "Create demo job" }));
    expect((await within(await screen.findByLabelText("Platform jobs")).findAllByText("job_created")).length).toBeGreaterThan(0);
    expect(createRequests).toHaveLength(1);

    await userEvent.click(screen.getByRole("button", { name: "Run job job_created" }));
    await waitFor(() => expect(within(screen.getByLabelText("Platform jobs")).getAllByText("SUCCEEDED").length).toBeGreaterThan(0));
    expect(await within(await screen.findByLabelText("Selected job events")).findByText("JOB_SUCCEEDED")).toBeInTheDocument();
    expect((await screen.findAllByText("Demo job completed.")).length).toBeGreaterThan(0);
    expect(runRequests).toHaveLength(1);

    await userEvent.click(screen.getByRole("button", { name: "View events job_pending" }));
    expect(document.querySelector(".form-success")?.textContent ?? "").not.toContain("Demo job completed.");
    expect(await within(await screen.findByLabelText("Selected job events")).findByText("JOB_CANCELLED")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("link", { name: /Project Cockpit/ }));
    await screen.findByRole("heading", { name: "Project Cockpit" });
    await userEvent.click(screen.getByRole("link", { name: /Admin Console/ }));
    await screen.findByRole("heading", { name: "Admin Console" });
    expect((await within(await screen.findByLabelText("Platform jobs")).findAllByText("job_created")).length).toBeGreaterThan(0);
  });
});
