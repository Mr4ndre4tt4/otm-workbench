import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "../platform/auth";

function renderFunctionalApp(initialPath = "/assets/library") {
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

function jsonResponse(body: unknown, status = 200, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers }
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

function cockpitSummary() {
  const activeContext = {
    allowed_domains: ["PUBLIC", "OTM1"],
    can_view_all_domains: false,
    domain_name: "OTM1",
    environment_id: "environment_1",
    profile_id: "profile_1",
    project_id: "project_1"
  };
  return {
    active_context: activeContext,
    accelerators: [
      {
        key: "assets",
        label: "Assets Library",
        description: "Governed reusable implementation files.",
        href: "/assets",
        status: "ACTIVE",
        icon_key: "assets",
        requires_private_context: true,
        disabled: false,
        disabled_reason: null
      }
    ],
    available_actions: [],
    context_selector: {
      active_context: activeContext,
      mode: "PRIVATE",
      public_view_available: true,
      requires_private_context: false,
      set_context_action_key: "set_active_context"
    },
    counts: { recent_artifacts: 0, recent_evidence: 0, recent_jobs: 0 },
    description: "Project-level operational overview.",
    module_id: "home",
    module_summary: { counts_by_status: { ACTIVE: 2 }, items: [], total: 2 },
    recent_artifacts: [],
    recent_evidence: [],
    recent_jobs: [],
    route_recovery: {
      blocked_route_message: "Return to Project Cockpit and select an available context or accelerator.",
      default_path: "/home",
      return_action_key: "return_to_cockpit"
    },
    project_info: {
      contacts: [],
      documents: [],
      links: [],
      secure_vault: {
        metadata_only: true,
        secret_values_available: false,
        status: "NOT_CONFIGURED"
      },
      status: "AVAILABLE",
      title: "Project information"
    },
    setup_status: {
      active_context_selected: true,
      environment_count: 1,
      missing_requirements: [],
      profile_count: 1,
      status: "READY"
    },
    status: "ready",
    title: "Project Cockpit",
    user_scope: {
      allowed_domains: ["PUBLIC", "OTM1"],
      can_view_all_domains: false,
      is_dba: false,
      role_mode: "SCOPED"
    }
  };
}

function assetFixture(status = "DRAFT", currentVersionId: string | null = null) {
  return {
    asset_type: "SPEC",
    category: "INTEGRATION",
    created_at: "2026-05-22T00:00:00",
    created_by: "admin@example.test",
    current_version_id: currentVersionId,
    description: "Client-safe synthetic support asset.",
    environment_id: null,
    id: "asset_qa_1",
    macro_object_code: "ORDER_RELEASE",
    module_id: "integration_mapping",
    name: "Synthetic Mapping Spec",
    otm_table_name: "ORDER_RELEASE",
    profile_id: null,
    project_id: null,
    scope_type: "MODULE",
    sensitivity: "INTERNAL",
    status,
    tags: ["SYNTHETIC", "MVP0"],
    updated_at: null,
    visibility: "PROJECT"
  };
}

function referenceAssetFixture() {
  return {
    ...assetFixture("DRAFT", null),
    category: "TESTING",
    description: "Client-safe selected reference asset.",
    id: "asset_qa_2",
    macro_object_code: "LOCATION",
    module_id: "master_data",
    name: "Synthetic Reference Template",
    otm_table_name: "LOCATION",
    tags: ["REFERENCE", "SYNTHETIC"]
  };
}

function versionFixture() {
  return {
    asset_id: "asset_qa_1",
    content_type: "text/markdown",
    created_at: "2026-05-22T00:00:00",
    file_name: "synthetic_mapping_spec.md",
    id: "asset_version_1",
    sha256: "abc123",
    size_bytes: 42,
    status: "ACTIVE",
    updated_at: null,
    uploaded_by: "admin@example.test",
    version_number: 1
  };
}

function linkFixture() {
  return {
    asset_id: "asset_qa_1",
    created_at: "2026-05-22T00:00:00",
    created_by: "admin@example.test",
    id: "asset_link_1",
    link_type: "MODULE",
    target_id: "integration_mapping",
    target_label: "Integration Mapping Studio",
    updated_at: null
  };
}

function classificationGroups(customClassifications: unknown[] = []) {
  const groups = {
    items: [
      {
        classification_type: "asset_type",
        items: [
          {
            code: "SPEC",
            description: "Functional or technical specification.",
            id: "asset_type_spec",
            is_active: true,
            name: "Specification",
            sort_order: 20,
            system_protected: true
          }
        ],
        total: 1
      },
      {
        classification_type: "asset_category",
        items: [
          {
            code: "INTEGRATION",
            description: "Integration-oriented artifact.",
            id: "asset_category_integration",
            is_active: true,
            name: "Integration",
            sort_order: 20,
            system_protected: true
          }
        ],
        total: 1
      },
      {
        classification_type: "asset_status",
        items: [
          {
            code: "DRAFT",
            description: "Editable draft asset.",
            id: "asset_status_draft",
            is_active: true,
            name: "Draft",
            sort_order: 10,
            system_protected: true
          }
        ],
        total: 1
      },
      {
        classification_type: "asset_link_type",
        items: [
          {
            code: "MODULE",
            description: "Links an asset to a module.",
            id: "asset_link_module",
            is_active: true,
            name: "Module",
            sort_order: 10,
            system_protected: true
          },
          {
            code: "OTM_TABLE",
            description: "Links an asset to an OTM table.",
            id: "asset_link_table",
            is_active: true,
            name: "OTM Table",
            sort_order: 30,
            system_protected: true
          },
          {
            code: "MACRO_OBJECT",
            description: "Links an asset to a Catalog Core macro object.",
            id: "asset_link_macro_object",
            is_active: true,
            name: "Macro Object",
            sort_order: 40,
            system_protected: true
          },
          {
            code: "ARTIFACT",
            description: "Links an asset to an Evidence Hub artifact.",
            id: "asset_link_artifact",
            is_active: true,
            name: "Artifact",
            sort_order: 50,
            system_protected: true
          },
          {
            code: "EVIDENCE",
            description: "Links an asset to Evidence Hub evidence.",
            id: "asset_link_evidence",
            is_active: true,
            name: "Evidence",
            sort_order: 60,
            system_protected: true
          }
        ],
        total: 5
      }
    ],
    total: 4
  };
  customClassifications.forEach((customClassification) => {
    if (
      typeof customClassification !== "object" ||
      customClassification === null ||
      !("classification_type" in customClassification)
    ) {
      return;
    }
    const classification = customClassification as {
      classification_type: string;
    };
    const group = groups.items.find((item) => item.classification_type === classification.classification_type);
    if (group) {
      group.items.push(customClassification as never);
      group.total += 1;
    } else {
      groups.items.push({
        classification_type: classification.classification_type,
        items: [customClassification as never],
        total: 1
      });
    }
  });
  groups.total = groups.items.length;
  return groups;
}

describe("Functional Assets Library journey", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
  });

  it("renders an Assets hub with route-level entry points before opening the library", async () => {
    const fetchMock = vi.fn((input) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(jsonResponse({ access_token: "session_token", token_type: "bearer" }));
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return Promise.resolve(
          jsonResponse({
            items: [
              { id: "home", label: "Project Cockpit", path: "/home", status: "ACTIVE" },
              { id: "assets", label: "Assets Library", path: "/assets", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/session/me")) {
        return Promise.resolve(jsonResponse({ email: "admin@example.test", is_admin: true }));
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(jsonResponse(cockpitSummary()));
      }
      if (url.endsWith("/api/v1/platform/active-context")) {
        return Promise.resolve(jsonResponse({ allowed_domains: ["OTM1"], can_view_all_domains: false, domain_name: "OTM1" }));
      }
      if (url.endsWith("/api/v1/platform/projects")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/profiles")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/environments")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets")) {
        return Promise.resolve(jsonResponse({ items: [assetFixture("DRAFT", null), referenceAssetFixture()], total: 2 }));
      }
      if (url.endsWith("/api/v1/modules/assets/classifications")) {
        return Promise.resolve(jsonResponse(classificationGroups()));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1")) {
        return Promise.resolve(jsonResponse(assetFixture("DRAFT", null)));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/versions")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/links")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp("/assets");
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Assets Library" });
    expect(screen.getByText("Recommended next actions")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open library" })).toHaveAttribute("href", "/assets/library");
    expect(screen.getByRole("link", { name: "Create asset" })).toHaveAttribute("href", "/assets/new");
    expect(screen.getByRole("link", { name: "Manage classifications" })).toHaveAttribute(
      "href",
      "/assets/classifications"
    );
    expect(screen.queryByLabelText("Assets Library workflow")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("link", { name: "Open library" }));
    expect(await screen.findByLabelText("Assets Library workflow")).toHaveTextContent("1Library");
  });

  it("renders asset classifications on a dedicated route without the asset workflow", async () => {
    const fetchMock = vi.fn((input) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(jsonResponse({ access_token: "session_token", token_type: "bearer" }));
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return Promise.resolve(
          jsonResponse({
            items: [
              { id: "home", label: "Project Cockpit", path: "/home", status: "ACTIVE" },
              { id: "assets", label: "Assets Library", path: "/assets", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/session/me")) {
        return Promise.resolve(jsonResponse({ email: "admin@example.test", is_admin: true }));
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(jsonResponse(cockpitSummary()));
      }
      if (url.endsWith("/api/v1/platform/active-context")) {
        return Promise.resolve(jsonResponse({ allowed_domains: ["OTM1"], can_view_all_domains: false, domain_name: "OTM1" }));
      }
      if (url.endsWith("/api/v1/platform/projects")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/profiles")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/environments")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets")) {
        return Promise.resolve(jsonResponse({ items: [referenceAssetFixture()], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/classifications")) {
        return Promise.resolve(jsonResponse(classificationGroups()));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp("/assets/classifications");
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Asset classifications" });
    expect(screen.getByRole("link", { name: "Back to Assets" })).toHaveAttribute("href", "/assets");
    expect(screen.getByRole("link", { name: "Create classification" })).toHaveAttribute(
      "href",
      "/assets/classifications/new"
    );
    expect(screen.getByText("asset_category")).toBeInTheDocument();
    expect(screen.getByText("Integration")).toBeInTheDocument();
    expect(screen.getByText("asset_link_type")).toBeInTheDocument();
    expect(screen.getByText("Module")).toBeInTheDocument();
    expect(screen.queryByLabelText("Assets Library workflow")).not.toBeInTheDocument();
  });

  it("creates an asset classification on a dedicated route", async () => {
    const classificationRequests: unknown[] = [];
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
              { id: "assets", label: "Assets Library", path: "/assets", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/session/me")) {
        return Promise.resolve(jsonResponse({ email: "admin@example.test", is_admin: true }));
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(jsonResponse(cockpitSummary()));
      }
      if (url.endsWith("/api/v1/platform/active-context")) {
        return Promise.resolve(jsonResponse({ allowed_domains: ["OTM1"], can_view_all_domains: false, domain_name: "OTM1" }));
      }
      if (url.endsWith("/api/v1/platform/projects")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/profiles")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/environments")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets")) {
        return Promise.resolve(jsonResponse({ items: [assetFixture("DRAFT", null)], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/classifications") && init?.method === "POST") {
        const body = JSON.parse(String(init.body));
        classificationRequests.push(body);
        return Promise.resolve(
          jsonResponse({
            ...body,
            id: "asset_classification_playbook",
            is_active: true,
            system_protected: false
          })
        );
      }
      if (url.endsWith("/api/v1/modules/assets/classifications")) {
        return Promise.resolve(jsonResponse(classificationGroups()));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp("/assets/classifications/new");
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Create asset classification" });
    expect(screen.getByRole("link", { name: "Back to Classifications" })).toHaveAttribute(
      "href",
      "/assets/classifications"
    );
    expect(screen.queryByLabelText("Assets Library workflow")).not.toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Asset classification type"), "asset_category");
    await userEvent.clear(screen.getByLabelText("Asset classification code"));
    await userEvent.type(screen.getByLabelText("Asset classification code"), "PLAYBOOK");
    await userEvent.clear(screen.getByLabelText("Asset classification name"));
    await userEvent.type(screen.getByLabelText("Asset classification name"), "Playbook");
    await userEvent.click(screen.getByRole("button", { name: "Create classification" }));

    expect(await screen.findByText("Classification PLAYBOOK created.")).toBeInTheDocument();
    expect(classificationRequests).toEqual([
      {
        classification_type: "asset_category",
        code: "PLAYBOOK",
        description: "Client-safe reusable implementation playbook.",
        name: "Playbook",
        sort_order: 90
      }
    ]);
  });

  it("edits an asset classification on a dedicated route", async () => {
    const classificationUpdates: unknown[] = [];
    const customClassification = {
      classification_type: "asset_category",
      code: "PLAYBOOK",
      description: "Client-safe reusable implementation playbook.",
      id: "asset_classification_playbook",
      is_active: true,
      name: "Playbook",
      sort_order: 90,
      system_protected: false
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
              { id: "assets", label: "Assets Library", path: "/assets", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/session/me")) {
        return Promise.resolve(jsonResponse({ email: "admin@example.test", is_admin: true }));
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(jsonResponse(cockpitSummary()));
      }
      if (url.endsWith("/api/v1/platform/active-context")) {
        return Promise.resolve(jsonResponse({ allowed_domains: ["OTM1"], can_view_all_domains: false, domain_name: "OTM1" }));
      }
      if (url.endsWith("/api/v1/platform/projects")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/profiles")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/environments")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets")) {
        return Promise.resolve(jsonResponse({ items: [assetFixture("DRAFT", null)], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/classifications/asset_classification_playbook")) {
        const body = JSON.parse(String(init?.body));
        classificationUpdates.push(body);
        return Promise.resolve(jsonResponse({ ...customClassification, ...body }));
      }
      if (url.endsWith("/api/v1/modules/assets/classifications")) {
        return Promise.resolve(jsonResponse(classificationGroups([customClassification])));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp("/assets/classifications/asset_classification_playbook/edit");
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Edit Playbook" });
    expect(screen.getByRole("link", { name: "Back to Classifications" })).toHaveAttribute(
      "href",
      "/assets/classifications"
    );
    await userEvent.clear(screen.getByLabelText("Asset classification name"));
    await userEvent.type(screen.getByLabelText("Asset classification name"), "Playbook Updated");
    await userEvent.clear(screen.getByLabelText("Asset classification description"));
    await userEvent.type(screen.getByLabelText("Asset classification description"), "Updated route-level classification.");
    await userEvent.click(screen.getByRole("button", { name: "Save classification" }));

    expect(await screen.findByText("Classification PLAYBOOK saved.")).toBeInTheDocument();
    expect(classificationUpdates).toEqual([
      {
        description: "Updated route-level classification.",
        is_active: true,
        name: "Playbook Updated",
        sort_order: 90
      }
    ]);
  });

  it("creates an asset on a dedicated route without classification authoring", async () => {
    const assetRequests: unknown[] = [];
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
              { id: "assets", label: "Assets Library", path: "/assets", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/session/me")) {
        return Promise.resolve(jsonResponse({ email: "admin@example.test", is_admin: true }));
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(jsonResponse(cockpitSummary()));
      }
      if (url.endsWith("/api/v1/platform/active-context")) {
        return Promise.resolve(jsonResponse({ allowed_domains: ["OTM1"], can_view_all_domains: false, domain_name: "OTM1" }));
      }
      if (url.endsWith("/api/v1/platform/projects")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/profiles")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/environments")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets") && init?.method === "POST") {
        const body = JSON.parse(String(init.body));
        assetRequests.push(body);
        return Promise.resolve(
          jsonResponse({
            ...assetFixture("DRAFT", null),
            ...body,
            created_at: "2026-05-22T00:00:00",
            created_by: "admin@example.test",
            id: "asset_created_route",
            tags: body.tags
          })
        );
      }
      if (url.endsWith("/api/v1/modules/assets/assets")) {
        return Promise.resolve(jsonResponse({ items: [assetFixture("DRAFT", null)], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/classifications")) {
        return Promise.resolve(jsonResponse(classificationGroups()));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp("/assets/new");
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Create asset" });
    expect(screen.getByRole("link", { name: "Back to Library" })).toHaveAttribute("href", "/assets/library");
    expect(screen.getByRole("link", { name: "Cancel" })).toHaveAttribute("href", "/assets/library");
    expect(screen.queryByLabelText("Assets Library workflow")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Asset classification authoring")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Asset name")).toHaveValue("Synthetic Mapping Spec");

    await userEvent.clear(screen.getByLabelText("Asset name"));
    await userEvent.type(screen.getByLabelText("Asset name"), "Synthetic Route Asset");
    await userEvent.clear(screen.getByLabelText("Asset description"));
    await userEvent.type(screen.getByLabelText("Asset description"), "Created from the dedicated route.");
    await userEvent.click(screen.getByRole("button", { name: "Create asset" }));

    expect(await screen.findByText("Asset Synthetic Route Asset created.")).toBeInTheDocument();
    expect(assetRequests).toEqual([
      {
        asset_type: "SPEC",
        category: "INTEGRATION",
        description: "Created from the dedicated route.",
        macro_object_code: "ORDER_RELEASE",
        module_id: "integration_mapping",
        name: "Synthetic Route Asset",
        otm_table_name: "ORDER_RELEASE",
        scope_type: "MODULE",
        sensitivity: "INTERNAL",
        tags: ["SYNTHETIC", "MVP0"],
        visibility: "PROJECT"
      }
    ]);
  });

  it("renders an asset detail route with metadata, versions, links, actions, and return paths", async () => {
    const downloadRequests: unknown[] = [];
    const fetchMock = vi.fn((input) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(jsonResponse({ access_token: "session_token", token_type: "bearer" }));
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return Promise.resolve(
          jsonResponse({
            items: [
              { id: "home", label: "Project Cockpit", path: "/home", status: "ACTIVE" },
              { id: "assets", label: "Assets Library", path: "/assets", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/session/me")) {
        return Promise.resolve(jsonResponse({ email: "admin@example.test", is_admin: true }));
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(jsonResponse(cockpitSummary()));
      }
      if (url.endsWith("/api/v1/platform/active-context")) {
        return Promise.resolve(jsonResponse({ allowed_domains: ["OTM1"], can_view_all_domains: false, domain_name: "OTM1" }));
      }
      if (url.endsWith("/api/v1/platform/projects")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/profiles")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/environments")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets")) {
        return Promise.resolve(jsonResponse({ items: [assetFixture("ACTIVE", "asset_version_1")], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/classifications")) {
        return Promise.resolve(jsonResponse(classificationGroups()));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1")) {
        return Promise.resolve(jsonResponse(assetFixture("ACTIVE", "asset_version_1")));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/versions")) {
        return Promise.resolve(jsonResponse({ items: [versionFixture()], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/links")) {
        return Promise.resolve(jsonResponse({ items: [linkFixture()], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/download")) {
        downloadRequests.push({ method: "GET" });
        return Promise.resolve(
          new Response("synthetic file", {
            headers: {
              "Content-Disposition": 'attachment; filename="synthetic_mapping_spec.md"',
              "Content-Type": "text/markdown"
            }
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp("/assets/asset_qa_1");
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Synthetic Mapping Spec" });
    expect(screen.getAllByText("Asset detail").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "Back to Library" })).toHaveAttribute("href", "/assets/library");
    expect(screen.getByRole("link", { name: "Back to Assets" })).toHaveAttribute("href", "/assets");
    expect(screen.getByRole("link", { name: "Edit metadata" })).toHaveAttribute("href", "/assets/asset_qa_1/edit");
    expect(screen.getByRole("link", { name: "Upload version" })).toHaveAttribute(
      "href",
      "/assets/asset_qa_1/versions/new"
    );
    expect(screen.getByRole("link", { name: "View versions" })).toHaveAttribute(
      "href",
      "/assets/asset_qa_1/versions"
    );
    expect(screen.getByRole("link", { name: "Manage links" })).toHaveAttribute("href", "/assets/asset_qa_1/links");
    expect(screen.getByRole("link", { name: "Archive asset" })).toHaveAttribute("href", "/assets/asset_qa_1/archive");
    expect(screen.getByLabelText("Asset detail metadata")).toHaveTextContent("ORDER_RELEASE");
    expect(screen.getByLabelText("Asset detail versions")).toHaveTextContent("synthetic_mapping_spec.md");
    expect(screen.getByLabelText("Asset detail links")).toHaveTextContent("Integration Mapping Studio");
    expect(screen.queryByLabelText("Assets Library workflow")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Download current version" }));
    await screen.findByText("Download started: synthetic_mapping_spec.md.");
    expect(downloadRequests).toEqual([{ method: "GET" }]);
  });

  it("renders library row actions for detail, version upload, and archive", async () => {
    const fetchMock = vi.fn((input) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return Promise.resolve(jsonResponse({ access_token: "session_token", token_type: "bearer" }));
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return Promise.resolve(
          jsonResponse({
            items: [
              { id: "home", label: "Project Cockpit", path: "/home", status: "ACTIVE" },
              { id: "assets", label: "Assets Library", path: "/assets", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/session/me")) {
        return Promise.resolve(jsonResponse({ email: "admin@example.test", is_admin: true }));
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(jsonResponse(cockpitSummary()));
      }
      if (url.endsWith("/api/v1/platform/active-context")) {
        return Promise.resolve(jsonResponse({ allowed_domains: ["OTM1"], can_view_all_domains: false, domain_name: "OTM1" }));
      }
      if (url.endsWith("/api/v1/platform/projects")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/profiles")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/environments")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets")) {
        return Promise.resolve(jsonResponse({ items: [assetFixture("DRAFT", null)], total: 1, page: 1, page_size: 50 }));
      }
      if (url.endsWith("/api/v1/modules/assets/classifications")) {
        return Promise.resolve(jsonResponse(classificationGroups()));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1")) {
        return Promise.resolve(jsonResponse(assetFixture("DRAFT", null)));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/versions")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/links")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp("/assets/library");
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Assets Library" });
    const assetRows = screen.getByLabelText("Assets");

    expect(within(assetRows).getByRole("link", { name: "Open Synthetic Mapping Spec" })).toHaveAttribute(
      "href",
      "/assets/asset_qa_1"
    );
    expect(within(assetRows).getByRole("link", { name: "Upload version for Synthetic Mapping Spec" })).toHaveAttribute(
      "href",
      "/assets/asset_qa_1/versions/new"
    );
    expect(within(assetRows).getByRole("link", { name: "Archive Synthetic Mapping Spec" })).toHaveAttribute(
      "href",
      "/assets/asset_qa_1/archive"
    );
  });

  it("edits asset metadata on a direct route without showing the legacy workflow", async () => {
    const updateRequests: unknown[] = [];
    let updatedAsset = assetFixture("DRAFT", null);
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
              { id: "assets", label: "Assets Library", path: "/assets", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/session/me")) {
        return Promise.resolve(jsonResponse({ email: "admin@example.test", is_admin: true }));
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(jsonResponse(cockpitSummary()));
      }
      if (url.endsWith("/api/v1/platform/active-context")) {
        return Promise.resolve(jsonResponse({ allowed_domains: ["OTM1"], can_view_all_domains: false, domain_name: "OTM1" }));
      }
      if (url.endsWith("/api/v1/platform/projects")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/profiles")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/environments")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets")) {
        return Promise.resolve(jsonResponse({ items: [updatedAsset], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/classifications")) {
        return Promise.resolve(jsonResponse(classificationGroups()));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1")) {
        if (init?.method === "PATCH") {
          const body = JSON.parse(String(init?.body));
          updateRequests.push(body);
          updatedAsset = { ...updatedAsset, ...body, tags: body.tags };
          return Promise.resolve(jsonResponse(updatedAsset));
        }
        return Promise.resolve(jsonResponse(updatedAsset));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/versions")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/links")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp("/assets/asset_qa_1/edit");
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Edit Synthetic Mapping Spec" });
    expect(screen.getByRole("link", { name: "Back to Asset" })).toHaveAttribute("href", "/assets/asset_qa_1");
    expect(screen.getByRole("link", { name: "Back to Library" })).toHaveAttribute("href", "/assets/library");
    expect(screen.queryByLabelText("Assets Library workflow")).not.toBeInTheDocument();

    await userEvent.clear(screen.getByLabelText("Asset name"));
    await userEvent.type(screen.getByLabelText("Asset name"), "Synthetic Mapping Spec Updated");
    await userEvent.clear(screen.getByLabelText("Asset description"));
    await userEvent.type(screen.getByLabelText("Asset description"), "Updated client-safe synthetic asset.");
    await userEvent.click(screen.getByRole("button", { name: "Save metadata" }));

    await screen.findByText("Asset Synthetic Mapping Spec Updated updated.");
    expect(updateRequests).toEqual([
      expect.objectContaining({
        name: "Synthetic Mapping Spec Updated",
        description: "Updated client-safe synthetic asset.",
        asset_type: "SPEC",
        category: "INTEGRATION",
        visibility: "PROJECT",
        scope_type: "MODULE",
        sensitivity: "INTERNAL"
      })
    ]);
  });

  it("renders an asset versions route with history, guarded download, and return paths", async () => {
    const downloadRequests: unknown[] = [];
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
              { id: "assets", label: "Assets Library", path: "/assets", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/session/me")) {
        return Promise.resolve(jsonResponse({ email: "admin@example.test", is_admin: true }));
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(jsonResponse(cockpitSummary()));
      }
      if (url.endsWith("/api/v1/platform/active-context")) {
        return Promise.resolve(jsonResponse(cockpitSummary().active_context));
      }
      if (url.endsWith("/api/v1/modules/assets/assets")) {
        return Promise.resolve(jsonResponse({ items: [assetFixture("ACTIVE", "asset_version_1")], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/classifications")) {
        return Promise.resolve(jsonResponse(classificationGroups()));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1")) {
        return Promise.resolve(jsonResponse(assetFixture("ACTIVE", "asset_version_1")));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/versions")) {
        return Promise.resolve(jsonResponse({ items: [versionFixture()], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/links")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/download")) {
        downloadRequests.push({ method: init?.method ?? "GET" });
        return Promise.resolve(
          new Response("asset file", { headers: { "Content-Disposition": "attachment; filename=synthetic_mapping_spec.md" } })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp("/assets/asset_qa_1/versions");
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Versions for Synthetic Mapping Spec" });
    expect(screen.getByRole("link", { name: "Back to Asset" })).toHaveAttribute("href", "/assets/asset_qa_1");
    expect(screen.getByRole("link", { name: "Back to Library" })).toHaveAttribute("href", "/assets/library");
    expect(screen.getByRole("link", { name: "Upload new version" })).toHaveAttribute(
      "href",
      "/assets/asset_qa_1/versions/new"
    );
    expect(screen.getByLabelText("Asset versions rows")).toHaveTextContent("synthetic_mapping_spec.md");
    expect(screen.getByLabelText("Asset versions rows")).toHaveTextContent("v1");
    expect(screen.queryByLabelText("Assets Library workflow")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Download current version" }));
    await screen.findByText("Download started: synthetic_mapping_spec.md.");
    expect(downloadRequests).toEqual([{ method: "GET" }]);
  });

  it("uploads an asset version on a direct route without showing the legacy workflow", async () => {
    const uploadRequests: unknown[] = [];
    let uploadedVersion: ReturnType<typeof versionFixture> | null = null;
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
              { id: "assets", label: "Assets Library", path: "/assets", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/session/me")) {
        return Promise.resolve(jsonResponse({ email: "admin@example.test", is_admin: true }));
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(jsonResponse(cockpitSummary()));
      }
      if (url.endsWith("/api/v1/platform/active-context")) {
        return Promise.resolve(jsonResponse(cockpitSummary().active_context));
      }
      if (url.endsWith("/api/v1/modules/assets/assets")) {
        return Promise.resolve(jsonResponse({ items: [assetFixture("DRAFT", null)], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/classifications")) {
        return Promise.resolve(jsonResponse(classificationGroups()));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1")) {
        return Promise.resolve(jsonResponse(assetFixture(uploadedVersion ? "ACTIVE" : "DRAFT", uploadedVersion?.id ?? null)));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/versions")) {
        if (init?.method === "POST") {
          expect(init?.body).toBeInstanceOf(FormData);
          uploadRequests.push({ method: init?.method });
          uploadedVersion = versionFixture();
          return Promise.resolve(jsonResponse(uploadedVersion));
        }
        return Promise.resolve(jsonResponse({ items: uploadedVersion ? [uploadedVersion] : [], total: uploadedVersion ? 1 : 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/links")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp("/assets/asset_qa_1/versions/new");
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Upload version for Synthetic Mapping Spec" });
    expect(screen.getByRole("link", { name: "Back to Asset" })).toHaveAttribute("href", "/assets/asset_qa_1");
    expect(screen.getByRole("link", { name: "Version history" })).toHaveAttribute(
      "href",
      "/assets/asset_qa_1/versions"
    );
    expect(screen.queryByLabelText("Assets Library workflow")).not.toBeInTheDocument();

    const versionFile = new File(["# synthetic mapping spec"], "synthetic_mapping_spec.md", { type: "text/markdown" });
    await userEvent.upload(screen.getByLabelText("Asset version file"), versionFile);
    await userEvent.click(screen.getByRole("button", { name: "Upload version" }));
    await screen.findByText("Asset version synthetic_mapping_spec.md uploaded.");
    expect(uploadRequests).toEqual([{ method: "POST" }]);
  });

  it("creates an asset link on a direct route without showing the legacy workflow", async () => {
    const linkRequests: unknown[] = [];
    let createdLink: ReturnType<typeof linkFixture> | null = null;
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
              { id: "assets", label: "Assets Library", path: "/assets", status: "ACTIVE" },
              {
                id: "integration_mapping",
                label: "Integration Mapping Studio",
                path: "/integration-mapping",
                status: "ACTIVE"
              }
            ],
            page: 1,
            page_size: 50,
            total: 3
          })
        );
      }
      if (url.endsWith("/api/v1/platform/session/me")) {
        return Promise.resolve(jsonResponse({ email: "admin@example.test", is_admin: true }));
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(jsonResponse(cockpitSummary()));
      }
      if (url.endsWith("/api/v1/platform/active-context")) {
        return Promise.resolve(jsonResponse(cockpitSummary().active_context));
      }
      if (url.endsWith("/api/v1/modules/assets/assets")) {
        return Promise.resolve(jsonResponse({ items: [assetFixture("ACTIVE", "asset_version_1")], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/classifications")) {
        return Promise.resolve(jsonResponse(classificationGroups()));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1")) {
        return Promise.resolve(jsonResponse(assetFixture("ACTIVE", "asset_version_1")));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/versions")) {
        return Promise.resolve(jsonResponse({ items: [versionFixture()], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/links")) {
        if (init?.method === "POST") {
          const body = JSON.parse(String(init.body));
          linkRequests.push(body);
          createdLink = { ...linkFixture(), target_id: body.target_id, target_label: body.target_label };
          return Promise.resolve(jsonResponse(createdLink));
        }
        return Promise.resolve(jsonResponse({ items: createdLink ? [createdLink] : [], total: createdLink ? 1 : 0 }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp("/assets/asset_qa_1/links");
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Links for Synthetic Mapping Spec" });
    expect(screen.getByRole("link", { name: "Back to Asset" })).toHaveAttribute("href", "/assets/asset_qa_1");
    expect(screen.getByRole("link", { name: "Back to Library" })).toHaveAttribute("href", "/assets/library");
    expect(screen.queryByLabelText("Assets Library workflow")).not.toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Asset link type"), "MODULE");
    await userEvent.selectOptions(screen.getByLabelText("Asset guided link target"), "integration_mapping");
    await userEvent.click(screen.getByRole("button", { name: "Create link" }));

    await screen.findByText("Asset link integration_mapping created.");
    expect(screen.getByLabelText("Asset links rows")).toHaveTextContent("Integration Mapping Studio");
    expect(linkRequests).toEqual([
      {
        link_type: "MODULE",
        target_id: "integration_mapping",
        target_label: "Integration Mapping Studio"
      }
    ]);
  });

  it("archives an asset on a direct route without showing the legacy workflow", async () => {
    const archiveRequests: unknown[] = [];
    let archivedAsset = assetFixture("ACTIVE", "asset_version_1");
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
              { id: "assets", label: "Assets Library", path: "/assets", status: "ACTIVE" }
            ],
            page: 1,
            page_size: 50,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/session/me")) {
        return Promise.resolve(jsonResponse({ email: "admin@example.test", is_admin: true }));
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(jsonResponse(cockpitSummary()));
      }
      if (url.endsWith("/api/v1/platform/active-context")) {
        return Promise.resolve(jsonResponse(cockpitSummary().active_context));
      }
      if (url.endsWith("/api/v1/modules/assets/assets")) {
        return Promise.resolve(jsonResponse({ items: [archivedAsset], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/classifications")) {
        return Promise.resolve(jsonResponse(classificationGroups()));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1")) {
        return Promise.resolve(jsonResponse(archivedAsset));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/versions")) {
        return Promise.resolve(jsonResponse({ items: [versionFixture()], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/links")) {
        return Promise.resolve(jsonResponse({ items: [linkFixture()], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/archive")) {
        archiveRequests.push({ method: init?.method });
        archivedAsset = { ...archivedAsset, status: "ARCHIVED" };
        return Promise.resolve(jsonResponse(archivedAsset));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp("/assets/asset_qa_1/archive");
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Archive Synthetic Mapping Spec" });
    expect(screen.getByRole("link", { name: "Back to Asset" })).toHaveAttribute("href", "/assets/asset_qa_1");
    expect(screen.getByRole("link", { name: "Back to Library" })).toHaveAttribute("href", "/assets/library");
    expect(screen.getByRole("link", { name: "Cancel" })).toHaveAttribute("href", "/assets/asset_qa_1");
    expect(screen.getByLabelText("Asset archive impact")).toHaveTextContent("asset_version_1");
    expect(screen.getByLabelText("Asset archive impact")).toHaveTextContent("1 linked target");
    expect(screen.queryByLabelText("Assets Library workflow")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Archive asset" }));
    await screen.findByText("Asset Synthetic Mapping Spec archived.");
    expect(screen.getByLabelText("Asset archive impact")).toHaveTextContent("ARCHIVED");
    expect(screen.getByRole("button", { name: "Archive asset" })).toBeDisabled();
    expect(archiveRequests).toEqual([{ method: "POST" }]);
  });

  it("creates an asset, uploads a version, links it, downloads it, archives it, and returns with backend state", async () => {
    const createRequests: unknown[] = [];
    const classificationRequests: unknown[] = [];
    const updateRequests: unknown[] = [];
    const uploadRequests: unknown[] = [];
    const invalidLinkRequests: unknown[] = [];
    const invalidMacroLinkRequests: unknown[] = [];
    const linkRequests: unknown[] = [];
    const downloadRequests: unknown[] = [];
    const archiveRequests: unknown[] = [];
    const listUrls: string[] = [];
    const evidenceUrls: string[] = [];
    let createdAsset: ReturnType<typeof assetFixture> | null = null;
    const referenceAsset = referenceAssetFixture();
    let uploadedVersion: ReturnType<typeof versionFixture> | null = null;
    let createdLink: ReturnType<typeof linkFixture> | null = null;
    let customClassification: unknown | null = null;

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
              { id: "assets", label: "Assets Library", path: "/assets", status: "ACTIVE" },
              {
                id: "integration_mapping",
                label: "Integration Mapping Studio",
                path: "/integration-mapping",
                status: "ACTIVE"
              }
            ],
            page: 1,
            page_size: 50,
            total: 3
          })
        );
      }
      if (url.endsWith("/api/v1/catalog/macro-objects")) {
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                allow_csvutil: true,
                allow_cutover: true,
                category: "RATES",
                code: "RATE_RECORD",
                default_load_order: 10,
                default_method: "CSVUTIL",
                description: "Rate record macro object.",
                evidence_required_default: true,
                id: "macro_rate_record",
                method_options: ["CSVUTIL"],
                name: "Rate Record"
              },
              {
                allow_csvutil: true,
                allow_cutover: true,
                category: "MASTER_DATA",
                code: "LOCATION",
                default_load_order: 20,
                default_method: "CSVUTIL",
                description: "Location macro object.",
                evidence_required_default: true,
                id: "macro_location",
                method_options: ["CSVUTIL"],
                name: "Location"
              }
            ],
            total: 2
          })
        );
      }
      if (url.includes("/api/v1/catalog/tables")) {
        const parsedUrl = new URL(url, "http://localhost");
        const query = (parsedUrl.searchParams.get("query") ?? "").toUpperCase();
        const items = query.includes("RATE_GEO")
          ? [
              {
                allow_csvutil: true,
                allow_cutover: true,
                column_count: 12,
                data_category: "RATES_SETUP",
                description: "Rate geo table.",
                is_transactional: false,
                schema_name: "GLOGOWNER",
                table_name: "RATE_GEO"
              },
              {
                allow_csvutil: true,
                allow_cutover: true,
                column_count: 18,
                data_category: "RATES_SETUP",
                description: "Rate geo cost table.",
                is_transactional: false,
                schema_name: "GLOGOWNER",
                table_name: "RATE_GEO_COST"
              }
            ]
          : [];
        return Promise.resolve(jsonResponse({ items, page: 1, page_size: items.length, total: items.length }));
      }
      if (url.includes("/api/v1/evidence-hub/evidence")) {
        evidenceUrls.push(url);
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                artifact: {
                  artifact_type: "integration_markdown_spec",
                  content_type: "text/markdown",
                  created_at: "2026-05-22T00:00:00",
                  file_name: "synthetic_mapping_spec.md",
                  id: "artifact_qa_1",
                  sensitivity_level: "client_safe",
                  sha256: "sha-artifact-1",
                  size_bytes: 42,
                  source_module: "integration_mapping"
                },
                client_safe: true,
                created_at: "2026-05-22T00:00:00",
                evidence_type: "integration_mapping_spec",
                id: "evidence_qa_1",
                manifest: null,
                project_id: null,
                sensitivity_level: "client_safe",
                source_module: "integration_mapping",
                status: "CREATED",
                summary: {}
              },
              {
                artifact: {
                  artifact_type: "integration_markdown_spec",
                  content_type: "text/markdown",
                  created_at: "2026-05-22T00:00:00",
                  file_name: "synthetic_mapping_spec.md",
                  id: "artifact_qa_1",
                  sensitivity_level: "client_safe",
                  sha256: "sha-artifact-1",
                  size_bytes: 42,
                  source_module: "integration_mapping"
                },
                client_safe: true,
                created_at: "2026-05-22T00:01:00",
                evidence_type: "integration_mapping_spec_review",
                id: "evidence_qa_2",
                manifest: null,
                project_id: null,
                sensitivity_level: "client_safe",
                source_module: "integration_mapping",
                status: "CREATED",
                summary: {}
              }
            ],
            page: 1,
            page_size: 2,
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/platform/session/me")) {
        return Promise.resolve(jsonResponse({ email: "admin@example.test", is_admin: true }));
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        return Promise.resolve(jsonResponse(cockpitSummary()));
      }
      if (url.endsWith("/api/v1/platform/active-context")) {
        return Promise.resolve(jsonResponse({ allowed_domains: ["OTM1"], can_view_all_domains: false, domain_name: "OTM1" }));
      }
      if (url.endsWith("/api/v1/platform/projects")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/profiles")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/platform/environments")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/classifications")) {
        if (init?.method === "POST") {
          expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
          const body = JSON.parse(String(init?.body));
          classificationRequests.push(body);
          customClassification = {
            ...body,
            code: String(body.code).toUpperCase(),
            id: `asset_classification_${String(body.code).toLowerCase()}`,
            is_active: true,
            system_protected: false
          };
          return Promise.resolve(jsonResponse(customClassification));
        }
        return Promise.resolve(jsonResponse(classificationGroups(customClassification ? [customClassification] : [])));
      }
      if (url.includes("/api/v1/modules/assets/assets") && !url.includes("/asset_qa_1") && !url.includes("/asset_qa_2")) {
        if (init?.method === "POST") {
          expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
          const body = JSON.parse(String(init?.body));
          createRequests.push(body);
          createdAsset = {
            ...assetFixture("DRAFT", null),
            asset_type: body.asset_type,
            category: body.category,
            description: body.description,
            macro_object_code: body.macro_object_code,
            module_id: body.module_id,
            name: body.name,
            otm_table_name: body.otm_table_name,
            scope_type: body.scope_type,
            sensitivity: body.sensitivity,
            tags: body.tags,
            visibility: body.visibility
          };
          return Promise.resolve(jsonResponse(createdAsset));
        }
        listUrls.push(url);
        const items = createdAsset ? [createdAsset, referenceAsset] : [];
        return Promise.resolve(jsonResponse({ items, total: items.length }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1")) {
        if (init?.method === "PATCH") {
          expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
          const body = JSON.parse(String(init?.body));
          updateRequests.push(body);
          createdAsset = { ...(createdAsset ?? assetFixture("DRAFT", null)), ...body };
          return Promise.resolve(jsonResponse(createdAsset));
        }
        return Promise.resolve(jsonResponse(createdAsset ?? assetFixture("DRAFT", null)));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_2")) {
        return Promise.resolve(jsonResponse(referenceAsset));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/versions")) {
        if (init?.method === "POST") {
          expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
          expect(init?.body).toBeInstanceOf(FormData);
          uploadRequests.push({ method: init?.method });
          uploadedVersion = versionFixture();
          createdAsset = { ...(createdAsset ?? assetFixture("DRAFT", null)), current_version_id: uploadedVersion.id };
          return Promise.resolve(jsonResponse(uploadedVersion));
        }
        return Promise.resolve(jsonResponse({ items: uploadedVersion ? [uploadedVersion] : [], total: uploadedVersion ? 1 : 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/links")) {
        if (init?.method === "POST") {
          expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
          const body = JSON.parse(String(init?.body));
          if (body.target_id === "NOT_A_REAL_OTM_TABLE") {
            invalidLinkRequests.push(body);
            return Promise.resolve(
              jsonResponse(
                {
                  code: "ASSET_LINK_INVALID_TABLE",
                  message: "OTM table not found in Data Dictionary."
                },
                400
              )
            );
          }
          if (body.target_id === "NOT_A_MACRO_OBJECT") {
            invalidMacroLinkRequests.push(body);
            return Promise.resolve(
              jsonResponse(
                {
                  code: "ASSET_LINK_INVALID_MACRO_OBJECT",
                  message: "OTM macro object not found in Catalog Core."
                },
                400
              )
            );
          }
          linkRequests.push(body);
          createdLink = { ...linkFixture(), link_type: body.link_type, target_id: body.target_id, target_label: body.target_label };
          return Promise.resolve(jsonResponse(createdLink));
        }
        return Promise.resolve(jsonResponse({ items: createdLink ? [createdLink] : [], total: createdLink ? 1 : 0 }));
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/download")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        downloadRequests.push({ method: init?.method ?? "GET" });
        return Promise.resolve(
          new Response(new Blob(["# synthetic mapping spec"], { type: "text/markdown" }), {
            headers: { "Content-Disposition": "attachment; filename=\"synthetic_mapping_spec.md\"" },
            status: 200
          })
        );
      }
      if (url.endsWith("/api/v1/modules/assets/assets/asset_qa_1/archive")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        archiveRequests.push({ method: init?.method });
        createdAsset = { ...(createdAsset ?? assetFixture("DRAFT", uploadedVersion?.id ?? null)), status: "ARCHIVED" };
        return Promise.resolve(jsonResponse(createdAsset));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp();
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Assets Library" });
    expect(screen.getByLabelText("Assets Library workflow")).toHaveTextContent("1Library");
    expect(screen.getByLabelText("Assets Library workflow")).toHaveTextContent("2Create");
    expect(screen.getByLabelText("Assets Library workflow")).toHaveTextContent("3Version");
    expect(screen.getByLabelText("Assets Library workflow")).toHaveTextContent("4Link");
    expect(screen.getByLabelText("Assets Library workflow")).toHaveTextContent("5Lifecycle");

    await userEvent.type(screen.getByLabelText("Asset name search"), "Rate Table");
    await userEvent.selectOptions(screen.getByLabelText("Asset name operator"), "contains");
    await userEvent.type(screen.getByLabelText("Asset description search"), "support asset");
    await userEvent.selectOptions(screen.getByLabelText("Asset description operator"), "contains");
    await userEvent.selectOptions(screen.getByLabelText("Asset type filter"), "SPEC");
    await userEvent.selectOptions(screen.getByLabelText("Asset category filter"), "INTEGRATION");
    await userEvent.selectOptions(screen.getByLabelText("Asset status filter"), "DRAFT");
    await userEvent.type(screen.getByLabelText("Asset tag filter"), "MVP0");
    await userEvent.selectOptions(screen.getByLabelText("Asset scope filter"), "MODULE");
    await userEvent.type(screen.getByLabelText("Asset module filter"), "rates");
    await userEvent.selectOptions(screen.getByLabelText("Asset module operator"), "one_of");
    await userEvent.type(screen.getByLabelText("Asset macro object filter"), "RATE_GEO");
    await userEvent.selectOptions(screen.getByLabelText("Asset macro object operator"), "begins_with");
    await userEvent.type(screen.getByLabelText("Asset OTM table filter"), "RATE_GEO_COST");
    await userEvent.selectOptions(screen.getByLabelText("Asset OTM table operator"), "one_of");
    await userEvent.selectOptions(screen.getByLabelText("Asset page size"), "25");
    await userEvent.click(screen.getByRole("button", { name: "Apply search" }));
    expect(
      listUrls.some(
        (url) =>
          url.includes("name=Rate+Table") &&
          url.includes("name_operator=contains") &&
          url.includes("description=support+asset") &&
          url.includes("description_operator=contains")
      )
    ).toBe(true);
    expect(listUrls.some((url) => url.includes("asset_type=SPEC") && url.includes("category=INTEGRATION"))).toBe(true);
    expect(listUrls.some((url) => url.includes("status=DRAFT") && url.includes("tag=MVP0"))).toBe(true);
    expect(
      listUrls.some(
        (url) =>
          url.includes("scope_type=MODULE") &&
          url.includes("module_id=rates") &&
          url.includes("module_id_operator=one_of") &&
          url.includes("macro_object_code=RATE_GEO") &&
          url.includes("macro_object_code_operator=begins_with") &&
          url.includes("otm_table_name=RATE_GEO_COST") &&
          url.includes("otm_table_name_operator=one_of") &&
          url.includes("page_size=25")
      )
    ).toBe(true);
    expect(screen.getByText("Showing 0 of 0 assets")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Reset search" }));
    expect(screen.getByLabelText("Asset name search")).toHaveValue("");
    expect(screen.getByLabelText("Asset name operator")).toHaveValue("contains");
    expect(screen.getByLabelText("Asset description search")).toHaveValue("");
    expect(screen.getByLabelText("Asset description operator")).toHaveValue("contains");
    expect(screen.getByLabelText("Asset type filter")).toHaveValue("");
    expect(screen.getByLabelText("Asset category filter")).toHaveValue("");
    expect(screen.getByLabelText("Asset status filter")).toHaveValue("");
    expect(screen.getByLabelText("Asset tag filter")).toHaveValue("");
    expect(screen.getByLabelText("Asset scope filter")).toHaveValue("");
    expect(screen.getByLabelText("Asset module filter")).toHaveValue("");
    expect(screen.getByLabelText("Asset module operator")).toHaveValue("contains");
    expect(screen.getByLabelText("Asset macro object filter")).toHaveValue("");
    expect(screen.getByLabelText("Asset macro object operator")).toHaveValue("contains");
    expect(screen.getByLabelText("Asset OTM table filter")).toHaveValue("");
    expect(screen.getByLabelText("Asset OTM table operator")).toHaveValue("contains");
    expect(screen.getByLabelText("Asset page size")).toHaveValue("50");
    await waitFor(() => {
      expect(listUrls.at(-1)?.endsWith("/api/v1/modules/assets/assets")).toBe(true);
    });

    await userEvent.click(screen.getByRole("button", { name: /2Create/ }));
    expect(screen.queryByLabelText("Asset classification authoring")).not.toBeInTheDocument();
    await userEvent.clear(screen.getByLabelText("Asset name"));
    await userEvent.type(screen.getByLabelText("Asset name"), "Synthetic Rate Table Notes");
    await userEvent.clear(screen.getByLabelText("Asset description"));
    await userEvent.type(screen.getByLabelText("Asset description"), "Client-safe rate table support asset.");
    await userEvent.selectOptions(screen.getByLabelText("Asset type"), "SPEC");
    await userEvent.selectOptions(screen.getByLabelText("Asset visibility"), "PROJECT");
    await userEvent.selectOptions(screen.getByLabelText("Asset scope"), "MODULE");
    await userEvent.selectOptions(screen.getByLabelText("Asset sensitivity"), "INTERNAL");
    await userEvent.clear(screen.getByLabelText("Asset module id"));
    await userEvent.type(screen.getByLabelText("Asset module id"), "rates");
    await userEvent.clear(screen.getByLabelText("Asset macro object"));
    await userEvent.type(screen.getByLabelText("Asset macro object"), "RATE_RECORD");
    await userEvent.clear(screen.getByLabelText("Asset OTM table"));
    await userEvent.type(screen.getByLabelText("Asset OTM table"), "RATE_GEO_COST");
    await userEvent.clear(screen.getByLabelText("Asset tags"));
    await userEvent.type(screen.getByLabelText("Asset tags"), "SYNTHETIC,RATE");
    await userEvent.click(screen.getByRole("button", { name: "Create asset" }));
    await screen.findByText("Asset Synthetic Rate Table Notes created.");
    expect(screen.getByLabelText("Selected asset", { exact: true })).toHaveTextContent("Synthetic Rate Table Notes");

    await userEvent.click(screen.getByRole("button", { name: /2Create/ }));
    await userEvent.clear(screen.getByLabelText("Asset name"));
    await userEvent.type(screen.getByLabelText("Asset name"), "Synthetic Rate Table Notes Updated");
    await userEvent.clear(screen.getByLabelText("Asset description"));
    await userEvent.type(screen.getByLabelText("Asset description"), "Updated client-safe rate table support asset.");
    await userEvent.clear(screen.getByLabelText("Asset tags"));
    await userEvent.type(screen.getByLabelText("Asset tags"), "SYNTHETIC,RATE,UPDATED");
    await userEvent.click(screen.getByRole("button", { name: "Update asset" }));
    await screen.findByText("Asset Synthetic Rate Table Notes Updated updated.");
    expect(screen.getByLabelText("Selected asset", { exact: true })).toHaveTextContent("Synthetic Rate Table Notes Updated");

    await userEvent.click(screen.getByRole("button", { name: /1Library/ }));
    await userEvent.click(screen.getByRole("button", { name: /Synthetic Reference Template/ }));
    await userEvent.click(screen.getByRole("button", { name: /2Create/ }));
    expect(screen.getByLabelText("Asset name")).toHaveValue("Synthetic Reference Template");
    expect(screen.getByLabelText("Asset description")).toHaveValue("Client-safe selected reference asset.");
    expect(screen.getByLabelText("Asset module id")).toHaveValue("master_data");
    expect(screen.getByLabelText("Asset tags")).toHaveValue("REFERENCE,SYNTHETIC");
    await userEvent.click(screen.getByRole("button", { name: /1Library/ }));
    await userEvent.click(screen.getByRole("button", { name: /Synthetic Rate Table Notes Updated/ }));
    await userEvent.click(screen.getByRole("button", { name: /2Create/ }));
    expect(screen.getByLabelText("Asset name")).toHaveValue("Synthetic Rate Table Notes Updated");

    await userEvent.click(screen.getByRole("button", { name: /3Version/ }));
    const versionFile = new File(["# synthetic mapping spec"], "synthetic_mapping_spec.md", { type: "text/markdown" });
    await userEvent.upload(screen.getByLabelText("Asset version file"), versionFile);
    await userEvent.click(screen.getByRole("button", { name: "Upload version" }));
    await screen.findByText("Asset version synthetic_mapping_spec.md uploaded.");
    expect(screen.getByLabelText("Selected asset versions")).toHaveTextContent("synthetic_mapping_spec.md");

    await userEvent.click(screen.getByRole("button", { name: /4Link/ }));
    expect(screen.getByLabelText("Asset guided link target")).toHaveTextContent("Integration Mapping Studio");
    await userEvent.selectOptions(screen.getByLabelText("Asset link type"), "OTM_TABLE");
    await userEvent.clear(screen.getByLabelText("Asset link target id"));
    await userEvent.type(screen.getByLabelText("Asset link target id"), "NOT_A_REAL_OTM_TABLE");
    await userEvent.clear(screen.getByLabelText("Asset link target label"));
    await userEvent.type(screen.getByLabelText("Asset link target label"), "Invalid OTM table");
    await userEvent.click(screen.getByRole("button", { name: "Create link" }));
    await screen.findByText("ASSET_LINK_INVALID_TABLE: OTM table not found in Data Dictionary.");
    expect(screen.getByLabelText("Assets Library workflow")).toHaveTextContent("4Link");
    expect(linkRequests).toEqual([]);
    await userEvent.clear(screen.getByLabelText("Asset link target id"));
    await userEvent.type(screen.getByLabelText("Asset link target id"), "RATE_GEO");
    await screen.findByRole("option", { name: "RATE_GEO_COST" });
    await userEvent.selectOptions(screen.getByLabelText("Asset guided link target"), "RATE_GEO_COST");
    await userEvent.click(screen.getByRole("button", { name: "Create link" }));
    await screen.findByText("Asset link RATE_GEO_COST created.");
    expect(screen.getByLabelText("Selected asset links")).toHaveTextContent("RATE_GEO_COST table");

    await userEvent.click(screen.getByRole("button", { name: /4Link/ }));
    await userEvent.selectOptions(screen.getByLabelText("Asset link type"), "MACRO_OBJECT");
    expect(screen.getByLabelText("Asset guided link target")).toHaveTextContent("Rate Record");
    await userEvent.clear(screen.getByLabelText("Asset link target id"));
    await userEvent.type(screen.getByLabelText("Asset link target id"), "NOT_A_MACRO_OBJECT");
    await userEvent.clear(screen.getByLabelText("Asset link target label"));
    await userEvent.type(screen.getByLabelText("Asset link target label"), "Invalid macro object");
    await userEvent.click(screen.getByRole("button", { name: "Create link" }));
    await screen.findByText("ASSET_LINK_INVALID_MACRO_OBJECT: OTM macro object not found in Catalog Core.");
    await userEvent.selectOptions(screen.getByLabelText("Asset guided link target"), "RATE_RECORD");
    await userEvent.click(screen.getByRole("button", { name: "Create link" }));
    await screen.findByText("Asset link RATE_RECORD created.");
    expect(screen.getByLabelText("Selected asset links")).toHaveTextContent("Rate Record macro object");

    await userEvent.click(screen.getByRole("button", { name: /4Link/ }));
    await userEvent.selectOptions(screen.getByLabelText("Asset link type"), "ARTIFACT");
    await userEvent.type(screen.getByLabelText("Evidence target source module filter"), "integration_mapping");
    await userEvent.type(screen.getByLabelText("Evidence target type filter"), "integration_mapping_spec");
    await userEvent.click(screen.getByRole("button", { name: "Apply evidence target filters" }));
    expect(
      evidenceUrls.some(
        (url) =>
          url.includes("client_safe=true") &&
          url.includes("source_module=integration_mapping") &&
          url.includes("evidence_type=integration_mapping_spec")
      )
    ).toBe(true);
    await userEvent.click(screen.getByRole("button", { name: "Reset evidence target filters" }));
    expect(screen.getByLabelText("Evidence target source module filter")).toHaveValue("");
    expect(screen.getByLabelText("Evidence target type filter")).toHaveValue("");
    expect(screen.getByLabelText("Evidence target status filter")).toHaveValue("");
    expect(screen.getByLabelText("Evidence target artifact id filter")).toHaveValue("");
    expect(evidenceUrls.at(-1)).toContain("client_safe=true");
    expect(evidenceUrls.at(-1)).not.toContain("source_module=integration_mapping");
    await userEvent.type(screen.getByLabelText("Evidence target source module filter"), "integration_mapping");
    await userEvent.type(screen.getByLabelText("Evidence target type filter"), "integration_mapping_spec");
    await userEvent.click(screen.getByRole("button", { name: "Apply evidence target filters" }));
    expect(screen.getByLabelText("Asset guided link target")).toHaveTextContent("synthetic_mapping_spec.md");
    await userEvent.selectOptions(screen.getByLabelText("Asset guided link target"), "artifact_qa_1");
    await userEvent.click(screen.getByRole("button", { name: "Create link" }));
    await screen.findByText("Asset link artifact_qa_1 created.");
    expect(screen.getByLabelText("Selected asset links")).toHaveTextContent("synthetic_mapping_spec.md");

    await userEvent.click(screen.getByRole("button", { name: /4Link/ }));
    await userEvent.selectOptions(screen.getByLabelText("Asset link type"), "EVIDENCE");
    expect(screen.getByLabelText("Asset guided link target")).toHaveTextContent("integration_mapping_spec");
    await userEvent.selectOptions(screen.getByLabelText("Asset guided link target"), "evidence_qa_1");
    await userEvent.click(screen.getByRole("button", { name: "Create link" }));
    await screen.findByText("Asset link evidence_qa_1 created.");
    expect(screen.getByLabelText("Selected asset links")).toHaveTextContent("integration_mapping_spec evidence");

    await userEvent.click(screen.getByRole("button", { name: /5Lifecycle/ }));
    await userEvent.click(screen.getByRole("button", { name: "Download current version" }));
    await screen.findByText("Download started: synthetic_mapping_spec.md.");

    await userEvent.click(screen.getByRole("button", { name: "Archive asset" }));
    await screen.findByText("Asset Synthetic Rate Table Notes Updated archived.");
    expect(screen.getByLabelText("Selected asset", { exact: true })).toHaveTextContent("ARCHIVED");
    await userEvent.click(screen.getByRole("button", { name: /3Version/ }));
    expect(screen.getByRole("button", { name: "Upload version" })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: /4Link/ }));
    expect(screen.getByRole("button", { name: "Create link" })).toBeDisabled();

    await userEvent.click(screen.getByRole("button", { name: /1Library/ }));
    await userEvent.click(screen.getByRole("button", { name: /Synthetic Reference Template/ }));
    expect(screen.queryByText("Asset Synthetic Rate Table Notes Updated archived.")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Selected asset", { exact: true })).toHaveTextContent("Synthetic Reference Template");
    await userEvent.click(screen.getByRole("button", { name: /3Version/ }));
    expect(screen.getByLabelText("Asset version file")).not.toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: /4Link/ }));
    expect(screen.getByRole("button", { name: "Create link" })).toBeEnabled();

    await userEvent.click(screen.getByRole("link", { name: /Project Cockpit/ }));
    await userEvent.click(
      within(screen.getByRole("navigation", { name: "Workbench modules" })).getByRole("link", {
        name: /Assets Library/
      })
    );
    await screen.findByRole("heading", { name: "Assets Library" });
    await userEvent.click(screen.getByRole("link", { name: "Open library" }));
    expect(await screen.findByLabelText("Assets")).toHaveTextContent("Synthetic Rate Table Notes Updated");

    expect(createRequests).toEqual([
      {
        asset_type: "SPEC",
        category: "INTEGRATION",
        description: "Client-safe rate table support asset.",
        macro_object_code: "RATE_RECORD",
        module_id: "rates",
        name: "Synthetic Rate Table Notes",
        otm_table_name: "RATE_GEO_COST",
        scope_type: "MODULE",
        sensitivity: "INTERNAL",
        tags: ["SYNTHETIC", "RATE"],
        visibility: "PROJECT"
      }
    ]);
    expect(uploadRequests).toEqual([{ method: "POST" }]);
    expect(classificationRequests).toEqual([]);
    expect(invalidLinkRequests).toEqual([
      { link_type: "OTM_TABLE", target_id: "NOT_A_REAL_OTM_TABLE", target_label: "Invalid OTM table" }
    ]);
    expect(invalidMacroLinkRequests).toEqual([
      { link_type: "MACRO_OBJECT", target_id: "NOT_A_MACRO_OBJECT", target_label: "Invalid macro object" }
    ]);
    expect(updateRequests).toEqual([
      {
        asset_type: "SPEC",
        category: "INTEGRATION",
        description: "Updated client-safe rate table support asset.",
        macro_object_code: "RATE_RECORD",
        module_id: "rates",
        name: "Synthetic Rate Table Notes Updated",
        otm_table_name: "RATE_GEO_COST",
        scope_type: "MODULE",
        sensitivity: "INTERNAL",
        tags: ["SYNTHETIC", "RATE", "UPDATED"],
        visibility: "PROJECT"
      }
    ]);
    expect(linkRequests).toEqual([
      { link_type: "OTM_TABLE", target_id: "RATE_GEO_COST", target_label: "RATE_GEO_COST table" },
      { link_type: "MACRO_OBJECT", target_id: "RATE_RECORD", target_label: "Rate Record macro object" },
      { link_type: "ARTIFACT", target_id: "artifact_qa_1", target_label: "synthetic_mapping_spec.md" },
      { link_type: "EVIDENCE", target_id: "evidence_qa_1", target_label: "integration_mapping_spec evidence" }
    ]);
    expect(downloadRequests).toEqual([{ method: "GET" }]);
    expect(archiveRequests).toEqual([{ method: "POST" }]);
    expect(within(screen.getByLabelText("Selected asset links")).getAllByText("EVIDENCE").length).toBeGreaterThan(0);
  }, 60000);
});
