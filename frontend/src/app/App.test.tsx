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

  it("renders Evidence Hub from backend list and detail contracts", async () => {
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
                { id: "evidence", label: "Evidence Hub", path: "/evidence", status: "ACTIVE" }
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
      if (url.endsWith("/api/v1/evidence-hub/evidence")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "evidence_1",
                  project_id: null,
                  source_module: "rates",
                  evidence_type: "rates_csv_export",
                  status: "CREATED",
                  summary: { status: "ok", note_present: true },
                  artifact: {
                    id: "artifact_1",
                    source_module: "rates",
                    artifact_type: "rates_csv_zip",
                    file_name: "demo.zip",
                    content_type: "application/zip",
                    sha256: "abc123",
                    size_bytes: 1234,
                    sensitivity_level: "internal",
                    created_at: "2026-05-21T00:00:00"
                  },
                  manifest: {
                    id: "manifest_1",
                    source_module: "rates",
                    status: "CREATED",
                    manifest_type: "rates_csv_export",
                    schema_version: "rates-csv-export-manifest/v1",
                    created_at: "2026-05-21T00:00:00"
                  },
                  client_safe: true,
                  sensitivity_level: "client_safe",
                  created_at: "2026-05-21T00:00:00"
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
      if (url.endsWith("/api/v1/evidence-hub/evidence/evidence_1")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              id: "evidence_1",
              project_id: null,
              source_module: "rates",
              evidence_type: "rates_csv_export",
              status: "CREATED",
              summary: { status: "ok", note_present: true },
              artifact: {
                id: "artifact_1",
                source_module: "rates",
                artifact_type: "rates_csv_zip",
                file_name: "demo.zip",
                content_type: "application/zip",
                sha256: "abc123",
                size_bytes: 1234,
                sensitivity_level: "internal",
                created_at: "2026-05-21T00:00:00"
              },
              manifest: {
                id: "manifest_1",
                source_module: "rates",
                status: "CREATED",
                manifest_type: "rates_csv_export",
                schema_version: "rates-csv-export-manifest/v1",
                created_at: "2026-05-21T00:00:00"
              },
              client_safe: true,
              sensitivity_level: "client_safe",
              created_at: "2026-05-21T00:00:00"
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/evidence");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Evidence Hub" });
    expect(await screen.findByText("rates_csv_export")).toBeInTheDocument();
    expect(screen.getAllByText("rates").length).toBeGreaterThan(0);
    expect(screen.getAllByText("demo.zip").length).toBeGreaterThan(0);
    expect(screen.getByText("rates-csv-export-manifest/v1")).toBeInTheDocument();
    expect(screen.queryByText(/file_path/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/manifest_json/i)).not.toBeInTheDocument();
  });

  it("renders Load Plan from backend summary, package list, and package detail contracts", async () => {
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
                { id: "load_plan", label: "Load Plan", path: "/load-plan", status: "ACTIVE" }
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
      if (url.endsWith("/api/v1/modules/load-plan/summary")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              registered_packages: 1,
              by_source_module: { rates: 1 },
              by_status: { REGISTERED: 1 },
              by_catalog_macro_object: {
                RATE_RECORD: {
                  package_count: 1,
                  catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
                }
              },
              next_actions: ["build_csvutil"]
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/modules/load-plan/packages")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "package_1",
                  project_id: "project_1",
                  environment_id: "environment_1",
                  profile_id: "profile_1",
                  source_module: "rates",
                  source_entity_type: "rate_batch",
                  source_entity_id: "batch_1",
                  package_type: "rates_csv_zip",
                  status: "REGISTERED",
                  artifact_id: "artifact_1",
                  manifest_id: "manifest_1",
                  evidence_id: "evidence_1",
                  approval_evidence_id: "approval_1",
                  load_sequence: [
                    {
                      position: 1,
                      table_name: "RATE_GEO",
                      row_count: 3,
                      requirement_level: "REQUIRED"
                    }
                  ],
                  summary: {
                    source_module: "rates",
                    package_type: "rates_csv_zip",
                    catalog_macro_object_code: "RATE_RECORD",
                    catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
                    table_count: 1,
                    row_count: 3,
                    has_export_artifact: true,
                    has_approval_evidence: true
                  },
                  created_by: "synthetic.user@example.test",
                  registered_at: "2026-05-21T01:00:00Z"
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
      if (url.endsWith("/api/v1/modules/load-plan/packages/package_1")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              id: "package_1",
              project_id: "project_1",
              environment_id: "environment_1",
              profile_id: "profile_1",
              source_module: "rates",
              source_entity_type: "rate_batch",
              source_entity_id: "batch_1",
              package_type: "rates_csv_zip",
              status: "REGISTERED",
              artifact_id: "artifact_1",
              manifest_id: "manifest_1",
              evidence_id: "evidence_1",
              approval_evidence_id: "approval_1",
              load_sequence: [
                {
                  position: 1,
                  table_name: "RATE_GEO",
                  row_count: 3,
                  requirement_level: "REQUIRED"
                }
              ],
              summary: {
                source_module: "rates",
                package_type: "rates_csv_zip",
                catalog_macro_object_code: "RATE_RECORD",
                catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
                table_count: 1,
                row_count: 3,
                has_export_artifact: true,
                has_approval_evidence: true
              },
              created_by: "synthetic.user@example.test",
              registered_at: "2026-05-21T01:00:00Z"
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/load-plan");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Load Plan" });
    expect(await screen.findByText("rates_csv_zip")).toBeInTheDocument();
    expect(screen.getAllByText("RATE_RECORD").length).toBeGreaterThan(0);
    expect(screen.getByText("RATE_GEO")).toBeInTheDocument();
    expect(screen.getByText("3 rows")).toBeInTheDocument();
    expect(screen.queryByText(/build csvutil/i)).not.toBeInTheDocument();
  });

  it("renders Catalog Core from backend macro object, table, and load plan contracts", async () => {
    const macroObject = {
      id: "macro_1",
      code: "RATE_RECORD",
      name: "Rate Record",
      category: "RATES",
      description: "Synthetic catalog macro object for rate packages.",
      default_load_order: 40,
      default_method: "CSVUTIL",
      method_options: ["CSVUTIL"],
      allow_cutover: true,
      allow_csvutil: true,
      evidence_required_default: true,
      summary: {
        table_count: 1,
        dependency_count: 1,
        validated_table_count: 1,
        all_tables_validated: true,
        csvutil_table_count: 1,
        cutover_table_count: 1
      }
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
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                { id: "home", label: "Project Cockpit", path: "/home", status: "ACTIVE" },
                { id: "catalog", label: "OTM Catalog Core", path: "/catalog", status: "ACTIVE" }
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
      if (url.endsWith("/api/v1/catalog/macro-objects")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(JSON.stringify({ items: [macroObject], total: 1, page: 1, page_size: 50 }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      if (url.endsWith("/api/v1/catalog/macro-objects/RATE_RECORD")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...macroObject,
              tables: [
                {
                  id: "macro_table_1",
                  table_name: "RATE_GEO",
                  relationship_role: "PRIMARY",
                  is_primary_table: true,
                  is_required: true,
                  data_category: "REFERENCE",
                  validated_by_datadict: true,
                  allow_csvutil: true,
                  allow_cutover: true
                }
              ],
              dependencies: [
                {
                  id: "dependency_1",
                  depends_on_code: "LOCATION",
                  depends_on_name: "Location",
                  dependency_type: "REFERENCE",
                  is_required: true,
                  notes: "Synthetic dependency"
                }
              ]
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      if (url.endsWith("/api/v1/catalog/macro-objects/RATE_RECORD/tables")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "macro_table_1",
                  table_name: "RATE_GEO",
                  relationship_role: "PRIMARY",
                  is_primary_table: true,
                  is_required: true,
                  data_category: "REFERENCE",
                  validated_by_datadict: true,
                  allow_csvutil: true,
                  allow_cutover: true
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
      if (url.endsWith("/api/v1/catalog/macro-objects/RATE_RECORD/load-plan")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              macro_object_code: "RATE_RECORD",
              items: [
                {
                  macro_object_code: "LOCATION",
                  macro_object_name: "Location",
                  dependency_role: "DEPENDENCY",
                  dependency_type: "REFERENCE",
                  is_required: true,
                  tables: ["LOCATION"],
                  table_count: 1,
                  all_tables_validated: true
                },
                {
                  macro_object_code: "RATE_RECORD",
                  macro_object_name: "Rate Record",
                  dependency_role: "TARGET",
                  dependency_type: "TARGET",
                  is_required: true,
                  tables: ["RATE_GEO"],
                  table_count: 1,
                  all_tables_validated: true
                }
              ],
              summary: {
                step_count: 2,
                dependency_count: 1,
                target_table_count: 1,
                all_target_tables_validated: true
              }
            }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          )
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/catalog");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "OTM Catalog Core" });
    expect(await screen.findByText("RATE_RECORD")).toBeInTheDocument();
    expect(screen.getAllByText("Rate Record").length).toBeGreaterThan(0);
    expect(screen.getByText("RATE_GEO")).toBeInTheDocument();
    expect(screen.getByText("LOCATION")).toBeInTheDocument();
    expect(screen.queryByText(/validate table/i)).not.toBeInTheDocument();
  });

  it("renders Master Data from backend template list and detail contracts", async () => {
    const template = {
      id: "template_1",
      code: "REGION_TEMPLATE",
      name: "Region Template",
      version: "1.0",
      status: "ACTIVE",
      catalog_macro_object_code: "REGION",
      data_category: "MASTER_DATA",
      target_tables: ["REGION"],
      sheets: [
        {
          code: "REGION",
          name: "Region",
          target_table: "REGION",
          fields: [
            {
              name: "region_gid",
              label: "Region GID",
              target_column: "REGION_GID",
              required: true
            }
          ]
        }
      ],
      description: "Synthetic master data template for region setup.",
      created_at: "2026-05-21T01:00:00",
      updated_at: "2026-05-21T01:00:00"
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
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                { id: "home", label: "Project Cockpit", path: "/home", status: "ACTIVE" },
                { id: "master_data", label: "Data Factory", path: "/master-data", status: "ACTIVE" }
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
      if (url.endsWith("/api/v1/modules/master-data/templates")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(JSON.stringify({ items: [template], total: 1, page: 1, page_size: 50 }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/REGION_TEMPLATE")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(JSON.stringify(template), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/master-data");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Data Factory" });
    expect(await screen.findByText("REGION_TEMPLATE")).toBeInTheDocument();
    expect(screen.getAllByText("REGION").length).toBeGreaterThan(0);
    expect(screen.getByText("Region GID")).toBeInTheDocument();
    expect(screen.queryByText(/build workbook/i)).not.toBeInTheDocument();
  });
});
