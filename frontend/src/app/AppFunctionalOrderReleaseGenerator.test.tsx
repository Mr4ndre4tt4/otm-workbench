import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "../platform/auth";

function renderFunctionalApp(initialPath = "/order-release-generator") {
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

function downloadResponse(body: string, filename: string, contentType = "application/xml") {
  return new Response(new Blob([body], { type: contentType }), {
    headers: { "Content-Disposition": `attachment; filename="${filename}"` },
    status: 200
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

function orderReleaseTemplate() {
  return {
    code: "SYN_TL_ORDER_RELEASE",
    created_at: "2026-05-22T00:00:00",
    created_by: "system",
    defaults: { weight_uom: "KG" },
    description: "Client-safe synthetic template for Order Release XML generation.",
    id: "template_or_tl",
    macro_object_code: "ORDER_RELEASE",
    name: "Synthetic TL Order Release",
    optional_columns: ["weight_uom"],
    required_columns: [
      "release_gid",
      "source_location_gid",
      "destination_location_gid",
      "early_pickup_date",
      "late_delivery_date",
      "item_gid",
      "packaged_item_gid",
      "weight"
    ],
    status: "ACTIVE",
    updated_at: null,
    version: 1
  };
}

function validBatch() {
  return {
    created_at: "2026-05-22T00:00:00",
    created_by: "admin@example.test",
    file_name: "synthetic_or_rows.json",
    id: "or_batch_1",
    issue_count: 0,
    release_count: 2,
    row_count: 3,
    rows: [
      {
        batch_id: "or_batch_1",
        created_at: "2026-05-22T00:00:00",
        id: "or_row_1",
        issues: [],
        normalized_json: { release_gid: "OTM1.OR_SYN_001", weight_uom: "KG" },
        release_gid: "OTM1.OR_SYN_001",
        row_number: 1,
        status: "VALID",
        updated_at: null
      }
    ],
    status: "VALID",
    summary: { issue_count: 0, release_count: 2, row_count: 3, template_code: "SYN_TL_ORDER_RELEASE" },
    template_id: "template_or_tl",
    updated_at: null
  };
}

function invalidBatch() {
  return {
    ...validBatch(),
    id: "or_batch_invalid",
    issue_count: 1,
    release_count: 1,
    rows: [
      {
        batch_id: "or_batch_invalid",
        created_at: "2026-05-22T00:00:00",
        id: "or_row_invalid_1",
        issues: [{ code: "MISSING_REQUIRED_COLUMN", column: "release_gid", severity: "ERROR" }],
        normalized_json: { weight: "100", weight_uom: "KG" },
        release_gid: null,
        row_number: 1,
        status: "INVALID",
        updated_at: null
      },
      {
        batch_id: "or_batch_invalid",
        created_at: "2026-05-22T00:00:00",
        id: "or_row_invalid_2",
        issues: [],
        normalized_json: { release_gid: "OTM1.OR_SYN_002", weight_uom: "KG" },
        release_gid: "OTM1.OR_SYN_002",
        row_number: 2,
        status: "VALID",
        updated_at: null
      }
    ],
    status: "INVALID",
    summary: { issue_count: 1, release_count: 1, row_count: 2, template_code: "SYN_TL_ORDER_RELEASE" }
  };
}

describe("Functional Order Release Generator journey", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
  });

  it("creates a batch, previews XML, generates an artifact, verifies submit guard, and returns with backend state", async () => {
    const createBatchRequests: unknown[] = [];
    const previewRequests: unknown[] = [];
    const artifactRequests: unknown[] = [];
    const downloadRequests: unknown[] = [];
    const submitRequests: unknown[] = [];
    let batchCreated = false;
    let artifactGenerated = false;
    const createObjectURL = vi.fn(() => "blob:order-release-xml");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { ...URL, createObjectURL, revokeObjectURL });

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
              {
                id: "order_release_generator",
                label: "Order Release Generator",
                path: "/order-release-generator",
                status: "ACTIVE"
              }
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
      if (url.endsWith("/api/v1/modules/order-release-generator/templates")) {
        return Promise.resolve(jsonResponse({ items: [orderReleaseTemplate()], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/order-release-generator/batches")) {
        if (init?.method === "POST") {
          expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
          const body = JSON.parse(String(init?.body));
          createBatchRequests.push({
            file_name: body.file_name,
            first_release_gid: body.rows[0].release_gid,
            first_weight: body.rows[0].weight,
            row_count: body.rows.length,
            template_id: body.template_id
          });
          batchCreated = true;
          return Promise.resolve(jsonResponse(validBatch()));
        }
        return Promise.resolve(jsonResponse({ items: batchCreated ? [validBatch()] : [], total: batchCreated ? 1 : 0 }));
      }
      if (url.endsWith("/api/v1/modules/order-release-generator/batches/or_batch_1/preview-xml")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        previewRequests.push({ method: init?.method });
        return Promise.resolve(
          jsonResponse({
            batch_id: "or_batch_1",
            job_id: "job_preview_1",
            line_count: 3,
            release_count: 2,
            xml: "<Transmission><TransmissionBody><GLogXMLElement /></TransmissionBody></Transmission>"
          })
        );
      }
      if (url.endsWith("/api/v1/modules/order-release-generator/batches/or_batch_1/generate-xml-artifact")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        artifactRequests.push({ method: init?.method });
        artifactGenerated = true;
        return Promise.resolve(
          jsonResponse({
            artifact_id: "artifact_or_xml",
            batch_id: "or_batch_1",
            content_type: "application/xml",
            download_url: "/api/v1/modules/order-release-generator/batches/or_batch_1/artifacts/artifact_or_xml/download",
            evidence_id: "evidence_or_xml",
            file_name: "or_batch_1.db.xml",
            job_id: "job_artifact_1",
            line_count: 3,
            release_count: 2,
            sha256: "abc123",
            size_bytes: 512,
            status: "GENERATED"
          })
        );
      }
      if (url.endsWith("/api/v1/modules/order-release-generator/batches/or_batch_1/artifacts")) {
        return Promise.resolve(
          jsonResponse({
            batch_id: "or_batch_1",
            items: artifactGenerated
              ? [
                  {
                    artifact_type: "order_release_xml",
                    batch_id: "or_batch_1",
                    content_type: "application/xml",
                    download_url: "/api/v1/modules/order-release-generator/batches/or_batch_1/artifacts/artifact_or_xml/download",
                    file_name: "or_batch_1.db.xml",
                    id: "artifact_or_xml",
                    sensitivity_level: "internal",
                    sha256: "abc123",
                    size_bytes: 512,
                    source_module: "order_release_generator"
                  }
                ]
              : [],
            total: artifactGenerated ? 1 : 0
          })
        );
      }
      if (url.endsWith("/api/v1/modules/order-release-generator/batches/or_batch_1/artifacts/artifact_or_xml/download")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        downloadRequests.push({ method: init?.method ?? "GET" });
        return Promise.resolve(downloadResponse("<Transmission />", "or_batch_1.db.xml"));
      }
      if (url.endsWith("/api/v1/modules/order-release-generator/batches/or_batch_1/submit-otm")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        submitRequests.push({ method: init?.method });
        return Promise.resolve(
          jsonResponse(
            {
              code: "ORDER_RELEASE_OTM_SUBMIT_DISABLED",
              details: {
                batch_id: "or_batch_1",
                reason: "MVP0 has no governed OTM connection/capability for direct submit.",
                required_capability: "order_release_generator.submit_otm"
              },
              message: "Direct OTM submission is disabled in MVP0."
            },
            409
          )
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp();
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Order Release Generator" });
    expect(screen.getByLabelText("Order Release templates")).toHaveTextContent("SYN_TL_ORDER_RELEASE");

    await userEvent.click(screen.getByRole("button", { name: /2Batch/ }));
    expect(screen.getByLabelText("Order Release row editor")).toHaveTextContent("release_gid");
    expect(screen.queryByLabelText("Batch rows JSON")).not.toBeInTheDocument();
    await userEvent.clear(screen.getByLabelText("Row 1 weight"));
    await userEvent.type(screen.getByLabelText("Row 1 weight"), "125");
    await userEvent.click(screen.getByRole("button", { name: "Reset rows" }));
    await screen.findByText("Order Release rows reset from the selected template.");
    expect(screen.getByLabelText("Order Release row editor")).toHaveTextContent("Row 1");
    expect(screen.getByLabelText("Order Release row editor")).not.toHaveTextContent("Row 2");
    expect(screen.getByLabelText("Row 1 weight_uom")).toHaveValue("KG");
    await userEvent.clear(screen.getByLabelText("Row 1 release_gid"));
    await userEvent.type(screen.getByLabelText("Row 1 release_gid"), "OTM1.OR_SYN_001");
    await userEvent.clear(screen.getByLabelText("Row 1 source_location_gid"));
    await userEvent.type(screen.getByLabelText("Row 1 source_location_gid"), "OTM1.SOURCE_A");
    await userEvent.clear(screen.getByLabelText("Row 1 destination_location_gid"));
    await userEvent.type(screen.getByLabelText("Row 1 destination_location_gid"), "OTM1.DEST_A");
    await userEvent.clear(screen.getByLabelText("Row 1 early_pickup_date"));
    await userEvent.type(screen.getByLabelText("Row 1 early_pickup_date"), "2026-05-20 08:00:00");
    await userEvent.clear(screen.getByLabelText("Row 1 late_delivery_date"));
    await userEvent.type(screen.getByLabelText("Row 1 late_delivery_date"), "2026-05-21 17:00:00");
    await userEvent.clear(screen.getByLabelText("Row 1 item_gid"));
    await userEvent.type(screen.getByLabelText("Row 1 item_gid"), "OTM1.ITEM_A");
    await userEvent.clear(screen.getByLabelText("Row 1 packaged_item_gid"));
    await userEvent.type(screen.getByLabelText("Row 1 packaged_item_gid"), "OTM1.PACK_A");
    await userEvent.clear(screen.getByLabelText("Row 1 weight"));
    await userEvent.type(screen.getByLabelText("Row 1 weight"), "125");
    await userEvent.click(screen.getByRole("button", { name: "Create batch" }));
    await screen.findByText("Order Release batch or_batch_1 created.");
    expect(screen.getByLabelText("Active Order Release batch")).toHaveTextContent("VALID");

    await userEvent.click(screen.getByRole("button", { name: /3Preview/ }));
    await userEvent.click(screen.getByRole("button", { name: "Preview XML" }));
    await screen.findByText("Order Release XML preview generated.");
    expect(screen.getByLabelText("Order Release XML preview")).toHaveTextContent("Transmission");

    await userEvent.click(screen.getByRole("button", { name: /4Artifact/ }));
    await userEvent.click(screen.getByRole("button", { name: "Generate XML artifact" }));
    await screen.findByText("Order Release XML artifact artifact_or_xml generated.");
    expect(screen.getByLabelText("Order Release XML artifact")).toHaveTextContent("or_batch_1.db.xml");
    await userEvent.click(screen.getByRole("button", { name: "Download" }));
    await screen.findByText("Order Release artifact or_batch_1.db.xml downloaded.");

    await userEvent.click(screen.getByRole("button", { name: /5Submit/ }));
    await userEvent.click(screen.getByRole("button", { name: "Verify OTM submit guard" }));
    await screen.findByText("Direct OTM submission is disabled in MVP0.");
    expect(screen.getByLabelText("OTM submit guard")).toHaveTextContent("order_release_generator.submit_otm");

    await userEvent.click(screen.getByRole("link", { name: /Project Cockpit/ }));
    await userEvent.click(screen.getByRole("link", { name: /Order Release Generator/ }));
    await screen.findByRole("heading", { name: "Order Release Generator" });
    expect(await screen.findByLabelText("Recent Order Release batches")).toHaveTextContent("or_batch_1");

    expect(createBatchRequests).toEqual([
      {
        file_name: "synthetic_order_release_rows.json",
        first_release_gid: "OTM1.OR_SYN_001",
        first_weight: "125",
        row_count: 1,
        template_id: "template_or_tl"
      }
    ]);
    expect(previewRequests).toEqual([{ method: "POST" }]);
    expect(artifactRequests).toEqual([{ method: "POST" }]);
    expect(downloadRequests).toEqual([{ method: "GET" }]);
    expect(createObjectURL).toHaveBeenCalledOnce();
    expect(submitRequests).toEqual([{ method: "POST" }]);
  }, 60000);

  it("shows invalid batch row issues and lets the user correct and recreate the batch", async () => {
    const createBatchRequests: unknown[] = [];
    let createAttempt = 0;
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
              {
                id: "order_release_generator",
                label: "Order Release Generator",
                path: "/order-release-generator",
                status: "ACTIVE"
              }
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
      if (url.endsWith("/api/v1/modules/order-release-generator/templates")) {
        return Promise.resolve(jsonResponse({ items: [orderReleaseTemplate()], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/order-release-generator/batches")) {
        if (init?.method === "POST") {
          const body = JSON.parse(String(init?.body));
          createAttempt += 1;
          createBatchRequests.push({ attempt: createAttempt, release_gid: body.rows[0].release_gid ?? null });
          return Promise.resolve(jsonResponse(createAttempt === 1 ? invalidBatch() : validBatch()));
        }
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/order-release-generator/batches/or_batch_invalid/artifacts")) {
        return Promise.resolve(jsonResponse({ batch_id: "or_batch_invalid", items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/order-release-generator/batches/or_batch_1/artifacts")) {
        return Promise.resolve(jsonResponse({ batch_id: "or_batch_1", items: [], total: 0 }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp();
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Order Release Generator" });
    await userEvent.click(screen.getByRole("button", { name: /2Batch/ }));
    await userEvent.clear(screen.getByLabelText("Row 1 release_gid"));
    await userEvent.click(screen.getByRole("button", { name: "Create batch" }));

    await screen.findByText("Order Release batch or_batch_invalid created.");
    expect(screen.getByLabelText("Order Release batch row issues")).toHaveTextContent("MISSING_REQUIRED_COLUMN");
    expect(screen.getByLabelText("Order Release batch row issues")).toHaveTextContent("release_gid");

    await userEvent.type(screen.getByLabelText("Row 1 release_gid"), "OTM1.OR_SYN_001");
    await userEvent.click(screen.getByRole("button", { name: "Create batch" }));
    await screen.findByText("Order Release batch or_batch_1 created.");

    expect(createBatchRequests).toEqual([
      { attempt: 1, release_gid: null },
      { attempt: 2, release_gid: "OTM1.OR_SYN_001" }
    ]);
  }, 60000);

  it("creates a backend-owned custom template from the Templates stage", async () => {
    const createTemplateRequests: unknown[] = [];
    const createVersionRequests: unknown[] = [];
    let templates = [orderReleaseTemplate()];
    const customTemplate = {
      ...orderReleaseTemplate(),
      code: "TL_OR_CUSTOM_MVP0",
      created_by: "admin@example.test",
      description: "Synthetic custom template.",
      id: "template_or_custom",
      name: "Custom TL Order Release",
      optional_columns: ["remarks"],
      required_columns: ["release_gid", "source_location_gid", "destination_location_gid"],
      version: 1
    };
    const customTemplateV2 = {
      ...customTemplate,
      id: "template_or_custom_v2",
      name: "Custom TL Order Release v2",
      optional_columns: ["remarks", "weight_uom"],
      required_columns: ["release_gid", "source_location_gid", "destination_location_gid", "weight"],
      version: 2
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
              {
                id: "order_release_generator",
                label: "Order Release Generator",
                path: "/order-release-generator",
                status: "ACTIVE"
              }
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
      if (url.endsWith("/api/v1/modules/order-release-generator/templates")) {
        if (init?.method === "POST") {
          expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
          const body = JSON.parse(String(init?.body));
          createTemplateRequests.push(body);
          templates = [orderReleaseTemplate(), customTemplate];
          return Promise.resolve(jsonResponse(customTemplate));
        }
        return Promise.resolve(jsonResponse({ items: templates, total: templates.length }));
      }
      if (url.endsWith("/api/v1/modules/order-release-generator/templates/template_or_custom/versions")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init?.body));
        createVersionRequests.push(body);
        templates = [orderReleaseTemplate(), customTemplateV2, customTemplate];
        return Promise.resolve(jsonResponse(customTemplateV2));
      }
      if (url.endsWith("/api/v1/modules/order-release-generator/batches")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp();
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Order Release Generator" });
    await userEvent.click(screen.getByRole("button", { name: /1Templates/ }));
    await userEvent.type(screen.getByLabelText("Template code"), "TL_OR_CUSTOM_MVP0");
    await userEvent.type(screen.getByLabelText("Template name"), "Custom TL Order Release");
    await userEvent.type(screen.getByLabelText("Required columns"), "release_gid, source_location_gid, destination_location_gid");
    await userEvent.type(screen.getByLabelText("Optional columns"), "remarks");
    await userEvent.type(screen.getByLabelText("Default values"), "domain_name=OTM1\ntransport_mode=TL");
    await userEvent.click(screen.getByRole("button", { name: "Create template" }));

    await screen.findByText("Order Release template TL_OR_CUSTOM_MVP0 created.");
    expect(screen.getByLabelText("Order Release templates")).toHaveTextContent("TL_OR_CUSTOM_MVP0");
    await userEvent.type(screen.getByLabelText("Version name"), "Custom TL Order Release v2");
    await userEvent.type(screen.getByLabelText("Version required columns"), "release_gid, source_location_gid, destination_location_gid, weight");
    await userEvent.type(screen.getByLabelText("Version optional columns"), "remarks, weight_uom");
    await userEvent.type(screen.getByLabelText("Version default values"), "domain_name=OTM1\nweight_uom=KG");
    await userEvent.click(screen.getByRole("button", { name: "Create version" }));

    await screen.findByText("Order Release template TL_OR_CUSTOM_MVP0 v2 created.");
    expect(screen.getByLabelText("Selected Order Release template")).toHaveTextContent("Version");
    expect(screen.getByLabelText("Selected Order Release template")).toHaveTextContent("2");
    expect(createTemplateRequests).toEqual([
      {
        code: "TL_OR_CUSTOM_MVP0",
        defaults: { domain_name: "OTM1", transport_mode: "TL" },
        description: "",
        name: "Custom TL Order Release",
        optional_columns: ["remarks"],
        required_columns: ["release_gid", "source_location_gid", "destination_location_gid"]
      }
    ]);
    expect(createVersionRequests).toEqual([
      {
        defaults: { domain_name: "OTM1", weight_uom: "KG" },
        description: "",
        name: "Custom TL Order Release v2",
        optional_columns: ["remarks", "weight_uom"],
        required_columns: ["release_gid", "source_location_gid", "destination_location_gid", "weight"]
      }
    ]);
  }, 60000);
});
