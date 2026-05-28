import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "../platform/auth";

function renderFunctionalApp(initialPath = "/settings") {
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

function settingsScopeAuthority() {
  return {
    module: "settings",
    label: "Settings",
    label_key: "module.settings.label",
    status: "READY",
    active_context: {
      user_id: "user_admin",
      project_id: "project_1",
      profile_id: "profile_1",
      environment_id: "environment_1",
      domain_name: "OTM1",
      allowed_domains: ["PUBLIC", "OTM1"],
      can_view_all_domains: false
    },
    setup_counts: {
      workspaces: 1,
      projects: 1,
      profiles: 1,
      environments: 1
    },
    setup_visibility: {
      level: "PROJECT",
      can_manage_users: true,
      can_manage_workspaces: true,
      can_manage_projects: true,
      can_manage_profiles: true,
      can_manage_environments: true,
      can_manage_roles: true,
      can_manage_grants: true,
      can_manage_access_policies: true
    },
    blocked_reasons: [],
    available_actions: [
      {
        key: "create_workspace",
        label: "Create workspace",
        method: "POST",
        href: "/api/v1/platform/workspaces",
        variant: "primary",
        icon_key: "settings.workspace",
        disabled: false,
        disabled_reason: null,
        requires_confirmation: false
      },
      {
        key: "assign_grant",
        label: "Assign grant",
        method: "POST",
        href: "/api/v1/platform/grants",
        variant: "primary",
        icon_key: "settings.grant",
        disabled: false,
        disabled_reason: null,
        requires_confirmation: false
      }
    ]
  };
}

describe("Functional Settings journey", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("surfaces setup authority, role grants, and access policy bindings from Settings APIs", async () => {
    const roleRequests: unknown[] = [];
    const userRequests: unknown[] = [];
    const grantRequests: unknown[] = [];
    const policyRequests: unknown[] = [];
    let roles = [{ id: "role_1", name: "Rates Operator", capability_names: ["rates.batch.view"] }];
    let users = [{ id: "user_2", email: "operator@example.test", is_active: true, is_admin: false }];
    let grants = [
      {
        id: "grant_1",
        project_id: "project_1",
        project_name: "Synthetic Rollout",
        environment_id: "environment_1",
        domain_name: "OTM1",
        user_id: "user_2",
        user_email: "operator@example.test",
        role_id: "role_1",
        role_name: "Rates Operator",
        binding_scope_label: "Synthetic Rollout / DEV / OTM1",
        binding_requirements: [
          "User: operator@example.test",
          "Role: Rates Operator",
          "Project: Synthetic Rollout",
          "Environment: DEV",
          "Domain: OTM1"
        ],
        active_context_match: true,
        active_context_disabled_reason: null
      }
    ];
    let accessPolicies = [
      {
        id: "policy_1",
        project_id: "project_1",
        project_name: "Synthetic Rollout",
        name: "OTM1 private policy",
        visibility: "PRIVATE",
        domain_name: "OTM1",
        rule_json: "{\"mode\":\"domain_role\"}",
        created_by: "user_admin",
        binding_scope_label: "Synthetic Rollout / PRIVATE / OTM1",
        binding_requirements: ["Project: Synthetic Rollout", "Visibility: PRIVATE", "Domain: OTM1"],
        active_context_match: true,
        active_context_disabled_reason: null
      }
    ];

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
              { id: "settings", label: "Settings", path: "/settings", status: "ACTIVE" }
            ],
            total: 2,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/session/me")) {
        return Promise.resolve(jsonResponse({ id: "user_admin", email: "admin@example.test", is_admin: true }));
      }
      if (url.endsWith("/api/v1/platform/workspaces")) {
        return Promise.resolve(jsonResponse([{ id: "workspace_1", name: "Synthetic Workspace" }]));
      }
      if (url.endsWith("/api/v1/platform/projects")) {
        return Promise.resolve(
          jsonResponse({
            items: [{ id: "project_1", name: "Synthetic Rollout" }],
            total: 1,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/platform/profiles?project_id=project_1")) {
        return Promise.resolve(
          jsonResponse({
            items: [{ id: "profile_1", name: "Default" }],
            total: 1,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/platform/environments?project_id=project_1")) {
        return Promise.resolve(
          jsonResponse({
            items: [{ id: "environment_1", name: "DEV" }],
            total: 1,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/platform/projects/project_1/setup-status")) {
        return Promise.resolve(
          jsonResponse({
            project_id: "project_1",
            project_name: "Synthetic Rollout",
            status: "READY",
            profile_count: 1,
            environment_count: 1,
            active_context_selected: true,
            missing_requirements: []
          })
        );
      }
      if (url.endsWith("/api/v1/platform/settings/scope-authority")) {
        return Promise.resolve(jsonResponse(settingsScopeAuthority()));
      }
      if (url.endsWith("/api/v1/platform/settings/access-model")) {
        return Promise.resolve(
          jsonResponse({
            setup_visibility: settingsScopeAuthority().setup_visibility,
            active_project_id: "project_1",
            users,
            roles,
            capability_names: ["rates.batch.view", "rates.batch.export"],
            grants,
            access_policies: accessPolicies
          })
        );
      }
      if (url.endsWith("/api/v1/platform/active-context/capabilities")) {
        return Promise.resolve(
          jsonResponse({
            user_id: "user_admin",
            project_id: "project_1",
            is_admin: true,
            roles: ["DBA"],
            capabilities: ["*"]
          })
        );
      }
      if (url.endsWith("/api/v1/platform/jobs")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/platform/audit-logs")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/platform/feature-flags")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/platform/roles")) {
        const body = JSON.parse(String(init?.body));
        roleRequests.push(body);
        const role = { id: "role_2", name: body.name, capability_names: body.capability_names };
        roles = [...roles, role];
        return Promise.resolve(jsonResponse(role));
      }
      if (url.endsWith("/api/v1/platform/users")) {
        const body = JSON.parse(String(init?.body));
        userRequests.push(body);
        const user = { id: "user_3", email: body.email, is_active: true, is_admin: false };
        users = [...users, user];
        return Promise.resolve(jsonResponse(user));
      }
      if (url.endsWith("/api/v1/platform/grants")) {
        const body = JSON.parse(String(init?.body));
        grantRequests.push(body);
        const user = users.find((item) => item.id === body.user_id);
        const role = roles.find((item) => item.id === body.role_id);
        const grant = {
          id: "grant_2",
          project_id: body.project_id,
          project_name: "Synthetic Rollout",
          environment_id: body.environment_id,
          domain_name: body.domain_name,
          user_id: body.user_id,
          user_email: user?.email ?? body.user_id,
          role_id: body.role_id,
          role_name: role?.name ?? body.role_id,
          binding_scope_label: "Synthetic Rollout / DEV / OTM1",
          binding_requirements: [
            `User: ${user?.email ?? body.user_id}`,
            `Role: ${role?.name ?? body.role_id}`,
            "Project: Synthetic Rollout",
            "Environment: DEV",
            "Domain: OTM1"
          ],
          active_context_match: true,
          active_context_disabled_reason: null
        };
        grants = [...grants, grant];
        return Promise.resolve(jsonResponse(grant));
      }
      if (url.endsWith("/api/v1/platform/access-policies")) {
        const body = JSON.parse(String(init?.body));
        policyRequests.push(body);
        const policy = {
          id: "policy_2",
          project_id: body.project_id,
          project_name: "Synthetic Rollout",
          name: body.name,
          visibility: body.visibility,
          domain_name: body.domain_name,
          rule_json: body.rule_json,
          created_by: "user_admin",
          binding_scope_label: `Synthetic Rollout / ${body.visibility} / ${body.domain_name}`,
          binding_requirements: [`Project: Synthetic Rollout`, `Visibility: ${body.visibility}`, `Domain: ${body.domain_name}`],
          active_context_match: true,
          active_context_disabled_reason: null
        };
        accessPolicies = [...accessPolicies, policy];
        return Promise.resolve(jsonResponse(policy));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp();
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByLabelText("Settings setup visibility")).toHaveTextContent("PROJECT");
    expect(screen.getByLabelText("Settings setup visibility")).toHaveTextContent("Grants: Manage");
    expect(screen.queryByRole("heading", { name: "Admin Console" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Admin Console/ })).not.toBeInTheDocument();

    expect(screen.getByLabelText("Role authoring")).toHaveTextContent("Rates Operator");
    expect(screen.getByLabelText("User authoring")).toHaveTextContent("operator@example.test");
    expect(screen.getByLabelText("Grant binding review")).toHaveTextContent("Synthetic Rollout / DEV / OTM1");
    expect(screen.getByLabelText("Grant binding review")).toHaveTextContent("READY");
    expect(screen.getByLabelText("Access policy binding review")).toHaveTextContent("Visibility: PRIVATE");
    expect(screen.getByLabelText("Access policy binding review")).toHaveTextContent("READY");

    await userEvent.type(screen.getByLabelText("Role name"), "Load Planner");
    await userEvent.type(screen.getByLabelText("Capabilities"), "load_plan.package.view, load_plan.package.export");
    await userEvent.click(screen.getByRole("button", { name: "Create role" }));
    await waitFor(() =>
      expect(roleRequests).toEqual([
        {
          name: "Load Planner",
          capability_names: ["load_plan.package.view", "load_plan.package.export"]
        }
      ])
    );
    expect(await screen.findByText("Created role Load Planner.")).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("User email"), "planner@example.test");
    await userEvent.click(screen.getByRole("button", { name: "Create user" }));
    await waitFor(() =>
      expect(userRequests).toEqual([
        {
          email: "planner@example.test",
          is_active: true,
          password: "SyntheticPass123!"
        }
      ])
    );
    expect(await screen.findByText("Created user planner@example.test.")).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Grant domain"), "OTM1");
    await userEvent.click(screen.getByRole("button", { name: "Assign grant" }));
    await waitFor(() =>
      expect(grantRequests).toEqual([
        {
          project_id: "project_1",
          environment_id: "environment_1",
          domain_name: "OTM1",
          role_id: "role_2",
          user_id: "user_3"
        }
      ])
    );
    expect(await screen.findByText("Assigned Load Planner to planner@example.test.")).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Policy name"), "OTM1 project policy");
    await userEvent.type(screen.getByLabelText("Domain"), "OTM1");
    await userEvent.click(screen.getByRole("button", { name: "Create access policy" }));
    await waitFor(() =>
      expect(policyRequests).toEqual([
        {
          project_id: "project_1",
          name: "OTM1 project policy",
          visibility: "PRIVATE",
          domain_name: "OTM1",
          rule_json: "{\"mode\":\"domain_role\"}"
        }
      ])
    );
    expect(await screen.findByText("Created access policy OTM1 project policy.")).toBeInTheDocument();
    expect(screen.getByLabelText("Access policy binding review")).toHaveTextContent("OTM1 project policy");

    expect(screen.getByRole("link", { name: "Return to Cockpit" })).toHaveAttribute("href", "/home");
  });
});
