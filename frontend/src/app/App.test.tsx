import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "../platform/auth";

function renderApp(initialPath = "/") {
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

describe("App shell", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
  });

  it("renders a backend session login before protected contracts are called", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    renderApp();

    expect(screen.getByText("Workbench")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Sign in to OTM Workbench" })).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("logs in with the backend session endpoint and sends bearer auth to protected contracts", async () => {
    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(
          new Response(JSON.stringify({ access_token: "session_token", token_type: "bearer" }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(JSON.stringify({ items: [], total: 0, page: 1, page_size: 50 }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              theme_mode: "light",
              follow_system_theme: false,
              density: "comfortable",
              sidebar_mode: "expanded"
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              module_id: "home",
              title: "Project Cockpit",
              status: "needs_context",
              description: "Project-level operational overview.",
              active_context: {},
              setup_status: null,
              counts: { recent_jobs: 0, recent_artifacts: 0, recent_evidence: 0 },
              module_summary: { total: 0, counts_by_status: {}, items: [] },
              recent_jobs: [],
              recent_artifacts: [],
              recent_evidence: [],
              available_actions: []
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp();
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => expect(screen.getByRole("heading", { name: "Project Cockpit" })).toBeInTheDocument());
    expect(sessionStorage.getItem("otm_workbench.session_token")).toBe("session_token");
  });

  it("updates active project context with backend selector contracts", async () => {
    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(
          new Response(JSON.stringify({ access_token: "session_token", token_type: "bearer" }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return Promise.resolve(
          new Response(JSON.stringify({ items: [], total: 0, page: 1, page_size: 50 }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              theme_mode: "light",
              follow_system_theme: false,
              density: "comfortable",
              sidebar_mode: "expanded"
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              module_id: "home",
              title: "Project Cockpit",
              status: "needs_context",
              description: "Project-level operational overview.",
              active_context: {},
              setup_status: null,
              counts: { recent_jobs: 0, recent_artifacts: 0, recent_evidence: 0 },
              module_summary: { total: 0, counts_by_status: {}, items: [] },
              recent_jobs: [],
              recent_artifacts: [],
              recent_evidence: [],
              available_actions: []
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/platform/projects")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({ items: [{ id: "project_1", name: "Synthetic Rollout" }], total: 1, page: 1, page_size: 50 }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/platform/profiles?project_id=project_1")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({ items: [{ id: "profile_1", name: "Default" }], total: 1, page: 1, page_size: 50 }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/platform/environments?project_id=project_1")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({ items: [{ id: "environment_1", name: "DEV" }], total: 1, page: 1, page_size: 50 }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/platform/active-context")) {
        expect(init?.method).toBe("POST");
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        expect(JSON.parse(String(init?.body))).toEqual({
          project_id: "project_1",
          profile_id: "profile_1",
          environment_id: "environment_1",
          domain_name: "otm1",
          can_view_all_domains: false
        });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              project_id: "project_1",
              profile_id: "profile_1",
              environment_id: "environment_1",
              domain_name: "OTM1",
              allowed_domains: ["PUBLIC", "OTM1"],
              can_view_all_domains: false
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp();
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Project Cockpit" });
    await userEvent.selectOptions(await screen.findByLabelText("Project"), "project_1");
    await userEvent.selectOptions(await screen.findByLabelText("Profile"), "profile_1");
    await userEvent.selectOptions(await screen.findByLabelText("Environment"), "environment_1");
    await userEvent.type(screen.getByLabelText("Domain"), "otm1");
    await userEvent.click(screen.getByRole("button", { name: "Apply context" }));

    await waitFor(() => expect(screen.getByText("Context updated.")).toBeInTheDocument());
  });

  it("stores theme preference through the backend contract", async () => {
    let savedPreferences = {
      theme_mode: "light",
      follow_system_theme: false,
      density: "comfortable",
      sidebar_mode: "expanded"
    };
    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(
          new Response(JSON.stringify({ access_token: "session_token", token_type: "bearer" }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return Promise.resolve(
          new Response(JSON.stringify({ items: [], total: 0, page: 1, page_size: 50 }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences") && init?.method === "PUT") {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        savedPreferences = JSON.parse(String(init?.body));
        expect(savedPreferences).toEqual({
          theme_mode: "dark",
          follow_system_theme: false,
          density: "comfortable",
          sidebar_mode: "expanded"
        });
        return Promise.resolve(
          new Response(JSON.stringify(savedPreferences), { status: 200, headers: { "Content-Type": "application/json" } })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(
          new Response(JSON.stringify(savedPreferences), { status: 200, headers: { "Content-Type": "application/json" } })
        );
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              module_id: "home",
              title: "Project Cockpit",
              status: "needs_context",
              description: "Project-level operational overview.",
              active_context: {},
              setup_status: null,
              counts: { recent_jobs: 0, recent_artifacts: 0, recent_evidence: 0 },
              module_summary: { total: 0, counts_by_status: {}, items: [] },
              recent_jobs: [],
              recent_artifacts: [],
              recent_evidence: [],
              available_actions: []
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp();
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Project Cockpit" });
    await userEvent.click(screen.getByRole("button", { name: "Use dark mode" }));

    await waitFor(() => expect(screen.getByRole("button", { name: "Use dark mode" })).toHaveAttribute("aria-pressed", "true"));
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/platform/user-preferences",
      expect.objectContaining({ method: "PUT" })
    );
  });

  it("stores density and sidebar preferences through the backend contract", async () => {
    let savedPreferences = {
      theme_mode: "light",
      follow_system_theme: false,
      density: "comfortable",
      sidebar_mode: "expanded"
    };
    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(
          new Response(JSON.stringify({ access_token: "session_token", token_type: "bearer" }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [{ id: "home", label: "Home", path: "/", status: "ACTIVE" }],
              total: 1,
              page: 1,
              page_size: 50
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences") && init?.method === "PUT") {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        savedPreferences = JSON.parse(String(init?.body));
        return Promise.resolve(
          new Response(JSON.stringify(savedPreferences), { status: 200, headers: { "Content-Type": "application/json" } })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(
          new Response(JSON.stringify(savedPreferences), { status: 200, headers: { "Content-Type": "application/json" } })
        );
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              module_id: "home",
              title: "Project Cockpit",
              status: "needs_context",
              description: "Project-level operational overview.",
              active_context: {},
              setup_status: null,
              counts: { recent_jobs: 0, recent_artifacts: 0, recent_evidence: 0 },
              module_summary: { total: 1, counts_by_status: { ACTIVE: 1 }, items: [] },
              recent_jobs: [],
              recent_artifacts: [],
              recent_evidence: [],
              available_actions: []
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    const view = renderApp();
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Project Cockpit" });
    await userEvent.click(screen.getByRole("button", { name: "Use compact density" }));

    await waitFor(() => expect(view.container.querySelector(".app-shell")).toHaveAttribute("data-density", "compact"));
    expect(savedPreferences).toMatchObject({ density: "compact", sidebar_mode: "expanded" });

    await userEvent.click(screen.getByRole("button", { name: "Collapse sidebar" }));

    await waitFor(() => expect(view.container.querySelector(".app-shell")).toHaveAttribute("data-sidebar", "collapsed"));
    expect(savedPreferences).toMatchObject({ density: "compact", sidebar_mode: "collapsed" });
  });

  it("renders Rates Studio from the backend module summary contract", async () => {
    const createObjectURL = vi.fn(() => "blob:rates-export");
    const revokeObjectURL = vi.fn();
    const anchorClick = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    vi.stubGlobal("URL", { ...URL, createObjectURL, revokeObjectURL });
    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(
          new Response(JSON.stringify({ access_token: "session_token", token_type: "bearer" }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                { id: "home", label: "Project Cockpit", path: "/home", status: "ACTIVE" },
                { id: "rates", label: "Rates Studio", path: "/rates", status: "PLANNED" }
              ],
              total: 2,
              page: 1,
              page_size: 50
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              theme_mode: "light",
              follow_system_theme: false,
              density: "comfortable",
              sidebar_mode: "expanded"
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/modules/rates/summary")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              module_id: "rates",
              status: "ok",
              title: "Rates Studio",
              description: "Prepare, validate, approve and export OTM rates packages.",
              primary_object: "rate_batch",
              counts: [
                { key: "total", label: "Total", value: 2, severity: "neutral" },
                { key: "ready_for_approval", label: "Ready for approval", value: 1, severity: "success" },
                { key: "ready_for_export", label: "Ready for export", value: 0, severity: "success" },
                { key: "blocked", label: "Blocked", value: 1, severity: "warning" }
              ],
              recent_objects: [
                {
                  id: "batch_1",
                  code: "ACCESSORIAL_ONLY",
                  display_name: "Synthetic ready batch",
                  status: "EXPORT_PREVIEWED",
                  project_id: null,
                  profile_id: null,
                  environment_id: null,
                  domain_name: "OTM1",
                  summary: {
                    ready_for_approval: true,
                    ready_for_export: false,
                    table_count: 1,
                    row_count: 1,
                    issue_summary: { errors: 0, warnings: 0 }
                  },
                  badges: [],
                  available_actions: []
                },
                {
                  id: "batch_2",
                  code: "ACCESSORIAL_ONLY",
                  display_name: "Synthetic blocked batch",
                  status: "DRAFT",
                  project_id: null,
                  profile_id: null,
                  environment_id: null,
                  domain_name: "OTM1",
                  summary: {
                    ready_for_approval: false,
                    ready_for_export: false,
                    table_count: 0,
                    row_count: 0,
                    issue_summary: { errors: 0, warnings: 0 }
                  },
                  badges: ["NO_ROWS"],
                  available_actions: []
                }
              ],
              open_blockers: [
                {
                  object_id: "batch_2",
                  object_type: "rate_batch",
                  severity: "warning",
                  codes: ["NO_ROWS"],
                  message: "Rate batch is not ready: NO_ROWS"
                }
              ],
              recent_jobs: [],
              recent_artifacts: [],
              available_actions: [
                {
                  key: "create_batch",
                  label: "Create rate batch",
                  method: "POST",
                  href: "/api/v1/modules/rates/batches",
                  variant: "primary",
                  icon_key: "plus",
                  disabled: false,
                  disabled_reason: null,
                  requires_confirmation: false
                }
              ]
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_1")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              id: "batch_1",
              project_id: null,
              environment_id: null,
              profile_id: null,
              scenario_code: "ACCESSORIAL_ONLY",
              catalog_macro_object_code: "RATE_RECORD",
              catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
              name: "Synthetic ready batch",
              description: "",
              status: "EXPORT_PREVIEWED",
              source_type: "api",
              domain_name: "OTM1",
              created_by: null,
              summary_json: "{}",
              tables: [
                {
                  id: "table_1",
                  batch_id: "batch_1",
                  table_name: "ACCESSORIAL_COST",
                  sequence_index: 1,
                  requirement_level: "OPTIONAL",
                  row_count: 1,
                  status: "VALID"
                }
              ],
              available_actions: [
                {
                  key: "approve",
                  label: "Approve",
                  method: "POST",
                  href: "/api/v1/modules/rates/batches/batch_1/approve",
                  variant: "primary",
                  icon_key: "check",
                  disabled: false,
                  disabled_reason: null,
                  requires_confirmation: true
                }
              ]
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_1/artifacts")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              batch_id: "batch_1",
              catalog_macro_object_code: "RATE_RECORD",
              catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
              items: [
                {
                  id: "artifact_1",
                  artifact_type: "rates_csv_export",
                  file_name: "rates_export.zip",
                  content_type: "application/zip",
                  sha256: "abc123",
                  size_bytes: 1234,
                  sensitivity_level: "client_safe",
                  download_url: "/api/v1/modules/rates/batches/batch_1/artifacts/artifact_1/download"
                }
              ],
              total: 1
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_1/artifacts/artifact_1/download")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(new Blob(["synthetic zip"], { type: "application/zip" }), {
            status: 200,
            headers: {
              "Content-Disposition": 'attachment; filename="rates_export.zip"',
              "Content-Type": "application/zip"
            }
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_1/evidence")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              batch_id: "batch_1",
              catalog_macro_object_code: "RATE_RECORD",
              catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
              items: [
                {
                  id: "evidence_1",
                  evidence_type: "rates_export",
                  status: "CREATED",
                  summary_json: "{}",
                  artifact_id: "artifact_1",
                  manifest_id: "manifest_1",
                  client_safe: true,
                  sensitivity_level: "client_safe"
                }
              ],
              total: 1
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_2/validate")) {
        expect(init?.method).toBe("POST");
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(JSON.stringify({ batch_id: "batch_2", status: "VALIDATED", issues: [] }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_2")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              id: "batch_2",
              project_id: null,
              environment_id: null,
              profile_id: null,
              scenario_code: "ACCESSORIAL_ONLY",
              catalog_macro_object_code: "RATE_RECORD",
              catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
              name: "Synthetic blocked batch",
              description: "",
              status: "DRAFT",
              source_type: "api",
              domain_name: "OTM1",
              created_by: null,
              summary_json: "{}",
              tables: [],
              available_actions: [
                {
                  key: "validate",
                  label: "Validate",
                  method: "POST",
                  href: "/api/v1/modules/rates/batches/batch_2/validate",
                  variant: "primary",
                  icon_key: "check",
                  disabled: false,
                  disabled_reason: null,
                  requires_confirmation: false,
                  result_hint: "refresh_object"
                }
              ]
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_2/artifacts")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              batch_id: "batch_2",
              catalog_macro_object_code: "RATE_RECORD",
              catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
              items: [],
              total: 0
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_2/evidence")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              batch_id: "batch_2",
              catalog_macro_object_code: "RATE_RECORD",
              catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
              items: [],
              total: 0
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/rates");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Rates Studio" });
    expect(screen.getByLabelText("Rates summary metrics")).toBeInTheDocument();
    expect(screen.getByText("Synthetic ready batch")).toBeInTheDocument();
    expect(await screen.findByText("ACCESSORIAL_COST")).toBeInTheDocument();
    expect(await screen.findByText("rates_export.zip")).toBeInTheDocument();
    expect(screen.getByText("rates_export")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Download" }));
    expect(await screen.findByText("Download started: rates_export.zip.")).toBeInTheDocument();
    expect(createObjectURL).toHaveBeenCalledOnce();
    expect(anchorClick).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:rates-export");
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByText("Ready for approval")).toBeInTheDocument();
    expect(screen.getByText("Rate batch is not ready: NO_ROWS")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /Synthetic blocked batch/ }));

    expect(await screen.findByText("No tables have been staged for this batch.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Validate" }));

    expect(await screen.findByText("Validate completed.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/modules/rates/batches/batch_2/validate",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("renders Assets Library from backend list and detail contracts", async () => {
    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(
          new Response(JSON.stringify({ access_token: "session_token", token_type: "bearer" }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                { id: "home", label: "Project Cockpit", path: "/home", status: "ACTIVE" },
                { id: "assets", label: "Assets Library", path: "/assets", status: "ACTIVE" }
              ],
              total: 2,
              page: 1,
              page_size: 50
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              theme_mode: "light",
              follow_system_theme: false,
              density: "comfortable",
              sidebar_mode: "expanded"
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/modules/assets/assets")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "asset_1",
                  project_id: null,
                  profile_id: null,
                  environment_id: null,
                  name: "Synthetic Mapping Spec",
                  description: "Client-safe synthetic support asset.",
                  asset_type: "SPEC",
                  category: "INTEGRATION",
                  visibility: "PROJECT",
                  scope_type: "PROJECT",
                  sensitivity: "INTERNAL",
                  status: "DRAFT",
                  module_id: "integration_mapping",
                  macro_object_code: "ORDER_RELEASE",
                  otm_table_name: "ORDER_RELEASE",
                  tags: ["SYNTHETIC", "MVP0"],
                  current_version_id: "version_1",
                  created_by: "synthetic.user@example.test",
                  created_at: "2026-05-21T00:00:00",
                  updated_at: "2026-05-21T00:00:00"
                }
              ],
              total: 1,
              page: 1,
              page_size: 50
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_1")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              id: "asset_1",
              project_id: null,
              profile_id: null,
              environment_id: null,
              name: "Synthetic Mapping Spec",
              description: "Client-safe synthetic support asset.",
              asset_type: "SPEC",
              category: "INTEGRATION",
              visibility: "PROJECT",
              scope_type: "PROJECT",
              sensitivity: "INTERNAL",
              status: "DRAFT",
              module_id: "integration_mapping",
              macro_object_code: "ORDER_RELEASE",
              otm_table_name: "ORDER_RELEASE",
              tags: ["SYNTHETIC", "MVP0"],
              current_version_id: "version_1",
              created_by: "synthetic.user@example.test",
              created_at: "2026-05-21T00:00:00",
              updated_at: "2026-05-21T00:00:00"
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_1/versions")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "version_1",
                  asset_id: "asset_1",
                  version_number: 1,
                  status: "ACTIVE",
                  file_name: "synthetic_spec.md",
                  content_type: "text/markdown",
                  sha256: "abc123",
                  size_bytes: 42,
                  uploaded_by: "synthetic.user@example.test",
                  created_at: "2026-05-21T00:00:00",
                  updated_at: "2026-05-21T00:00:00"
                }
              ],
              total: 1,
              page: 1,
              page_size: 50
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/assets");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Assets Library" });
    expect(await screen.findByText("Synthetic Mapping Spec")).toBeInTheDocument();
    expect(screen.getAllByText("INTEGRATION").length).toBeGreaterThan(0);
    expect(screen.getAllByText("ORDER_RELEASE").length).toBeGreaterThan(0);
    expect(await screen.findByText("synthetic_spec.md")).toBeInTheDocument();
    expect(screen.getByText("42 bytes")).toBeInTheDocument();
    expect(screen.queryByText(/storage_path/i)).not.toBeInTheDocument();
  });
});
