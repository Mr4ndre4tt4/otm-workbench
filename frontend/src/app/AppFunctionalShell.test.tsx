import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "../platform/auth";

function renderFunctionalApp(initialPath = "/") {
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

function cockpitSummary(contextReady: boolean) {
  const activeContext = contextReady
    ? {
        project_id: "project_1",
        profile_id: "profile_1",
        environment_id: "environment_1",
        domain_name: "OTM1",
        allowed_domains: ["PUBLIC", "OTM1"],
        can_view_all_domains: false
      }
    : {
        project_id: null,
        profile_id: null,
        environment_id: null,
        domain_name: null,
        allowed_domains: ["PUBLIC"],
        can_view_all_domains: false
      };
  return {
    module_id: "home",
    title: "Project Cockpit",
    status: contextReady ? "ready" : "needs_context",
    description: "Project context, project information, and module accelerators.",
    active_context: activeContext,
    setup_status: {
      status: contextReady ? "READY" : "NEEDS_CONTEXT",
      profile_count: 1,
      environment_count: 1,
      active_context_selected: contextReady,
      missing_requirements: contextReady ? [] : ["active_context"]
    },
    counts: { recent_jobs: 0, recent_artifacts: 0, recent_evidence: 0 },
    context_selector: {
      mode: contextReady ? "PRIVATE" : "PUBLIC",
      active_context: activeContext,
      public_view_available: true,
      requires_private_context: false,
      set_context_action_key: "set_active_context"
    },
    project_info: {
      title: "Project information",
      status: contextReady ? "AVAILABLE" : "NEEDS_CONTEXT",
      links: [],
      documents: [],
      contacts: [],
      secure_vault: {
        status: "NOT_CONFIGURED",
        metadata_only: true,
        secret_values_available: false
      }
    },
    accelerators: [
      {
        key: "rates",
        label: "Rates Studio",
        description: "Synthetic Rates functional shell target.",
        href: "/rates",
        status: "ACTIVE",
        icon_key: "rates",
        requires_private_context: true,
        disabled: !contextReady,
        disabled_reason: contextReady ? null : "ACTIVE_CONTEXT_REQUIRED"
      }
    ],
    user_scope: {
      role_mode: "SCOPED",
      is_dba: false,
      allowed_domains: contextReady ? ["PUBLIC", "OTM1"] : ["PUBLIC"],
      can_view_all_domains: false
    },
    route_recovery: {
      default_path: "/home",
      return_action_key: "return_to_cockpit",
      blocked_route_message: "Return to Project Cockpit and select an available context or accelerator."
    },
    module_summary: { total: 2, counts_by_status: { ACTIVE: 2 }, items: [] },
    recent_jobs: [],
    recent_artifacts: [],
    recent_evidence: [],
    available_actions: []
  };
}

function ratesSummary() {
  return {
    module_id: "rates",
    status: "ACTIVE",
    title: "Rates Studio",
    description: "Synthetic Rates functional shell target.",
    primary_object: "rate_batch",
    counts: [{ key: "batches", label: "Batches", value: 0, severity: "info" }],
    recent_objects: [],
    open_blockers: [],
    recent_jobs: [],
    recent_artifacts: [],
    available_actions: []
  };
}

describe("Functional shell journey", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
  });

  it("persists backend-owned context and preferences across module navigation", async () => {
    let contextReady = false;
    let preferences = {
      theme_mode: "light",
      follow_system_theme: false,
      density: "comfortable",
      sidebar_mode: "expanded"
    };
    const activeContextRequests: unknown[] = [];
    const preferenceUpdates: unknown[] = [];

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
              { id: "rates", label: "Rates Studio", path: "/rates", status: "ACTIVE" }
            ],
            total: 2,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences") && init?.method === "PUT") {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        preferences = JSON.parse(String(init.body));
        preferenceUpdates.push(preferences);
        return Promise.resolve(jsonResponse(preferences));
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(preferences));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(cockpitSummary(contextReady)));
      }
      if (url.endsWith("/api/v1/platform/projects")) {
        return Promise.resolve(jsonResponse({ items: [{ id: "project_1", name: "Synthetic Rollout" }], total: 1 }));
      }
      if (url.endsWith("/api/v1/platform/profiles?project_id=project_1")) {
        return Promise.resolve(jsonResponse({ items: [{ id: "profile_1", name: "Default Profile" }], total: 1 }));
      }
      if (url.endsWith("/api/v1/platform/environments?project_id=project_1")) {
        return Promise.resolve(jsonResponse({ items: [{ id: "environment_1", name: "DEV" }], total: 1 }));
      }
      if (url.endsWith("/api/v1/platform/active-context")) {
        expect(init?.method).toBe("POST");
        const body = JSON.parse(String(init?.body));
        activeContextRequests.push(body);
        expect(body).toEqual({
          project_id: "project_1",
          profile_id: "profile_1",
          environment_id: "environment_1",
          domain_name: "otm1",
          can_view_all_domains: false
        });
        contextReady = true;
        return Promise.resolve(
          jsonResponse({
            project_id: "project_1",
            profile_id: "profile_1",
            environment_id: "environment_1",
            domain_name: "OTM1",
            allowed_domains: ["PUBLIC", "OTM1"],
            can_view_all_domains: false
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/summary")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(ratesSummary()));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    const view = renderFunctionalApp();
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Project Cockpit" })).toBeInTheDocument();
    expect(screen.getByText("No project selected")).toBeInTheDocument();

    await userEvent.selectOptions(await screen.findByLabelText("Project"), "project_1");
    await userEvent.selectOptions(await screen.findByLabelText("Profile"), "profile_1");
    await userEvent.selectOptions(await screen.findByLabelText("Environment"), "environment_1");
    await userEvent.type(screen.getByLabelText("Domain"), "otm1");
    await userEvent.click(screen.getByRole("button", { name: "Apply context" }));

    await waitFor(() => expect(activeContextRequests).toHaveLength(1));
    await waitFor(() => expect(screen.getByText("Private scope")).toBeInTheDocument());
    expect(screen.getByText("OTM1")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Use compact density" }));
    await userEvent.click(screen.getByRole("button", { name: "Collapse sidebar" }));

    await waitFor(() => expect(preferenceUpdates).toHaveLength(2));
    await waitFor(() => expect(view.container.querySelector(".app-shell")).toHaveAttribute("data-density", "compact"));
    expect(view.container.querySelector(".app-shell")).toHaveAttribute("data-sidebar", "collapsed");

    await userEvent.click(within(screen.getByRole("navigation", { name: "Workbench modules" })).getByRole("link", { name: /Rates Studio/ }));
    expect(await screen.findByRole("heading", { name: "Rates Studio" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("link", { name: /Project Cockpit/ }));
    expect(await screen.findByRole("heading", { name: "Project Cockpit" })).toBeInTheDocument();
    expect(screen.getByText("Private scope")).toBeInTheDocument();
    expect(screen.getByText("OTM1")).toBeInTheDocument();
    expect(view.container.querySelector(".app-shell")).toHaveAttribute("data-density", "compact");
    expect(view.container.querySelector(".app-shell")).toHaveAttribute("data-sidebar", "collapsed");
  });

  it("opens the Workbench Assistant shell without adding navigation", async () => {
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
              { id: "rates", label: "Rates Studio", path: "/rates", status: "ACTIVE" }
            ],
            total: 2,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            theme_mode: "light",
            follow_system_theme: false,
            density: "comfortable",
            sidebar_mode: "expanded"
          })
        );
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(cockpitSummary(true)));
      }
      if (url.endsWith("/api/v1/assistant/health")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse({ status: "ok", module: "assistant", capabilities: ["source_index"] }));
      }
      if (url.endsWith("/api/v1/assistant/search?query=shipment+template&limit=5")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                source_id: "source_1",
                source_title: "Shipment template guide",
                source_type: "WORKBENCH_DOC",
                source_uri: "workbench-doc://shipment-template.md",
                module_id: "order_release_generator",
                domain_name: "PUBLIC",
                visibility: "PUBLIC",
                chunk_id: "chunk_1",
                snippet: "Shipment template source for synthetic assistant tests.",
                rank: 1
              }
            ],
            total: 1,
            page: 1,
            page_size: 1
          })
        );
      }
      if (url.endsWith("/api/v1/assistant/oracle-docs/live-lookup")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init?.body));
        expect(body).toEqual({
          query: "client ACME REST API post shipment endpoint",
          private_terms: ["ACME"]
        });
        return Promise.resolve(
          jsonResponse({
            answer_type: "lookup_request",
            summary: "Oracle documentation lookup is prepared and requires an explicit web action.",
            confidence: "high",
            source_mode: "official_search_link",
            cost_level: "web",
            network_performed: false,
            sanitized_query: "client REST API post shipment endpoint",
            actions: [
              {
                label: "Search official Oracle docs",
                url: "https://docs.oracle.com/search/?q=client+REST+API+post+shipment+endpoint",
                source_domain: "docs.oracle.com"
              }
            ],
            warnings: ["No external request was performed."]
          })
        );
      }
      if (url.endsWith("/api/v1/assistant/sql/draft")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init?.body));
        expect(body).toEqual({
          table_name: "RATE_GEO_COST",
          columns: ["RATE_GEO_COST_GROUP_GID", "RATE_GEO_COST_SEQ"],
          filter_column: "RATE_GEO_COST_GROUP_GID",
          purpose: "Find rate cost by group"
        });
        return Promise.resolve(
          jsonResponse({
            answer_type: "sql_draft",
            summary: "Draft SELECT for RATE_GEO_COST.",
            confidence: "high",
            source_mode: "generated_draft",
            cost_level: "local",
            block: {
              type: "sql_draft",
              purpose: "Find rate cost by group",
              sql: "select rgc.RATE_GEO_COST_GROUP_GID, rgc.RATE_GEO_COST_SEQ from RATE_GEO_COST rgc where rgc.RATE_GEO_COST_GROUP_GID = :rate_geo_cost_group_gid",
              parameters: [
                {
                  name: "rate_geo_cost_group_gid",
                  description: "Filter for RATE_GEO_COST.RATE_GEO_COST_GROUP_GID"
                }
              ],
              tables: ["RATE_GEO_COST"],
              columns: ["RATE_GEO_COST.RATE_GEO_COST_GROUP_GID", "RATE_GEO_COST.RATE_GEO_COST_SEQ"],
              assumptions: [],
              warnings: []
            },
            sources: ["Data Dictionary: RATE_GEO_COST"]
          })
        );
      }
      if (url.endsWith("/api/v1/assistant/sql/explain")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init?.body));
        expect(body).toEqual({
          sql_text: "select rgc.RATE_GEO_COST_GROUP_GID, rgc.UNKNOWN_COL from RATE_GEO_COST rgc"
        });
        return Promise.resolve(
          jsonResponse({
            answer_type: "sql_draft",
            summary: "Reviewed SELECT for RATE_GEO_COST.",
            confidence: "medium",
            source_mode: "generated_draft",
            cost_level: "local",
            block: {
              type: "sql_draft",
              purpose: "Explain pasted SELECT.",
              sql: "select rgc.RATE_GEO_COST_GROUP_GID, rgc.UNKNOWN_COL from RATE_GEO_COST rgc",
              parameters: [],
              tables: ["RATE_GEO_COST"],
              columns: ["RATE_GEO_COST.RATE_GEO_COST_GROUP_GID", "RATE_GEO_COST.UNKNOWN_COL"],
              assumptions: [],
              warnings: ["RATE_GEO_COST.UNKNOWN_COL was not found."]
            },
            sources: ["Data Dictionary: RATE_GEO_COST"]
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp();
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Project Cockpit" })).toBeInTheDocument();
    const moduleNav = screen.getByRole("navigation", { name: "Workbench modules" });
    expect(within(moduleNav).queryByRole("link", { name: /Assistant/ })).not.toBeInTheDocument();

    await userEvent.click(await screen.findByRole("button", { name: "Open Workbench Assistant" }));
    expect(await screen.findByRole("heading", { name: "Workbench Assistant" })).toBeInTheDocument();
    expect(await screen.findByText("Assistant backend connected")).toBeInTheDocument();
    const assistantPanel = screen.getByLabelText("Workbench Assistant panel");
    expect(within(assistantPanel).getByText("Current screen")).toBeInTheDocument();
    expect(within(assistantPanel).getByText("Project Cockpit")).toBeInTheDocument();
    expect(within(assistantPanel).getByRole("button", { name: "Help for this screen" })).toBeInTheDocument();
    expect(within(assistantPanel).getByRole("button", { name: "Find template" })).toBeInTheDocument();
    expect(within(assistantPanel).getByRole("button", { name: "Search Oracle docs" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Find template" }));
    expect(screen.getByLabelText("Search Workbench sources")).toHaveValue("Project Cockpit template");

    await userEvent.click(screen.getByRole("button", { name: "Search Oracle docs" }));
    expect(screen.getByLabelText("Oracle docs question")).toHaveValue(
      "Oracle Transportation Management Project Cockpit documentation"
    );

    await userEvent.clear(screen.getByLabelText("Search Workbench sources"));
    await userEvent.type(screen.getByLabelText("Search Workbench sources"), "shipment template");
    await userEvent.click(screen.getByRole("button", { name: "Search sources" }));
    expect(await screen.findByText("Shipment template guide")).toBeInTheDocument();
    expect(screen.getByText("workbench-doc://shipment-template.md")).toBeInTheDocument();

    await userEvent.clear(screen.getByLabelText("Oracle docs question"));
    await userEvent.type(screen.getByLabelText("Oracle docs question"), "client ACME REST API post shipment endpoint");
    await userEvent.type(screen.getByLabelText("Private terms"), "ACME");
    await userEvent.click(screen.getByRole("button", { name: "Prepare Oracle lookup" }));
    expect(await screen.findByText("client REST API post shipment endpoint")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Search official Oracle docs" })).toHaveAttribute(
      "href",
      "https://docs.oracle.com/search/?q=client+REST+API+post+shipment+endpoint"
    );

    await userEvent.type(screen.getByLabelText("SQL table"), "RATE_GEO_COST");
    await userEvent.type(screen.getByLabelText("SQL columns"), "RATE_GEO_COST_GROUP_GID, RATE_GEO_COST_SEQ");
    await userEvent.type(screen.getByLabelText("SQL filter column"), "RATE_GEO_COST_GROUP_GID");
    await userEvent.type(screen.getByLabelText("SQL purpose"), "Find rate cost by group");
    await userEvent.click(screen.getByRole("button", { name: "Draft SQL" }));
    expect(await screen.findByText("SQL draft preview")).toBeInTheDocument();
    expect(
      screen.getByText(
        "select rgc.RATE_GEO_COST_GROUP_GID, rgc.RATE_GEO_COST_SEQ from RATE_GEO_COST rgc where rgc.RATE_GEO_COST_GROUP_GID = :rate_geo_cost_group_gid"
      )
    ).toBeInTheDocument();
    expect(screen.getByText("Review before use; Assistant drafts are not executed.")).toBeInTheDocument();

    await userEvent.type(
      screen.getByLabelText("SQL to review"),
      "select rgc.RATE_GEO_COST_GROUP_GID, rgc.UNKNOWN_COL from RATE_GEO_COST rgc"
    );
    await userEvent.click(screen.getByRole("button", { name: "Review SQL" }));
    expect(await screen.findByText("SQL review preview")).toBeInTheDocument();
    expect(screen.getByText("RATE_GEO_COST.UNKNOWN_COL was not found.")).toBeInTheDocument();
    expect(screen.getByText("Review before use; Assistant SQL review is not execution.")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Close Workbench Assistant" }));
    expect(screen.queryByRole("heading", { name: "Workbench Assistant" })).not.toBeInTheDocument();
  });
});
