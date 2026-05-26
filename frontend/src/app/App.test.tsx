import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
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

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

function platformPreferences() {
  return {
    density: "comfortable",
    follow_system_theme: false,
    sidebar_mode: "expanded",
    theme_mode: "light"
  };
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

  it("keeps unknown backend routes behind the module unavailable state", async () => {
    const fetchMock = vi.fn(async (input: string | URL) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return jsonResponse({ access_token: "token-1", token_type: "bearer" });
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return jsonResponse({
          items: [{ id: "rates", label: "Rates Studio", path: "/rates", status: "ACTIVE" }],
          total: 1,
          page: 1,
          page_size: 50
        });
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return jsonResponse({
          theme_mode: "light",
          follow_system_theme: false,
          density: "comfortable",
          sidebar_mode: "expanded"
        });
      }
      return jsonResponse({ detail: "Unexpected request" }, 404);
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/missing-module");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "synthetic-password");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Module unavailable" })).toBeInTheDocument();
    expect(screen.getByText("Use the backend-owned navigation menu to open an available module.")).toBeInTheDocument();
  });

  it("renders Developer Tools as a guarded technical hub instead of a generic module placeholder", async () => {
    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(jsonResponse({ access_token: "session_token", token_type: "bearer" }));
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            items: [{ id: "dev_tools", label: "Developer Tools", path: "/dev-tools", status: "DISABLED" }],
            total: 1,
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
        return Promise.resolve(
          jsonResponse({
            module_id: "home",
            title: "Project Cockpit",
            status: "ready",
            description: "Project-level operational overview.",
            active_context: {},
            setup_status: null,
            counts: { recent_jobs: 0, recent_artifacts: 0, recent_evidence: 0 },
            module_summary: { total: 1, counts_by_status: { DISABLED: 1 }, items: [] },
            recent_jobs: [],
            recent_artifacts: [],
            recent_evidence: [],
            available_actions: []
          })
        );
      }
      if (url.endsWith("/api/v1/platform/dev-tools/summary")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            module_id: "dev_tools",
            title: "Technical Diagnostics Hub",
            status: "guarded",
            description: "Controlled technical diagnostics for authorized implementation support users.",
            active_context: {
              project_id: "project_1",
              profile_id: "profile_1",
              environment_id: "env_1",
              domain_name: "OTM1",
              allowed_domains: ["PUBLIC", "OTM1"],
              can_view_all_domains: false
            },
            guards: [
              {
                key: "feature_flag",
                label: "Feature flag",
                status: "READY",
                message: "dev_tools is enabled."
              }
            ],
            counts: { available_tools: 1, disabled_tools: 1, recent_runs: 1 },
            tools: [
              {
                key: "data_dictionary",
                label: "Data Dictionary Explorer",
                status: "AVAILABLE",
                href: "/dev-tools/data-dictionary",
                required_capability: "dev_tools.data_dictionary.view",
                disabled_reason: null
              },
              {
                key: "oracle_lab",
                label: "Oracle Lab",
                status: "DISABLED",
                href: null,
                required_capability: "dev_tools.oracle_lab.run",
                disabled_reason: "Disabled until governance approves SQL lab execution."
              }
            ],
            recent_runs: [
              {
                id: "job_1",
                job_type: "DEMO_ECHO",
                source_module: "dev_tools",
                project_id: "project_1",
                profile_id: "profile_1",
                environment_id: "env_1",
                domain_name: "OTM1",
                status: "SUCCEEDED",
                progress: 100,
                message: "Job succeeded.",
                input_present: true,
                result_present: true,
                created_at: null,
                finished_at: null
              }
            ]
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/dev-tools");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Technical Diagnostics Hub" })).toBeInTheDocument();
    expect(screen.getByText("Developer Tools is controlled by backend navigation, feature flags, and capabilities.")).toBeInTheDocument();
    expect(await screen.findByText("Data Dictionary Explorer")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open Data Dictionary Explorer" })).toHaveAttribute(
      "href",
      "/dev-tools/data-dictionary"
    );
    expect(screen.getByText("Oracle Lab")).toBeInTheDocument();
    expect(screen.getByText("Disabled until governance approves SQL lab execution.")).toBeInTheDocument();
    expect(screen.getByText("DEMO_ECHO")).toBeInTheDocument();
    expect(screen.getByText("Summary returns backend-safe metadata only; raw diagnostic payloads remain hidden.")).toBeInTheDocument();
    expect(screen.queryByText("Primary list or work queue")).not.toBeInTheDocument();
  });

  it("renders Developer Tools Data Dictionary as a dedicated technical explorer", async () => {
    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(jsonResponse({ access_token: "session_token", token_type: "bearer" }));
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return Promise.resolve(
          jsonResponse({
            items: [{ id: "dev_tools", label: "Developer Tools", path: "/dev-tools", status: "PLANNED" }],
            total: 1,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(
          jsonResponse({
            module_id: "home",
            title: "Project Cockpit",
            status: "ready",
            description: "Project-level operational overview.",
            active_context: {},
            setup_status: null,
            counts: { recent_jobs: 0, recent_artifacts: 0, recent_evidence: 0 },
            module_summary: { total: 1, counts_by_status: { PLANNED: 1 }, items: [] },
            recent_jobs: [],
            recent_artifacts: [],
            recent_evidence: [],
            available_actions: []
          })
        );
      }
      if (url.endsWith("/api/v1/platform/dev-tools/data-dictionary?query=rate_geo&limit=25")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            module_id: "dev_tools",
            tool_key: "data_dictionary",
            title: "Data Dictionary Explorer",
            status: "ready",
            description: "Read-only technical table metadata from the backend Data Dictionary.",
            query: "rate_geo",
            limit: 25,
            total: 2,
            source_contract: "/api/v1/catalog/tables",
            active_context: {},
            items: [
              {
                table_name: "RATE_GEO",
                schema_name: "GLOGOWNER",
                description: "Synthetic rate geo header.",
                column_count: 12,
                data_category: "RATES_SETUP",
                is_transactional: false,
                allow_cutover: true,
                allow_csvutil: true
              },
              {
                table_name: "RATE_GEO_COST",
                schema_name: "GLOGOWNER",
                description: "Synthetic rate cost detail.",
                column_count: 18,
                data_category: "RATES_SETUP",
                is_transactional: false,
                allow_cutover: true,
                allow_csvutil: true
              }
            ]
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/dev-tools/data-dictionary?query=rate_geo");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Data Dictionary Explorer" })).toBeInTheDocument();
    expect(screen.getByText("Read-only technical table metadata from the backend Data Dictionary.")).toBeInTheDocument();
    expect(await screen.findByText("RATE_GEO_COST")).toBeInTheDocument();
    expect(screen.getAllByText("RATES_SETUP").length).toBeGreaterThan(0);
    const dataDictionaryRows = screen.getByLabelText("Developer Tools Data Dictionary tables");
    expect(within(dataDictionaryRows).getAllByRole("link", { name: "Open table" })[1]).toHaveAttribute(
      "href",
      "/dev-tools/data-dictionary/tables/RATE_GEO_COST"
    );
    expect(screen.getByRole("link", { name: "Back to Developer Tools" })).toHaveAttribute("href", "/dev-tools");
    expect(screen.queryByRole("heading", { name: "Technical Diagnostics Hub" })).not.toBeInTheDocument();
    expect(screen.queryByText("Primary list or work queue")).not.toBeInTheDocument();
  });

  it("renders Developer Tools Data Dictionary table detail as a dedicated route", async () => {
    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(jsonResponse({ access_token: "session_token", token_type: "bearer" }));
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return Promise.resolve(
          jsonResponse({
            items: [{ id: "dev_tools", label: "Developer Tools", path: "/dev-tools", status: "PLANNED" }],
            total: 1,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(
          jsonResponse({
            module_id: "home",
            title: "Project Cockpit",
            status: "ready",
            description: "Project-level operational overview.",
            active_context: {},
            setup_status: null,
            counts: { recent_jobs: 0, recent_artifacts: 0, recent_evidence: 0 },
            module_summary: { total: 1, counts_by_status: { PLANNED: 1 }, items: [] },
            recent_jobs: [],
            recent_artifacts: [],
            recent_evidence: [],
            available_actions: []
          })
        );
      }
      if (url.endsWith("/api/v1/platform/dev-tools/data-dictionary/tables/RATE_GEO_COST")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            module_id: "dev_tools",
            tool_key: "data_dictionary",
            title: "Data Dictionary Table Detail",
            status: "ready",
            source_contract: "/api/v1/catalog/tables/{table_name}",
            active_context: {},
            table: {
              table_name: "RATE_GEO_COST",
              schema_name: "GLOGOWNER",
              description: "Synthetic rate cost detail.",
              column_count: 134,
              data_category: "RATES_SETUP",
              is_transactional: false,
              allow_cutover: true,
              allow_csvutil: true,
              exists: true
            },
            columns: [
              {
                column_name: "RATE_GEO_COST_GROUP_GID",
                data_type: "VARCHAR2",
                nullable: false,
                max_length: 101,
                ordinal_position: 1
              },
              {
                column_name: "COST",
                data_type: "NUMBER",
                nullable: true,
                max_length: null,
                ordinal_position: 2
              }
            ],
            column_total: 2
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/dev-tools/data-dictionary/tables/RATE_GEO_COST");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "RATE_GEO_COST" })).toBeInTheDocument();
    expect(screen.getByText("Data Dictionary Table Detail")).toBeInTheDocument();
    expect(await screen.findByText("RATE_GEO_COST_GROUP_GID")).toBeInTheDocument();
    expect(screen.getByText("VARCHAR2")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Data Dictionary" })).toHaveAttribute(
      "href",
      "/dev-tools/data-dictionary?query=RATE_GEO_COST"
    );
  });

  it("renders Developer Tools FK Catalog as a dedicated technical explorer", async () => {
    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(jsonResponse({ access_token: "session_token", token_type: "bearer" }));
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return Promise.resolve(
          jsonResponse({
            items: [{ id: "dev_tools", label: "Developer Tools", path: "/dev-tools", status: "PLANNED" }],
            total: 1,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(
          jsonResponse({
            module_id: "home",
            title: "Project Cockpit",
            status: "ready",
            description: "Project-level operational overview.",
            active_context: {},
            setup_status: null,
            counts: { recent_jobs: 0, recent_artifacts: 0, recent_evidence: 0 },
            module_summary: { total: 1, counts_by_status: { PLANNED: 1 }, items: [] },
            recent_jobs: [],
            recent_artifacts: [],
            recent_evidence: [],
            available_actions: []
          })
        );
      }
      if (url.endsWith("/api/v1/platform/dev-tools/fk-catalog?source_table=RATE_GEO_COST&limit=50")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            module_id: "dev_tools",
            tool_key: "fk_catalog",
            title: "FK Catalog Explorer",
            status: "ready",
            description: "Read-only foreign-key relationships from the backend Data Dictionary.",
            source_table: "RATE_GEO_COST",
            limit: 50,
            total: 2,
            source_contract: "/api/v1/catalog/tables/RATE_GEO_COST",
            active_context: {},
            items: [
              {
                source_table_name: "RATE_GEO_COST",
                column_name: "RATE_GEO_COST_GROUP_GID",
                parent_table_name: "RATE_GEO_COST_GROUP",
                parent_column_name: "RATE_GEO_COST_GROUP_GID",
                relationship_type: "FOREIGN_KEY",
                parent_table_href: "/dev-tools/data-dictionary/tables/RATE_GEO_COST_GROUP"
              },
              {
                source_table_name: "RATE_GEO_COST",
                column_name: "RATE_GEO_COST_OPERAND_SEQ",
                parent_table_name: "RATE_GEO_COST_OPERAND",
                parent_column_name: "RATE_GEO_COST_OPERAND_SEQ",
                relationship_type: "FOREIGN_KEY",
                parent_table_href: "/dev-tools/data-dictionary/tables/RATE_GEO_COST_OPERAND"
              }
            ]
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/dev-tools/fk-catalog?source_table=RATE_GEO_COST");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "FK Catalog Explorer" })).toBeInTheDocument();
    expect(await screen.findAllByText("RATE_GEO_COST_GROUP_GID")).toHaveLength(2);
    expect(screen.getAllByText("RATE_GEO_COST_GROUP").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "Open parent table RATE_GEO_COST_GROUP" })).toHaveAttribute(
      "href",
      "/dev-tools/data-dictionary/tables/RATE_GEO_COST_GROUP"
    );
    expect(screen.getByRole("link", { name: "Back to Developer Tools" })).toHaveAttribute("href", "/dev-tools");
    expect(screen.queryByText("Primary list or work queue")).not.toBeInTheDocument();
  });

  it("renders Developer Tools Schema Pack Diagnostics as a dedicated technical explorer", async () => {
    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(jsonResponse({ access_token: "session_token", token_type: "bearer" }));
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return Promise.resolve(
          jsonResponse({
            items: [{ id: "dev_tools", label: "Developer Tools", path: "/dev-tools", status: "PLANNED" }],
            total: 1,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(
          jsonResponse({
            module_id: "home",
            title: "Project Cockpit",
            status: "ready",
            description: "Project-level operational overview.",
            active_context: {},
            setup_status: null,
            counts: { recent_jobs: 0, recent_artifacts: 0, recent_evidence: 0 },
            module_summary: { total: 1, counts_by_status: { PLANNED: 1 }, items: [] },
            recent_jobs: [],
            recent_artifacts: [],
            recent_evidence: [],
            available_actions: []
          })
        );
      }
      if (url.endsWith("/api/v1/platform/dev-tools/schema-packs?otm_version=26A&limit=25")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            module_id: "dev_tools",
            tool_key: "schema_packs",
            title: "Schema Pack Diagnostics",
            status: "ready",
            description: "Read-only WSDL/XSD schema-pack diagnostics from Catalog Core.",
            otm_version: "26A",
            code: "",
            filter_status: "",
            limit: 25,
            total: 1,
            source_contract: "/api/v1/catalog/schema-packs",
            root_contract: "/api/v1/catalog/schema-roots",
            active_context: {},
            items: [
              {
                id: "pack_1",
                code: "OTM26A",
                name: "Synthetic OTM 26A",
                otm_version: "26A",
                source_type: "LOCAL_FOLDER",
                asset_id: null,
                status: "INDEXED",
                namespace_count: 2,
                root_count: 1,
                operation_count: 0,
                content_hash: "synthetic-hash",
                created_by: "synthetic.user@example.test",
                created_at: null,
                updated_at: null,
                root_total: 1,
                root_preview: [
                  {
                    id: "root_1",
                    schema_pack_id: "pack_1",
                    schema_file_id: "file_1",
                    root_name: "Transmission",
                    root_display_label: "Transmission",
                    canonical_root_name: "Transmission",
                    schema_root_aliases: ["Transmission"],
                    data_dictionary_family: "",
                    schema_guidance_role: "ENVELOPE_ONLY",
                    namespace: "http://xmlns.oracle.com/apps/otm/transmission",
                    domain_area: "INTEGRATION",
                    root_type: "ENVELOPE",
                    envelope_role: "TRANSMISSION",
                    recommended_modules: ["integration_mapping", "order_release_generator"],
                    documentation: "Synthetic transmission envelope."
                  }
                ]
              }
            ]
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/dev-tools/schema-packs?otm_version=26A");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Schema Pack Diagnostics" })).toBeInTheDocument();
    expect(await screen.findByText("Synthetic OTM 26A")).toBeInTheDocument();
    expect(screen.getByText("Transmission")).toBeInTheDocument();
    expect(screen.getByText("ENVELOPE_ONLY")).toBeInTheDocument();
    expect(screen.getByText("Source contract: /api/v1/catalog/schema-packs")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Developer Tools" })).toHaveAttribute("href", "/dev-tools");
    expect(screen.queryByText("Primary list or work queue")).not.toBeInTheDocument();
  });

  it("renders Developer Tools Environment Readiness as a dedicated technical explorer", async () => {
    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(jsonResponse({ access_token: "session_token", token_type: "bearer" }));
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return Promise.resolve(
          jsonResponse({
            items: [{ id: "dev_tools", label: "Developer Tools", path: "/dev-tools", status: "PLANNED" }],
            total: 1,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(
          jsonResponse({
            module_id: "home",
            title: "Project Cockpit",
            status: "ready",
            description: "Project-level operational overview.",
            active_context: {},
            setup_status: null,
            counts: { recent_jobs: 0, recent_artifacts: 0, recent_evidence: 0 },
            module_summary: { total: 1, counts_by_status: { PLANNED: 1 }, items: [] },
            recent_jobs: [],
            recent_artifacts: [],
            recent_evidence: [],
            available_actions: []
          })
        );
      }
      if (url.endsWith("/api/v1/platform/dev-tools/environment-readiness")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            module_id: "dev_tools",
            tool_key: "environment_readiness",
            title: "Environment Readiness",
            status: "ready",
            description: "Read-only environment readiness checks for the active implementation context.",
            active_context: {
              user_id: "user_1",
              project_id: "project_1",
              profile_id: "profile_1",
              environment_id: "environment_1",
              domain_name: "OTM1",
              allowed_domains: ["PUBLIC", "OTM1"],
              can_view_all_domains: false
            },
            active_environment_id: "environment_1",
            counts: { environments: 1, ready_checks: 4, blocked_checks: 0 },
            environments: [
              {
                id: "environment_1",
                name: "DEV",
                environment_type: "DEV",
                status: "ACTIVE",
                is_active: true
              }
            ],
            checks: [
              { key: "active_project", label: "Active project", status: "READY", message: "Project context is selected." },
              { key: "active_profile", label: "Active profile", status: "READY", message: "Profile context is selected." },
              {
                key: "active_environment",
                label: "Active environment",
                status: "READY",
                message: "Environment context is selected."
              },
              { key: "domain_scope", label: "Domain scope", status: "READY", message: "Domain scope is set." }
            ],
            source_contract: "/api/v1/platform/active-context"
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/dev-tools/environment-readiness");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Environment Readiness" })).toBeInTheDocument();
    expect(await screen.findByText("DEV")).toBeInTheDocument();
    expect(screen.getByText("Active environment")).toBeInTheDocument();
    expect(screen.getByText("Domain scope")).toBeInTheDocument();
    expect(screen.getByText("Source contract: /api/v1/platform/active-context")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Developer Tools" })).toHaveAttribute("href", "/dev-tools");
    expect(screen.queryByText("Primary list or work queue")).not.toBeInTheDocument();
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

  it("stores system theme preference through the backend contract", async () => {
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
          theme_mode: "system",
          follow_system_theme: true,
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

    const view = renderApp();
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Project Cockpit" });
    await userEvent.click(screen.getByRole("button", { name: "Follow system theme" }));

    await waitFor(() => expect(view.container.querySelector(".app-shell")).toHaveAttribute("data-theme", "system"));
    expect(screen.getByRole("button", { name: "Follow system theme" })).toHaveAttribute("aria-pressed", "true");
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
    expect(
      await within(await screen.findByLabelText("Selected batch tables")).findByText("ACCESSORIAL_COST")
    ).toBeInTheDocument();
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
    await waitFor(() => expect(screen.getAllByText("rates_csv_zip").length).toBeGreaterThan(0));
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
    await waitFor(() => expect(screen.getAllByText("RATE_RECORD").length).toBeGreaterThan(0));
    expect(screen.getAllByText("Rate Record").length).toBeGreaterThan(0);
    expect(screen.queryByText("RATE_GEO")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Validate table" })).toBeInTheDocument();
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

    renderApp("/master-data/factory");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Data Factory" });
    await waitFor(() => expect(screen.getAllByText("REGION_TEMPLATE").length).toBeGreaterThan(0));
    expect(screen.getAllByText("REGION").length).toBeGreaterThan(0);
    expect(screen.getByText("Region GID")).toBeInTheDocument();
    expect(screen.queryByText(/build workbook/i)).not.toBeInTheDocument();
  });

  it("renders a route-level Master Data template detail with a Back action", async () => {
    const template = {
      id: "template_region",
      code: "REGION_TEMPLATE",
      name: "Region Template",
      catalog_macro_object_code: "REGION",
      data_category: "MASTER_DATA",
      version: 1,
      status: "PUBLISHED",
      target_tables: ["REGION"],
      available_actions: [
        {
          disabled: false,
          disabled_reason: null,
          href: "",
          icon_key: "file-spreadsheet",
          key: "build_workbook",
          label: "Build workbook",
          method: "POST",
          recommended: true,
          requires_confirmation: false,
          result_hint: "refresh_object",
          variant: "secondary"
        }
      ],
      sheets: [
        {
          code: "REGIONS",
          name: "Regions",
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
        return Promise.resolve(jsonResponse({ access_token: "session_token", token_type: "bearer" }));
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            items: [
              { id: "home", label: "Project Cockpit", path: "/home", status: "ACTIVE" },
              { id: "master_data", label: "Data Factory", path: "/master-data", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates")) {
        return Promise.resolve(jsonResponse({ items: [template], page: 1, page_size: 50, total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/REGION_TEMPLATE")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(template));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/master-data/factory/templates/REGION_TEMPLATE");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "REGION_TEMPLATE" });
    expect(screen.getByRole("link", { name: "Back to Data Factory" })).toHaveAttribute("href", "/master-data/factory");
    expect(screen.getByLabelText("Template operational summary")).toHaveTextContent("REGION");
    expect(screen.getByLabelText("Template operational summary")).toHaveTextContent("Region GID");
    expect(screen.queryByLabelText("Selected Master Data template")).not.toBeInTheDocument();
  });

  it("renders a route-level Master Data batch workspace with backend action blockers", async () => {
    const template = {
      id: "template_region",
      code: "REGION_TEMPLATE",
      name: "Region Template",
      catalog_macro_object_code: "REGION",
      data_category: "MASTER_DATA",
      version: 1,
      status: "PUBLISHED",
      target_tables: ["REGION"],
      available_actions: [],
      sheets: [
        {
          code: "REGIONS",
          name: "Regions",
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
    const batch = {
      batch_id: "batch_ready",
      template_code: "REGION_TEMPLATE",
      status: "PARSED",
      file_name: "regions_ready.xlsx",
      issue_count: 0,
      row_count: 2,
      sheet_count: 1,
      csv_file_count: 0,
      sheet_summaries: [{ row_count: 2, sheet_code: "REGIONS", target_table: "REGION" }],
      available_actions: [
        {
          disabled: false,
          disabled_reason: null,
          href: "",
          icon_key: "check-circle",
          key: "validate_relationships",
          label: "Validate relationships",
          method: "POST",
          recommended: true,
          requires_confirmation: false,
          result_hint: "refresh_object",
          variant: "primary"
        },
        {
          disabled: true,
          disabled_reason: "Run relationship validation before mapping records.",
          href: "",
          icon_key: "git-branch",
          key: "map_records",
          label: "Map records",
          method: "POST",
          recommended: false,
          requires_confirmation: false,
          result_hint: "refresh_object",
          variant: "secondary"
        },
        {
          disabled: true,
          disabled_reason: "Build output before exporting a CSV package.",
          href: "",
          icon_key: "package",
          key: "export_csv_package",
          label: "Export package",
          method: "POST",
          recommended: false,
          requires_confirmation: false,
          result_hint: "refresh_object",
          variant: "secondary"
        }
      ],
      summary: { source: "workbook-editor" }
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
              { id: "master_data", label: "Data Factory", path: "/master-data", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates")) {
        return Promise.resolve(jsonResponse({ items: [template], page: 1, page_size: 50, total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/REGION_TEMPLATE")) {
        return Promise.resolve(jsonResponse(template));
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_ready")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(batch));
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_ready/artifacts")) {
        return Promise.resolve(jsonResponse({ items: [], page: 1, page_size: 50, total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_ready/output-records")) {
        return Promise.resolve(jsonResponse({ items: [], page: 1, page_size: 50, total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_ready/csv-files")) {
        return Promise.resolve(jsonResponse({ items: [], page: 1, page_size: 50, total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/batches")) {
        return Promise.resolve(jsonResponse({ items: [batch], page: 1, page_size: 50, total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/summary")) {
        return Promise.resolve(
          jsonResponse({
            latest_batch_id: "batch_ready",
            status_breakdown: [],
            template_breakdown: [],
            total_batches: 1,
            total_issues: 0,
            total_rows: 2
          })
        );
      }
      if (
        url.endsWith("/api/v1/modules/master-data/scenario-packs") ||
        url.endsWith("/api/v1/modules/master-data/coordinate-quality/batches") ||
        url.endsWith("/api/v1/catalog/macro-objects")
      ) {
        return Promise.resolve(jsonResponse({ items: [], page: 1, page_size: 50, total: 0 }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/master-data/factory/batches/batch_ready");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "batch_ready" });
    expect(screen.getByRole("link", { name: "Back to template" })).toHaveAttribute(
      "href",
      "/master-data/factory/templates/REGION_TEMPLATE"
    );
    expect(screen.getByLabelText("Master Data batch execution workspace")).toHaveTextContent("regions_ready.xlsx");
    expect(screen.getByLabelText("Batch execution steps")).toHaveTextContent("CSV Package");
    await userEvent.click(screen.getByRole("button", { name: /3Output/ }));
    expect(screen.getByRole("button", { name: "Map records" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Map records" })).toHaveAttribute(
      "title",
      "Run relationship validation before mapping records."
    );
    expect(screen.queryByLabelText("Selected Master Data template")).not.toBeInTheDocument();
  });

  it("renders Template Builder search and route-level template actions", async () => {
    const templates = [
      {
        id: "template_region",
        code: "REGION_TEMPLATE",
        name: "Region Template",
        catalog_macro_object_code: "REGION",
        data_category: "MASTER_DATA",
        version: 1,
        status: "PUBLISHED",
        target_tables: ["REGION"],
        available_actions: [],
        sheets: [],
        description: "Synthetic region template.",
        created_at: "2026-05-21T01:00:00",
        updated_at: "2026-05-21T01:00:00"
      },
      {
        id: "template_item",
        code: "ITEM_TEMPLATE",
        name: "Item Template",
        catalog_macro_object_code: "ITEM",
        data_category: "MASTER_DATA",
        version: 1,
        status: "DRAFT",
        target_tables: ["ITEM"],
        available_actions: [],
        sheets: [],
        description: "Synthetic item template.",
        created_at: "2026-05-21T01:00:00",
        updated_at: "2026-05-21T01:00:00"
      }
    ];
    const templateResponse = {
      items: templates,
      normalized_filters: [],
      page: 1,
      page_size: 50,
      search_metadata: {
        fields: [
          { key: "template_code", label: "Template code" },
          { key: "template_name", label: "Template name" },
          { key: "macro_object", label: "Macro object" },
          { key: "status", label: "Status" }
        ],
        operators: ["begins_with", "contains", "one_of", "not_one_of"]
      },
      total: 2
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
              { id: "master_data", label: "Data Factory", path: "/master-data", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.includes("/api/v1/modules/master-data/templates?")) {
        expect(url).toContain("template_code=REG");
        expect(url).toContain("template_code_operator=begins_with");
        return Promise.resolve(
          jsonResponse({
            ...templateResponse,
            items: [templates[0]],
            normalized_filters: [{ field: "template_code", operator: "begins_with", value: "REG" }],
            total: 1
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/templates")) {
        return Promise.resolve(jsonResponse(templateResponse));
      }
      if (url.endsWith("/api/v1/modules/master-data/scenario-packs")) {
        return Promise.resolve(jsonResponse({ items: [], page: 1, page_size: 50, total: 0 }));
      }
      if (url.endsWith("/api/v1/catalog/macro-objects")) {
        return Promise.resolve(jsonResponse({ items: [], page: 1, page_size: 50, total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/summary")) {
        return Promise.resolve(
          jsonResponse({
            latest_batch_id: null,
            status_breakdown: [],
            template_breakdown: [],
            total_batches: 0,
            total_issues: 0,
            total_rows: 0
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/batches")) {
        return Promise.resolve(jsonResponse({ items: [], page: 1, page_size: 50, total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/coordinate-quality/batches")) {
        return Promise.resolve(jsonResponse({ items: [], page: 1, page_size: 50, total: 0 }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/master-data/template-builder");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Template Builder" });
    expect(screen.getByRole("link", { name: "Create template" })).toHaveAttribute("href", "/master-data/template-builder/new");
    await userEvent.selectOptions(screen.getByLabelText("Template code operator"), "begins_with");
    await userEvent.type(screen.getByLabelText("Template code filter"), "REG");
    await userEvent.click(screen.getByRole("button", { name: "Apply template search" }));

    expect(await screen.findByText("template_code begins_with REG")).toBeInTheDocument();
    expect(screen.getByLabelText("Template Builder templates")).toHaveTextContent("REGION_TEMPLATE");
    expect(screen.getByRole("link", { name: "View REGION_TEMPLATE" })).toHaveAttribute(
      "href",
      "/master-data/template-builder/REGION_TEMPLATE"
    );
    expect(screen.getByRole("link", { name: "Edit REGION_TEMPLATE" })).toHaveAttribute(
      "href",
      "/master-data/template-builder/REGION_TEMPLATE/edit"
    );
    expect(screen.getByRole("link", { name: "Copy REGION_TEMPLATE" })).toHaveAttribute(
      "href",
      "/master-data/template-builder/REGION_TEMPLATE/copy"
    );
    expect(screen.getByRole("link", { name: "Retire REGION_TEMPLATE" })).toHaveAttribute(
      "href",
      "/master-data/template-builder/REGION_TEMPLATE/delete"
    );
    expect(screen.queryByLabelText("Selected Master Data template")).not.toBeInTheDocument();
  });

  it("renders focused Template Builder create and edit routes without the legacy workflow", async () => {
    const draftTemplate = {
      id: "template_edit",
      code: "EDIT_TEMPLATE",
      name: "Editable Template",
      catalog_macro_object_code: "LOCATION",
      data_category: "MASTER_DATA",
      version: 1,
      status: "DRAFT",
      target_tables: ["LOCATION", "LOCATION_ADDRESS"],
      available_actions: [
        {
          disabled: false,
          disabled_reason: null,
          href: "",
          icon_key: "check-circle",
          key: "validate_definition",
          label: "Validate definition",
          method: "POST",
          recommended: true,
          requires_confirmation: false,
          result_hint: "refresh_object",
          variant: "secondary"
        },
        {
          disabled: false,
          disabled_reason: null,
          href: "",
          icon_key: "upload-cloud",
          key: "publish_template",
          label: "Publish template",
          method: "POST",
          recommended: false,
          requires_confirmation: false,
          result_hint: "refresh_object",
          variant: "secondary"
        }
      ],
      sheets: [
        {
          code: "LOCATIONS",
          name: "Locations",
          target_table: "LOCATION",
          fields: [
            {
              name: "location_gid",
              label: "Location GID",
              target_column: "LOCATION_GID",
              required: true
            }
          ]
        }
      ],
      definition: {
        schema_version: "master-data-template-definition/v2",
        template: {
          code: "EDIT_TEMPLATE",
          name: "Editable Template",
          version: 1,
          status: "DRAFT",
          catalog_macro_object_code: "LOCATION",
          data_category: "MASTER_DATA"
        },
        target_tables: [
          { required: true, sequence: 10, table_name: "LOCATION" },
          { required: false, sequence: 20, table_name: "LOCATION_ADDRESS" }
        ],
        sheets: [{ code: "LOCATIONS", field_keys: ["location_gid"], name: "Locations", sequence: 10 }],
        fields: [
          {
            data_type: "string",
            field_key: "location_gid",
            label: "Location GID",
            required: true,
            sheet_code: "LOCATIONS"
          }
        ],
        mappings: [
          {
            mapping_key: "location_gid_to_location_gid",
            required: true,
            source_field_key: "location_gid",
            source_type: "USER_FIELD",
            target_column: "LOCATION_GID",
            target_table: "LOCATION"
          }
        ],
        relationship_rules: [],
        documentation_refs: [{ note: "Synthetic dictionary basis.", scope: "LOCATION", source_type: "DATA_DICTIONARY" }]
      },
      description: "Synthetic editable template.",
      created_at: "2026-05-21T01:00:00",
      updated_at: "2026-05-21T01:00:00"
    };
    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(jsonResponse({ access_token: "session_token", token_type: "bearer" }));
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return Promise.resolve(
          jsonResponse({
            items: [
              { id: "home", label: "Project Cockpit", path: "/home", status: "ACTIVE" },
              { id: "master_data", label: "Data Factory", path: "/master-data", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates")) {
        return Promise.resolve(jsonResponse({ items: [draftTemplate], page: 1, page_size: 50, total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/EDIT_TEMPLATE")) {
        return Promise.resolve(jsonResponse(draftTemplate));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/EDIT_TEMPLATE/draft")) {
        expect(init?.method).toBe("PATCH");
        const body = JSON.parse(String(init?.body));
        expect(body.code).toBe("EDIT_TEMPLATE");
        expect(body.target_tables.map((table: { table_name: string }) => table.table_name)).toEqual([
          "LOCATION",
          "LOCATION_ADDRESS"
        ]);
        return Promise.resolve(jsonResponse(draftTemplate));
      }
      if (url.endsWith("/api/v1/modules/master-data/scenario-packs")) {
        return Promise.resolve(jsonResponse({ items: [], page: 1, page_size: 50, total: 0 }));
      }
      if (
        url.endsWith("/api/v1/catalog/macro-objects") ||
        url.endsWith("/api/v1/modules/master-data/batches") ||
        url.endsWith("/api/v1/modules/master-data/batches/summary") ||
        url.endsWith("/api/v1/modules/master-data/coordinate-quality/batches")
      ) {
        return Promise.resolve(jsonResponse({ items: [], page: 1, page_size: 50, total: 0 }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/master-data/template-builder/new");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "New template" });
    expect(screen.getByLabelText("Template Builder new template workspace")).toHaveTextContent("Template basics");
    expect(screen.queryByLabelText("Data Factory workflow")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Selected Master Data template")).not.toBeInTheDocument();

    renderApp("/master-data/template-builder/EDIT_TEMPLATE/edit");
    await screen.findByRole("heading", { name: "EDIT_TEMPLATE" });
    expect(screen.getByRole("link", { name: "Back to Template Detail" })).toHaveAttribute(
      "href",
      "/master-data/template-builder/EDIT_TEMPLATE"
    );
    expect(screen.getByLabelText("Template Builder target table editor")).toHaveTextContent("LOCATION_ADDRESS");
    expect(screen.getByLabelText("Template Builder field editor")).toHaveTextContent("LOCATION_GID");
    expect(screen.queryByLabelText("Data Factory workflow")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Selected Master Data template")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Save draft" }));
    await screen.findByText("Draft EDIT_TEMPLATE saved.");
  });

  it("creates a Template Builder copy from a dedicated route and opens the copied draft for editing", async () => {
    const sourceTemplate = {
      id: "template_copy_source",
      code: "COPY_SOURCE",
      name: "Copy Source Template",
      catalog_macro_object_code: "LOCATION",
      data_category: "MASTER_DATA",
      version: 1,
      status: "PUBLISHED",
      target_tables: ["LOCATION", "LOCATION_ADDRESS"],
      available_actions: [
        {
          disabled: false,
          disabled_reason: null,
          href: "",
          icon_key: "copy",
          key: "create_version",
          label: "Create next version",
          method: "POST",
          recommended: false,
          requires_confirmation: false,
          result_hint: "refresh_object",
          variant: "secondary"
        }
      ],
      sheets: [],
      definition: {
        schema_version: "master-data-template-definition/v2",
        template: {
          code: "COPY_SOURCE",
          name: "Copy Source Template",
          version: 1,
          status: "PUBLISHED",
          catalog_macro_object_code: "LOCATION",
          data_category: "MASTER_DATA"
        },
        target_tables: [
          { required: true, sequence: 10, table_name: "LOCATION" },
          { required: false, sequence: 20, table_name: "LOCATION_ADDRESS" }
        ],
        sheets: [{ code: "LOCATIONS", field_keys: ["location_gid"], name: "Locations", sequence: 10 }],
        fields: [
          {
            data_type: "string",
            field_key: "location_gid",
            label: "Location GID",
            required: true,
            sheet_code: "LOCATIONS"
          }
        ],
        mappings: [
          {
            mapping_key: "location_gid_to_location_gid",
            required: true,
            source_field_key: "location_gid",
            source_type: "USER_FIELD",
            target_column: "LOCATION_GID",
            target_table: "LOCATION"
          }
        ],
        relationship_rules: [
          {
            rule_key: "location_address_parent",
            severity: "ERROR"
          }
        ],
        documentation_refs: [{ note: "Synthetic dictionary basis.", scope: "LOCATION", source_type: "DATA_DICTIONARY" }]
      },
      description: "Synthetic template to copy.",
      created_at: "2026-05-21T01:00:00",
      updated_at: "2026-05-21T01:00:00"
    };
    const copiedTemplate = {
      ...sourceTemplate,
      id: "template_copy_created",
      code: "COPY_SOURCE_CUSTOM",
      name: "Copy Source Template",
      version: 2,
      status: "DRAFT",
      definition: {
        ...sourceTemplate.definition,
        template: {
          ...sourceTemplate.definition.template,
          code: "COPY_SOURCE_CUSTOM",
          status: "DRAFT",
          version: 2
        }
      }
    };
    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(jsonResponse({ access_token: "session_token", token_type: "bearer" }));
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return Promise.resolve(
          jsonResponse({
            items: [{ id: "master_data", label: "Data Factory", path: "/master-data", status: "ACTIVE" }],
            page: 1,
            page_size: 50,
            total: 1
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates")) {
        return Promise.resolve(jsonResponse({ items: [sourceTemplate, copiedTemplate], page: 1, page_size: 50, total: 2 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/COPY_SOURCE")) {
        return Promise.resolve(jsonResponse(sourceTemplate));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/COPY_SOURCE_CUSTOM")) {
        return Promise.resolve(jsonResponse(copiedTemplate));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/COPY_SOURCE/versions")) {
        expect(init?.method).toBe("POST");
        expect(JSON.parse(String(init?.body))).toEqual({ new_code: "COPY_SOURCE_CUSTOM" });
        return Promise.resolve(jsonResponse(copiedTemplate));
      }
      if (url.endsWith("/api/v1/modules/master-data/scenario-packs")) {
        return Promise.resolve(jsonResponse({ items: [], page: 1, page_size: 50, total: 0 }));
      }
      if (
        url.endsWith("/api/v1/catalog/macro-objects") ||
        url.endsWith("/api/v1/modules/master-data/batches") ||
        url.endsWith("/api/v1/modules/master-data/batches/summary") ||
        url.endsWith("/api/v1/modules/master-data/coordinate-quality/batches")
      ) {
        return Promise.resolve(jsonResponse({ items: [], page: 1, page_size: 50, total: 0 }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/master-data/template-builder/COPY_SOURCE/copy");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "COPY_SOURCE" });
    expect(screen.getByLabelText("Template Builder copy route")).toHaveTextContent("New template header");
    expect(screen.getByLabelText("Copy tables")).toBeChecked();
    expect(screen.getByLabelText("Copy fields")).toBeChecked();
    expect(screen.getByLabelText("Copy relationship rules")).toBeChecked();
    expect(screen.getByLabelText("Template copy scope preview")).toHaveTextContent("2 target table(s)");

    await userEvent.clear(screen.getByLabelText("New template code"));
    await userEvent.type(screen.getByLabelText("New template code"), "copy_source_custom");
    await userEvent.click(screen.getByRole("button", { name: "Create copy" }));

    await screen.findByText("Copy COPY_SOURCE_CUSTOM created.");
    expect(await screen.findByRole("heading", { name: "COPY_SOURCE_CUSTOM" })).toBeInTheDocument();
    expect(screen.getByLabelText("Template Builder edit route")).toHaveTextContent("Header and definition controls");
  });

  it("renders Master Data as a focused hub before entering factory workflows", async () => {
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
              { id: "master_data", label: "Data Factory", path: "/master-data", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse({ items: [], page: 1, page_size: 50, total: 0 }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/master-data");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Master Data" });
    expect(screen.getByRole("link", { name: /Open Data Factory/i })).toHaveAttribute("href", "/master-data/factory");
    expect(screen.getByRole("link", { name: /Open Template Builder/i })).toHaveAttribute(
      "href",
      "/master-data/template-builder"
    );
    expect(screen.getByRole("link", { name: /Open Quality Tools/i })).toHaveAttribute("href", "/master-data/quality");
    expect(screen.queryByLabelText("Data Factory workflow")).not.toBeInTheDocument();
  });

  it("renders Order Release Generator from backend template contracts", async () => {
    const template = {
      id: "or_template_1",
      code: "TL_ORDER_RELEASE_MVP0",
      name: "Synthetic TL Order Release",
      version: 1,
      status: "ACTIVE",
      macro_object_code: "ORDER_RELEASE",
      description: "Synthetic template for TL order release XML generation.",
      required_columns: ["release_gid", "source_location_gid", "dest_location_gid"],
      optional_columns: ["equipment_group_gid", "ship_unit_count"],
      defaults: {
        transport_mode_gid: "TL",
        service_provider_gid: "SYNTHETIC_CARRIER"
      },
      created_by: "system",
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
                {
                  id: "order_release_generator",
                  label: "Order Release Generator",
                  path: "/order-release-generator",
                  status: "ACTIVE"
                }
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
      if (url.endsWith("/api/v1/modules/order-release-generator/templates")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(JSON.stringify({ items: [template], total: 1, page: 1, page_size: 50 }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/order-release-generator");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Order Release Generator" });
    expect(screen.getAllByText("TL_ORDER_RELEASE_MVP0").length).toBeGreaterThan(0);
    expect(screen.getByText("release_gid")).toBeInTheDocument();
    expect(screen.getByText("equipment_group_gid")).toBeInTheDocument();
    expect(screen.getByText("transport_mode_gid")).toBeInTheDocument();
    expect(screen.queryByText(/submit otm/i)).not.toBeInTheDocument();
  });

  it("renders Integration Mapping Studio from backend definition and mapping contracts", async () => {
    const definition = {
      id: "definition_1",
      code: "INT_SYNTHETIC_TRIP",
      name: "Synthetic Trip Mapping",
      description: "Synthetic mapping definition for GUI contract tests.",
      source_system: "OTM",
      target_system: "NDD",
      source_format: "XML",
      target_format: "JSON",
      status: "DRAFT",
      created_by: "synthetic.user@example.test",
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
                {
                  id: "integration_mapping",
                  label: "Integration Mapping Studio",
                  path: "/integration-mapping",
                  status: "ACTIVE"
                }
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
      if (url.endsWith("/api/v1/modules/integration-mapping/transform-types")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "transform_1",
                  code: "DIRECT",
                  name: "Direct",
                  description: "Direct assignment.",
                  requires_expression: false,
                  status: "ACTIVE",
                  sequence_index: 1,
                  system_seeded: true,
                  created_at: "2026-05-21T01:00:00",
                  updated_at: "2026-05-21T01:00:00"
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
      if (url.endsWith("/api/v1/modules/integration-mapping/systems")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(JSON.stringify({ items: [], total: 0, page: 1, page_size: 50 }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(JSON.stringify({ items: [definition], total: 1, page: 1, page_size: 50 }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(JSON.stringify(definition), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          })
        );
      }
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/payload-artifacts")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "payload_1",
                  definition_id: "definition_1",
                  artifact_id: "artifact_1",
                  payload_role: "SOURCE_SAMPLE",
                  payload_format: "XML",
                  file_name: "planned_shipment.xml",
                  description: "Synthetic source payload.",
                  content_type: "application/xml",
                  sha256: "abc123",
                  size_bytes: 3210,
                  created_by: "synthetic.user@example.test",
                  created_at: "2026-05-21T01:00:00",
                  updated_at: "2026-05-21T01:00:00"
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
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/schema-documents")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "schema_1",
                  definition_id: "definition_1",
                  payload_artifact_id: "payload_1",
                  payload_format: "XML",
                  root_name: "PlannedShipment",
                  node_count: 12,
                  status: "PARSED",
                  created_by: "synthetic.user@example.test",
                  created_at: "2026-05-21T01:00:00",
                  updated_at: "2026-05-21T01:00:00"
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
      if (url.endsWith("/api/v1/modules/integration-mapping/definitions/definition_1/mappings")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "mapping_1",
                  definition_id: "definition_1",
                  source_schema_document_id: "schema_1",
                  target_schema_document_id: "schema_2",
                  source_path: "/Shipment/Id",
                  target_path: "$.numeroViagem",
                  transform_type: "DIRECT",
                  description: "Synthetic direct mapping.",
                  sequence_index: 1,
                  status: "ACTIVE",
                  created_by: "synthetic.user@example.test",
                  created_at: "2026-05-21T01:00:00",
                  updated_at: "2026-05-21T01:00:00"
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

    renderApp("/integration-mapping");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Integration Mapping Studio" });
    expect(await screen.findByText("INT_SYNTHETIC_TRIP")).toBeInTheDocument();
    expect(screen.getByText("planned_shipment.xml")).toBeInTheDocument();
    expect(screen.getByText("PlannedShipment")).toBeInTheDocument();
    expect(screen.getByText("$.numeroViagem")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Generate spec" })).toBeInTheDocument();
  });
});
