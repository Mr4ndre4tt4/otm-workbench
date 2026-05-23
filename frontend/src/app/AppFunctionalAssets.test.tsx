import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "../platform/auth";

function renderFunctionalApp(initialPath = "/assets") {
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
  return {
    active_context: {},
    available_actions: [],
    counts: { recent_artifacts: 0, recent_evidence: 0, recent_jobs: 0 },
    description: "Project-level operational overview.",
    module_id: "home",
    module_summary: { counts_by_status: { ACTIVE: 2 }, items: [], total: 2 },
    recent_artifacts: [],
    recent_evidence: [],
    recent_jobs: [],
    setup_status: {
      active_context_selected: true,
      environment_count: 1,
      missing_requirements: [],
      profile_count: 1,
      status: "READY"
    },
    status: "ready",
    title: "Project Cockpit"
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

function classificationGroups() {
  return {
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
          }
        ],
        total: 3
      }
    ],
    total: 4
  };
}

describe("Functional Assets Library journey", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
  });

  it("creates an asset, uploads a version, links it, downloads it, archives it, and returns with backend state", async () => {
    const createRequests: unknown[] = [];
    const updateRequests: unknown[] = [];
    const uploadRequests: unknown[] = [];
    const invalidLinkRequests: unknown[] = [];
    const invalidMacroLinkRequests: unknown[] = [];
    const linkRequests: unknown[] = [];
    const downloadRequests: unknown[] = [];
    const archiveRequests: unknown[] = [];
    const listUrls: string[] = [];
    let createdAsset: ReturnType<typeof assetFixture> | null = null;
    const referenceAsset = referenceAssetFixture();
    let uploadedVersion: ReturnType<typeof versionFixture> | null = null;
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
      if (url.endsWith("/api/v1/modules/assets/classifications")) {
        return Promise.resolve(jsonResponse(classificationGroups()));
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

    await userEvent.selectOptions(screen.getByLabelText("Asset type filter"), "SPEC");
    await userEvent.selectOptions(screen.getByLabelText("Asset category filter"), "INTEGRATION");
    await userEvent.selectOptions(screen.getByLabelText("Asset status filter"), "DRAFT");
    await userEvent.type(screen.getByLabelText("Asset tag filter"), "MVP0");
    await userEvent.selectOptions(screen.getByLabelText("Asset scope filter"), "MODULE");
    await userEvent.type(screen.getByLabelText("Asset module filter"), "rates");
    await userEvent.type(screen.getByLabelText("Asset macro object filter"), "RATE_GEO");
    await userEvent.type(screen.getByLabelText("Asset OTM table filter"), "RATE_GEO_COST");
    await userEvent.click(screen.getByRole("button", { name: "Apply asset filters" }));
    expect(listUrls.some((url) => url.includes("asset_type=SPEC") && url.includes("category=INTEGRATION"))).toBe(true);
    expect(listUrls.some((url) => url.includes("status=DRAFT") && url.includes("tag=MVP0"))).toBe(true);
    expect(
      listUrls.some(
        (url) =>
          url.includes("scope_type=MODULE") &&
          url.includes("module_id=rates") &&
          url.includes("macro_object_code=RATE_GEO") &&
          url.includes("otm_table_name=RATE_GEO_COST")
      )
    ).toBe(true);

    await userEvent.click(screen.getByRole("button", { name: /2Create/ }));
    await userEvent.clear(screen.getByLabelText("Asset name"));
    await userEvent.type(screen.getByLabelText("Asset name"), "Synthetic Rate Table Notes");
    await userEvent.clear(screen.getByLabelText("Asset description"));
    await userEvent.type(screen.getByLabelText("Asset description"), "Client-safe rate table support asset.");
    await userEvent.selectOptions(screen.getByLabelText("Asset type"), "SPEC");
    await userEvent.selectOptions(screen.getByLabelText("Asset category"), "INTEGRATION");
    await userEvent.selectOptions(screen.getByLabelText("Asset visibility"), "PROJECT");
    await userEvent.selectOptions(screen.getByLabelText("Asset scope"), "MODULE");
    await userEvent.selectOptions(screen.getByLabelText("Asset sensitivity"), "INTERNAL");
    await userEvent.clear(screen.getByLabelText("Asset module id"));
    await userEvent.type(screen.getByLabelText("Asset module id"), "rates");
    await userEvent.clear(screen.getByLabelText("Asset macro object"));
    await userEvent.type(screen.getByLabelText("Asset macro object"), "RATE_GEO");
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
    await userEvent.type(screen.getByLabelText("Asset link target id"), "RATE_GEO_COST");
    await userEvent.clear(screen.getByLabelText("Asset link target label"));
    await userEvent.type(screen.getByLabelText("Asset link target label"), "Rate Geo Cost table");
    await userEvent.click(screen.getByRole("button", { name: "Create link" }));
    await screen.findByText("Asset link RATE_GEO_COST created.");
    expect(screen.getByLabelText("Selected asset links")).toHaveTextContent("Rate Geo Cost table");

    await userEvent.click(screen.getByRole("button", { name: /4Link/ }));
    await userEvent.selectOptions(screen.getByLabelText("Asset link type"), "MACRO_OBJECT");
    await userEvent.clear(screen.getByLabelText("Asset link target id"));
    await userEvent.type(screen.getByLabelText("Asset link target id"), "NOT_A_MACRO_OBJECT");
    await userEvent.clear(screen.getByLabelText("Asset link target label"));
    await userEvent.type(screen.getByLabelText("Asset link target label"), "Invalid macro object");
    await userEvent.click(screen.getByRole("button", { name: "Create link" }));
    await screen.findByText("ASSET_LINK_INVALID_MACRO_OBJECT: OTM macro object not found in Catalog Core.");
    await userEvent.clear(screen.getByLabelText("Asset link target id"));
    await userEvent.type(screen.getByLabelText("Asset link target id"), "RATE_RECORD");
    await userEvent.clear(screen.getByLabelText("Asset link target label"));
    await userEvent.type(screen.getByLabelText("Asset link target label"), "Rate Record macro object");
    await userEvent.click(screen.getByRole("button", { name: "Create link" }));
    await screen.findByText("Asset link RATE_RECORD created.");
    expect(screen.getByLabelText("Selected asset links")).toHaveTextContent("Rate Record macro object");

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

    await userEvent.click(screen.getByRole("link", { name: /Project Cockpit/ }));
    await userEvent.click(screen.getByRole("link", { name: /Assets Library/ }));
    await screen.findByRole("heading", { name: "Assets Library" });
    expect(await screen.findByLabelText("Assets")).toHaveTextContent("Synthetic Rate Table Notes Updated");

    expect(createRequests).toEqual([
      {
        asset_type: "SPEC",
        category: "INTEGRATION",
        description: "Client-safe rate table support asset.",
        macro_object_code: "RATE_GEO",
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
        macro_object_code: "RATE_GEO",
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
      { link_type: "OTM_TABLE", target_id: "RATE_GEO_COST", target_label: "Rate Geo Cost table" },
      { link_type: "MACRO_OBJECT", target_id: "RATE_RECORD", target_label: "Rate Record macro object" }
    ]);
    expect(downloadRequests).toEqual([{ method: "GET" }]);
    expect(archiveRequests).toEqual([{ method: "POST" }]);
    expect(within(screen.getByLabelText("Selected asset links")).getAllByText("MACRO_OBJECT").length).toBeGreaterThan(0);
  }, 60000);
});
