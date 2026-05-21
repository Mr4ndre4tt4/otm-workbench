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

  it("renders a reusable module route template from backend navigation", async () => {
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
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/rates");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Rates Studio" });
    expect(screen.getByText("Module workspace")).toBeInTheDocument();
    expect(screen.getByLabelText("Rates Studio module template")).toBeInTheDocument();
    expect(screen.getByText("Available actions from backend")).toBeInTheDocument();
  });
});
