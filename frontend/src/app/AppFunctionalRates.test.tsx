import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "../platform/auth";

function renderFunctionalApp(initialPath = "/rates") {
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

function ratesSummary() {
  return {
    module_id: "rates",
    status: "ok",
    title: "Rates Studio",
    description: "Prepare, validate, approve and export OTM rates packages.",
    primary_object: "rate_batch",
    counts: [
      { key: "total", label: "Total", value: 2, severity: "neutral" },
      { key: "ready_for_approval", label: "Ready for approval", value: 1, severity: "success" },
      { key: "blocked", label: "Blocked", value: 1, severity: "warning" }
    ],
    recent_objects: [
      {
        id: "batch_ready",
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
        id: "batch_blocked",
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
        object_id: "batch_blocked",
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
  };
}

function ratesSummaryWithCreatedBatch() {
  return {
    ...ratesSummary(),
    counts: [
      { key: "total", label: "Total", value: 3, severity: "neutral" },
      { key: "ready_for_approval", label: "Ready for approval", value: 1, severity: "success" },
      { key: "blocked", label: "Blocked", value: 1, severity: "warning" }
    ],
    recent_objects: [
      {
        id: "batch_created",
        code: "RATE_GEO_ONLY",
        display_name: "Synthetic new rate package",
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
        badges: [],
        available_actions: []
      },
      ...ratesSummary().recent_objects
    ]
  };
}

function readyBatchDetail() {
  return {
    id: "batch_ready",
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
        id: "table_ready",
        batch_id: "batch_ready",
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
        href: "/api/v1/modules/rates/batches/batch_ready/approve",
        variant: "primary",
        icon_key: "check",
        disabled: false,
        disabled_reason: null,
        requires_confirmation: true
      }
    ]
  };
}

function approvedBatchDetail() {
  return {
    ...readyBatchDetail(),
    status: "APPROVED",
    available_actions: [
      {
        key: "validate",
        label: "Validate",
        method: "POST",
        href: "/api/v1/modules/rates/batches/batch_ready/validate",
        variant: "secondary",
        icon_key: "check-circle",
        disabled: true,
        disabled_reason: "ALREADY_APPROVED",
        requires_confirmation: false,
        result_hint: "refresh_object"
      },
      {
        key: "approve",
        label: "Approve",
        method: "POST",
        href: "/api/v1/modules/rates/batches/batch_ready/approve",
        variant: "primary",
        icon_key: "badge-check",
        disabled: true,
        disabled_reason: "ALREADY_APPROVED",
        requires_confirmation: true,
        result_hint: "refresh_object"
      }
    ]
  };
}

function blockedBatchDetail() {
  return {
    id: "batch_blocked",
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
        href: "/api/v1/modules/rates/batches/batch_blocked/validate",
        variant: "primary",
        icon_key: "check",
        disabled: false,
        disabled_reason: null,
        requires_confirmation: false,
        result_hint: "refresh_object"
      }
    ]
  };
}

function createdBatchDetail() {
  return {
    id: "batch_created",
    project_id: null,
    environment_id: null,
    profile_id: null,
    scenario_code: "RATE_GEO_ONLY",
    catalog_macro_object_code: "RATE_RECORD",
    catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
    name: "Synthetic new rate package",
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
        href: "/api/v1/modules/rates/batches/batch_created/validate",
        variant: "primary",
        icon_key: "check",
        disabled: false,
        disabled_reason: null,
        requires_confirmation: false,
        result_hint: "refresh_object"
      }
    ]
  };
}

function createdBatchDetailWithTable() {
  return {
    ...createdBatchDetail(),
    tables: [
      {
        id: "table_created",
        batch_id: "batch_created",
        table_name: "X_LANE",
        sequence_index: 1,
        requirement_level: "REQUIRED",
        row_count: 1,
        status: "PENDING"
      }
    ]
  };
}

describe("Functional Rates journey", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("loads a rate batch, downloads evidence artifacts, and executes backend validation", async () => {
    const createObjectURL = vi.fn(() => "blob:synthetic-rates-export");
    const revokeObjectURL = vi.fn();
    const anchorClick = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    vi.stubGlobal("URL", { ...URL, createObjectURL, revokeObjectURL });

    let approved = false;
    const approvalRequests: unknown[] = [];
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
        return Promise.resolve(jsonResponse(platformPreferences()));
      }
      if (url.endsWith("/api/v1/modules/rates/summary")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(ratesSummary()));
      }
      if (url.endsWith("/api/v1/modules/rates/batches")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            items: [readyBatchDetail(), blockedBatchDetail()],
            total: 2,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(approved ? approvedBatchDetail() : readyBatchDetail()));
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready/artifacts")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_ready",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            items: [
              {
                id: "artifact_ready",
                artifact_type: "rates_csv_export",
                file_name: "synthetic_rates_export.zip",
                content_type: "application/zip",
                sha256: "synthetic-sha",
                size_bytes: 1234,
                sensitivity_level: "client_safe",
                download_url: "/api/v1/modules/rates/batches/batch_ready/artifacts/artifact_ready/download"
              }
            ],
            total: 1
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready/artifacts/artifact_ready/download")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(new Blob(["synthetic zip"], { type: "application/zip" }), {
            status: 200,
            headers: {
              "Content-Disposition": 'attachment; filename="synthetic_rates_export.zip"',
              "Content-Type": "application/zip"
            }
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready/evidence")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_ready",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            items: approved
              ? [
                  {
                    id: "evidence_approval",
                    evidence_type: "rates_batch_approval",
                    status: "APPROVED",
                    summary_json: "{}",
                    artifact_id: null,
                    manifest_id: "manifest_approval",
                    client_safe: true,
                    sensitivity_level: "client_safe"
                  },
                  {
                    id: "evidence_ready",
                    evidence_type: "rates_export",
                    status: "CREATED",
                    summary_json: "{}",
                    artifact_id: "artifact_ready",
                    manifest_id: "manifest_ready",
                    client_safe: true,
                    sensitivity_level: "client_safe"
                  }
                ]
              : [
                  {
                    id: "evidence_ready",
                    evidence_type: "rates_export",
                    status: "CREATED",
                    summary_json: "{}",
                    artifact_id: "artifact_ready",
                    manifest_id: "manifest_ready",
                    client_safe: true,
                    sensitivity_level: "client_safe"
                  }
                ],
            total: approved ? 2 : 1
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready/approve")) {
        expect(init?.method).toBe("POST");
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init.body));
        approvalRequests.push(body);
        expect(body).toEqual({ approval_note: "Reviewed for synthetic browser QA." });
        approved = true;
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_ready",
            status: "APPROVED",
            approved_at: "2026-05-21T22:00:00Z",
            approved_by: "synthetic.user@example.test",
            evidence_id: "evidence_approval",
            manifest_id: "manifest_approval"
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_blocked/validate")) {
        expect(init?.method).toBe("POST");
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse({ batch_id: "batch_blocked", status: "VALIDATED", issues: [] }));
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_blocked")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(blockedBatchDetail()));
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_blocked/artifacts")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_blocked",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            items: [],
            total: 0
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_blocked/evidence")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_blocked",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            items: [],
            total: 0
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

    await screen.findByRole("heading", { name: "Rates Studio" });
    const library = await screen.findByLabelText("Rate batch library");
    expect(library).toHaveTextContent("Synthetic ready batch");
    expect(library).toHaveTextContent("Synthetic blocked batch");
    await userEvent.type(within(library).getByLabelText("Rate batch search"), "blocked");
    await userEvent.selectOptions(within(library).getByLabelText("Rate batch status filter"), "DRAFT");
    await userEvent.selectOptions(within(library).getByLabelText("Rate batch domain filter"), "OTM1");
    expect(library).toHaveTextContent("Synthetic blocked batch");
    expect(within(library).queryByText("Synthetic ready batch")).not.toBeInTheDocument();
    await userEvent.click(within(library).getByRole("button", { name: /Synthetic blocked batch/ }));
    expect(await screen.findByLabelText("Selected rate batch")).toHaveTextContent("Synthetic blocked batch");
    await userEvent.clear(within(library).getByLabelText("Rate batch search"));
    await userEvent.selectOptions(within(library).getByLabelText("Rate batch status filter"), "ALL");
    await userEvent.click(within(library).getByRole("button", { name: /Synthetic ready batch/ }));
    expect(await screen.findByLabelText("Selected rate batch")).toHaveTextContent("Synthetic ready batch");
    expect(screen.getByLabelText("Rates lifecycle destinations")).toHaveTextContent("Back to Cockpit");
    expect(screen.getByLabelText("Rates lifecycle destinations")).toHaveTextContent("Open batch library");
    expect(screen.getByLabelText("Rates lifecycle destinations")).toHaveTextContent("Create rate batch");
    expect(screen.getByRole("link", { name: "Back to Cockpit" })).toHaveAttribute("href", "/home");
    expect(screen.getByRole("link", { name: "Open batch library" })).toHaveAttribute("href", "/rates/batches");
    expect(screen.getByRole("link", { name: "Open selected batch" })).toHaveAttribute("href", "/rates/batches/batch_ready");
    expect(screen.getByRole("link", { name: "Stage tables" })).toHaveAttribute("href", "/rates/batches/batch_ready/stage");
    expect(screen.getByRole("link", { name: "Review issues" })).toHaveAttribute("href", "/rates/batches/batch_ready/issues");
    expect(screen.getByRole("link", { name: "CSV preview" })).toHaveAttribute("href", "/rates/batches/batch_ready/csv-preview");
    expect(screen.getByRole("link", { name: "Export review" })).toHaveAttribute("href", "/rates/batches/batch_ready/export");
    expect(screen.getByRole("link", { name: "Approval review" })).toHaveAttribute("href", "/rates/batches/batch_ready/approve");
    expect(screen.getByRole("link", { name: "Artifacts" })).toHaveAttribute("href", "/rates/batches/batch_ready/artifacts");
    expect(screen.getByRole("link", { name: "Evidence" })).toHaveAttribute("href", "/rates/batches/batch_ready/evidence");
    expect(screen.getByRole("link", { name: "Load Plan handoff" })).toHaveAttribute("href", "/rates/batches/batch_ready/load-plan");
    expect(screen.getByLabelText("Rates summary metrics")).toBeInTheDocument();
    expect(screen.getAllByText("Synthetic ready batch").length).toBeGreaterThan(0);
    expect(
      await within(await screen.findByLabelText("Selected batch tables")).findByText("ACCESSORIAL_COST")
    ).toBeInTheDocument();
    expect(await screen.findByText("synthetic_rates_export.zip")).toBeInTheDocument();
    expect(screen.getByText("rates_export")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Download" }));
    expect(await screen.findByText("Download started: synthetic_rates_export.zip.")).toBeInTheDocument();
    expect(createObjectURL).toHaveBeenCalledOnce();
    expect(anchorClick).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:synthetic-rates-export");
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByText("Ready for approval")).toBeInTheDocument();
    expect(screen.getByText("Rate batch is not ready: NO_ROWS")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Approve" }));
    expect(await screen.findByRole("heading", { name: "Confirm rate batch approval" })).toBeInTheDocument();
    expect(screen.getByLabelText("Rate approval review")).toHaveTextContent("Synthetic ready batch");
    expect(screen.getByLabelText("Rate approval review")).toHaveTextContent("ACCESSORIAL_ONLY");
    expect(screen.getByLabelText("Rate approval review")).toHaveTextContent("1 table(s)");
    expect(screen.getByLabelText("Rate approval review")).toHaveTextContent("OTM1");
    await userEvent.type(screen.getByLabelText("Approval note"), "Reviewed for synthetic browser QA.");
    await userEvent.click(screen.getByRole("button", { name: "Confirm approval" }));
    expect(await screen.findByText("Approve completed.")).toBeInTheDocument();
    expect(await screen.findByText("rates_batch_approval")).toBeInTheDocument();
    expect(approvalRequests).toHaveLength(1);

    await userEvent.click(within(screen.getByLabelText("Rate batch library")).getByRole("button", { name: /Synthetic blocked batch/ }));
    expect(await screen.findByText("No tables have been staged for this batch.")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Validate" }));
    expect(await screen.findByText("Validate completed.")).toBeInTheDocument();
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/modules/rates/batches/batch_blocked/validate",
        expect.objectContaining({ method: "POST" })
      )
    );
  });

  it("creates a synthetic rate batch from the module action and selects it", async () => {
    const createObjectURL = vi.fn(() => "blob:synthetic-export");
    const revokeObjectURL = vi.fn();
    const anchorClick = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    vi.stubGlobal("URL", { ...URL, createObjectURL, revokeObjectURL });
    let created = false;
    let tableAdded = false;
    let previewed = false;
    let exported = false;
    const createRequests: unknown[] = [];
    const tableRequests: unknown[] = [];
    const previewRequests: unknown[] = [];
    const exportRequests: unknown[] = [];
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
              { id: "rates", label: "Rates Studio", path: "/rates", status: "ACTIVE" }
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
      if (url.endsWith("/api/v1/modules/rates/summary")) {
        return Promise.resolve(jsonResponse(created ? ratesSummaryWithCreatedBatch() : ratesSummary()));
      }
      if (url.endsWith("/api/v1/modules/rates/batches") && (!init?.method || init.method === "GET")) {
        return Promise.resolve(
          jsonResponse({
            items: created
              ? [tableAdded ? createdBatchDetailWithTable() : createdBatchDetail(), readyBatchDetail()]
              : [readyBatchDetail(), blockedBatchDetail()],
            total: created ? 2 : 2,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches") && init?.method === "POST") {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init.body));
        createRequests.push(body);
        expect(body).toEqual({
          scenario_code: "RATE_GEO_ONLY",
          name: "Synthetic new rate package",
          domain_name: "OTM1",
          description: "",
          source_type: "api"
        });
        created = true;
        return Promise.resolve(jsonResponse(createdBatchDetail()));
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_created")) {
        return Promise.resolve(jsonResponse(tableAdded ? createdBatchDetailWithTable() : createdBatchDetail()));
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_created/tables")) {
        expect(init?.method).toBe("POST");
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init.body));
        tableRequests.push(body);
        expect(body).toEqual({
          tables: [
            {
              table_name: "X_LANE",
              rows: [{ X_LANE_GID: "OTM1.XL_SYN_001", X_LANE_XID: "XL_SYN_001" }]
            }
          ]
        });
        tableAdded = true;
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_created",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            tables: createdBatchDetailWithTable().tables
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_created/csv-preview")) {
        expect(init?.method).toBe("POST");
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        previewRequests.push({ url, method: init.method });
        previewed = true;
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_created",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            previews: [
              {
                table_name: "X_LANE",
                content: "X_LANE\nX_LANE_GID,X_LANE_XID\nOTM1.XL_SYN_001,XL_SYN_001"
              }
            ]
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_created/export-csv")) {
        expect(init?.method).toBe("POST");
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        exportRequests.push({ url, method: init.method });
        exported = true;
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_created",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            artifact_id: "artifact_created",
            evidence_id: "evidence_created",
            manifest_id: "manifest_created",
            file_name: "synthetic_created_rates_export.zip",
            file_path: "client-safe-hidden",
            sha256: "synthetic-export-sha",
            size_bytes: 2048,
            tables: ["X_LANE"]
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_created/artifacts")) {
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_created",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            items: exported
              ? [
                  {
                    id: "artifact_created",
                    artifact_type: "rates_csv_zip",
                    file_name: "synthetic_created_rates_export.zip",
                    content_type: "application/zip",
                    sha256: "synthetic-export-sha",
                    size_bytes: 2048,
                    sensitivity_level: "client_safe",
                    download_url: "/api/v1/modules/rates/batches/batch_created/artifacts/artifact_created/download"
                  }
                ]
              : [],
            total: exported ? 1 : 0
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_created/artifacts/artifact_created/download")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(new Blob(["synthetic export zip"], { type: "application/zip" }), {
            status: 200,
            headers: {
              "Content-Disposition": 'attachment; filename="synthetic_created_rates_export.zip"',
              "Content-Type": "application/zip"
            }
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_created/evidence")) {
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_created",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            items: exported
              ? [
                  {
                    id: "evidence_created",
                    evidence_type: "rates_export",
                    status: "CREATED",
                    summary_json: "{}",
                    artifact_id: "artifact_created",
                    manifest_id: "manifest_created",
                    client_safe: true,
                    sensitivity_level: "client_safe"
                  }
                ]
              : [],
            total: exported ? 1 : 0
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready")) {
        return Promise.resolve(jsonResponse(readyBatchDetail()));
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready/artifacts")) {
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_ready",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            items: [],
            total: 0
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready/evidence")) {
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_ready",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            items: [],
            total: 0
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

    await screen.findByRole("heading", { name: "Rates Studio" });
    await userEvent.click(screen.getByRole("button", { name: "Create rate batch" }));
    expect(await screen.findByRole("heading", { name: "New rate batch" })).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Scenario"), "RATE_GEO_ONLY");
    await userEvent.clear(screen.getByLabelText("Batch name"));
    await userEvent.type(screen.getByLabelText("Batch name"), "Synthetic new rate package");
    await userEvent.clear(screen.getByLabelText("Domain"));
    await userEvent.type(screen.getByLabelText("Domain"), "OTM1");
    await userEvent.click(screen.getByRole("button", { name: "Create batch" }));

    expect(await screen.findByText("Rate batch created.")).toBeInTheDocument();
    expect(
      await within(await screen.findByLabelText("Rate batch library")).findByRole("button", {
        name: /Synthetic new rate package/
      })
    ).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByLabelText("Selected rate batch")).toHaveTextContent("Synthetic new rate package");
    expect(createRequests).toHaveLength(1);

    expect(screen.getByRole("heading", { name: "Stage table row" })).toBeInTheDocument();
    await userEvent.selectOptions(screen.getByLabelText("Table"), "X_LANE");
    await userEvent.clear(screen.getByLabelText("Row GID"));
    await userEvent.type(screen.getByLabelText("Row GID"), "OTM1.XL_SYN_001");
    await userEvent.clear(screen.getByLabelText("Row value"));
    await userEvent.type(screen.getByLabelText("Row value"), "XL_SYN_001");
    await userEvent.click(screen.getByRole("button", { name: "Add table row" }));

    expect(await screen.findByText("Table row staged.")).toBeInTheDocument();
    expect(await within(await screen.findByLabelText("Selected batch tables")).findByText("X_LANE")).toBeInTheDocument();
    expect(tableRequests).toHaveLength(1);

    await userEvent.click(screen.getByRole("button", { name: "Preview CSV" }));

    expect(await screen.findByText("CSV preview ready.")).toBeInTheDocument();
    expect(screen.getByLabelText("CSV preview output")).toHaveTextContent("X_LANE_GID,X_LANE_XID");
    expect(screen.getByLabelText("CSV preview output")).toHaveTextContent("OTM1.XL_SYN_001,XL_SYN_001");
    expect(previewRequests).toHaveLength(1);
    expect(previewed).toBe(true);

    await userEvent.click(screen.getByRole("button", { name: "Export CSV" }));
    expect(screen.getByLabelText("Rate export review")).toHaveTextContent("Synthetic new rate package");
    expect(screen.getByLabelText("Rate export review")).toHaveTextContent("RATE_GEO_ONLY");
    expect(screen.getByLabelText("Rate export review")).toHaveTextContent("1 table(s)");
    expect(screen.getByLabelText("Rate export review")).toHaveTextContent("1 preview file(s)");
    expect(screen.getByLabelText("Rate export review")).toHaveTextContent("client-safe artifact");
    expect(exportRequests).toHaveLength(0);
    await userEvent.click(screen.getByRole("button", { name: "Confirm export" }));
    expect(await screen.findByText("CSV export created: synthetic_created_rates_export.zip.")).toBeInTheDocument();
    expect(await screen.findByText("synthetic_created_rates_export.zip")).toBeInTheDocument();
    expect(await screen.findByText("rates_export")).toBeInTheDocument();
    expect(exportRequests).toHaveLength(1);

    await userEvent.click(screen.getByRole("button", { name: "Download" }));
    expect(await screen.findByText("Download started: synthetic_created_rates_export.zip.")).toBeInTheDocument();
    expect(createObjectURL).toHaveBeenCalledOnce();
    expect(anchorClick).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:synthetic-export");

    await userEvent.click(within(screen.getByLabelText("Rate batch library")).getByRole("button", { name: /Synthetic ready batch/ }));
    expect(await screen.findByLabelText("Selected rate batch")).toHaveTextContent("Synthetic ready batch");
    expect(screen.queryByText("Download started: synthetic_created_rates_export.zip.")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("CSV preview output")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Export CSV" })).toBeDisabled();
  });

  it("recovers direct batch library and new batch routes", async () => {
    let created = false;
    const createRequests: unknown[] = [];
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
              { id: "rates", label: "Rates Studio", path: "/rates", status: "ACTIVE" }
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
      if (url.endsWith("/api/v1/modules/rates/summary")) {
        return Promise.resolve(jsonResponse(created ? ratesSummaryWithCreatedBatch() : ratesSummary()));
      }
      if (url.endsWith("/api/v1/modules/rates/batches") && (!init?.method || init.method === "GET")) {
        return Promise.resolve(
          jsonResponse({
            items: created ? [createdBatchDetail(), readyBatchDetail(), blockedBatchDetail()] : [readyBatchDetail(), blockedBatchDetail()],
            total: created ? 3 : 2,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches") && init?.method === "POST") {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init.body));
        createRequests.push(body);
        created = true;
        return Promise.resolve(jsonResponse(createdBatchDetail()));
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_created")) {
        return Promise.resolve(jsonResponse(createdBatchDetail()));
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_created/artifacts")) {
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_created",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            items: [],
            total: 0
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_created/evidence")) {
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_created",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            items: [],
            total: 0
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp("/rates/batches");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Rate batch library" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Rates" })).toHaveAttribute("href", "/rates");
    expect(screen.getByRole("link", { name: "Create rate batch" })).toHaveAttribute("href", "/rates/batches/new");
    const library = screen.getByLabelText("Route rate batch library");
    expect(library).toHaveTextContent("Synthetic ready batch");
    expect(library).toHaveTextContent("Synthetic blocked batch");
    await userEvent.type(within(library).getByLabelText("Rate batch search"), "blocked");
    expect(library).toHaveTextContent("Synthetic blocked batch");
    expect(within(library).queryByText("Synthetic ready batch")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("link", { name: "Create rate batch" }));
    expect(await screen.findByRole("heading", { name: "New rate batch" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to batch library" })).toHaveAttribute("href", "/rates/batches");
    await userEvent.clear(screen.getByLabelText("Batch name"));
    await userEvent.type(screen.getByLabelText("Batch name"), "Synthetic new rate package");
    await userEvent.click(screen.getByRole("button", { name: "Create batch" }));

    expect(await screen.findByRole("heading", { name: "Rate batch overview" })).toBeInTheDocument();
    expect(screen.getByLabelText("Route batch summary")).toHaveTextContent("Synthetic new rate package");
    expect(createRequests).toHaveLength(1);
  });

  it("recovers direct batch lifecycle routes", async () => {
    const createObjectURL = vi.fn(() => "blob:synthetic-route-export");
    const revokeObjectURL = vi.fn();
    const anchorClick = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    vi.stubGlobal("URL", { ...URL, createObjectURL, revokeObjectURL });
    const tableRequests: unknown[] = [];
    const previewRequests: unknown[] = [];
    const exportRequests: unknown[] = [];
    const approvalRequests: unknown[] = [];
    const loadPlanRequests: unknown[] = [];
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
              { id: "rates", label: "Rates Studio", path: "/rates", status: "ACTIVE" }
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
      if (url.endsWith("/api/v1/modules/rates/summary")) {
        return Promise.resolve(jsonResponse(ratesSummary()));
      }
      if (url.endsWith("/api/v1/modules/rates/batches")) {
        return Promise.resolve(
          jsonResponse({
            items: [readyBatchDetail(), blockedBatchDetail()],
            total: 2,
            page: 1,
            page_size: 50
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready")) {
        return Promise.resolve(jsonResponse(readyBatchDetail()));
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready/tables")) {
        expect(init?.method).toBe("POST");
        const body = JSON.parse(String(init.body));
        tableRequests.push(body);
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_ready",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            tables: readyBatchDetail().tables
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready/issues")) {
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_ready",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            items: [
              {
                id: "issue_warning",
                batch_id: "batch_ready",
                batch_table_id: "table_ready",
                batch_row_id: null,
                severity: "WARNING",
                issue_code: "MISSING_OPTIONAL_FIELD",
                table_name: "ACCESSORIAL_COST",
                column_name: "COST_CODE_GID",
                message: "Optional cost code should be reviewed before export.",
                details_json: "{}"
              }
            ],
            total: 1
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready/tables/ACCESSORIAL_COST")) {
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_ready",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            table: readyBatchDetail().tables[0],
            rows: [
              {
                row_index: 1,
                status: "PENDING",
                payload: {
                  ACCESSORIAL_COST_GID: "OTM1.ACC_ROUTE",
                  COST_CODE_GID: "OTM1.ACC_FUEL"
                }
              }
            ],
            issues: [
              {
                id: "issue_warning",
                batch_id: "batch_ready",
                batch_table_id: "table_ready",
                batch_row_id: null,
                severity: "WARNING",
                issue_code: "MISSING_OPTIONAL_FIELD",
                table_name: "ACCESSORIAL_COST",
                column_name: "COST_CODE_GID",
                message: "Optional cost code should be reviewed before export.",
                details_json: "{}"
              }
            ],
            total: 1
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready/csv-preview")) {
        expect(init?.method).toBe("POST");
        previewRequests.push({ url, method: init.method });
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_ready",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            previews: [
              {
                table_name: "ACCESSORIAL_COST",
                content: "ACCESSORIAL_COST\nACCESSORIAL_COST_GID,COST_CODE_GID\nOTM1.ACC_ROUTE,OTM1.ACC_FUEL"
              }
            ]
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready/export-csv")) {
        expect(init?.method).toBe("POST");
        exportRequests.push({ url, method: init.method });
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_ready",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            artifact_id: "artifact_route",
            evidence_id: "evidence_route",
            manifest_id: "manifest_route",
            file_name: "synthetic_route_rates_export.zip",
            file_path: "client-safe-hidden",
            sha256: "synthetic-route-export-sha",
            size_bytes: 2048,
            tables: ["ACCESSORIAL_COST"]
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready/approve")) {
        expect(init?.method).toBe("POST");
        const body = JSON.parse(String(init.body));
        approvalRequests.push(body);
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_ready",
            status: "APPROVED",
            approved_at: "2026-05-27T18:00:00Z",
            approved_by: "synthetic.user@example.test",
            evidence_id: "evidence_route_approval",
            manifest_id: "manifest_route_approval"
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready/artifacts")) {
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_ready",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            items: [
              {
                id: "artifact_route",
                artifact_type: "rates_csv_export",
                file_name: "synthetic_route_rates_export.zip",
                content_type: "application/zip",
                sha256: "synthetic-route-export-sha",
                size_bytes: 2048,
                sensitivity_level: "client_safe",
                download_url: "/api/v1/modules/rates/batches/batch_ready/artifacts/artifact_route/download"
              }
            ],
            total: 1
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready/artifacts/artifact_route/download")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          new Response(new Blob(["synthetic route export zip"], { type: "application/zip" }), {
            status: 200,
            headers: {
              "Content-Disposition": 'attachment; filename="synthetic_route_rates_export.zip"',
              "Content-Type": "application/zip"
            }
          })
        );
      }
      if (url.endsWith("/api/v1/modules/rates/batches/batch_ready/evidence")) {
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_ready",
            catalog_macro_object_code: "RATE_RECORD",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            items: [
              {
                id: "evidence_route",
                evidence_type: "rates_export",
                status: "CREATED",
                summary_json: "{}",
                artifact_id: "artifact_route",
                manifest_id: "manifest_route",
                client_safe: true,
                sensitivity_level: "client_safe"
              },
              {
                id: "evidence_route_approval",
                evidence_type: "rates_batch_approval",
                status: "APPROVED",
                summary_json: "{}",
                artifact_id: null,
                manifest_id: "manifest_route_approval",
                client_safe: true,
                sensitivity_level: "client_safe"
              }
            ],
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/modules/load-plan/packages/from-rates/batch_ready")) {
        expect(init?.method).toBe("POST");
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        loadPlanRequests.push({ url, method: init.method });
        return Promise.resolve(
          jsonResponse({
            id: "load_plan_rate_package",
            package_type: "rates",
            source_batch_id: "batch_ready",
            status: "REGISTERED",
            domain_name: "OTM1",
            environment_id: null,
            summary: {
              catalog_macro_object_code: "RATE_RECORD",
              catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
            }
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp("/rates/batches/batch_ready");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Rate batch overview" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Rates" })).toHaveAttribute("href", "/rates");
    expect(screen.getByLabelText("Route batch summary")).toHaveTextContent("Synthetic ready batch");
    expect(screen.getByLabelText("Route batch tables")).toHaveTextContent("ACCESSORIAL_COST");
    await userEvent.click(screen.getByRole("link", { name: "ACCESSORIAL_COST" }));
    expect(await screen.findByRole("heading", { name: "Rate batch table detail" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Batch" })).toHaveAttribute("href", "/rates/batches/batch_ready");
    expect(screen.getByLabelText("Route table detail")).toHaveTextContent("ACCESSORIAL_COST");
    expect(screen.getByLabelText("Route table rows")).toHaveTextContent("OTM1.ACC_ROUTE");
    expect(screen.getByLabelText("Route table rows")).toHaveTextContent("OTM1.ACC_FUEL");
    expect(screen.getByLabelText("Route table issues")).toHaveTextContent("MISSING_OPTIONAL_FIELD");
    await userEvent.click(screen.getByRole("link", { name: "Back to Batch" }));
    expect(await screen.findByRole("heading", { name: "Rate batch overview" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("link", { name: "Stage tables" }));
    expect(await screen.findByRole("heading", { name: "Stage rate batch tables" })).toBeInTheDocument();
    await userEvent.clear(screen.getByLabelText("Row GID"));
    await userEvent.type(screen.getByLabelText("Row GID"), "OTM1.XL_ROUTE_001");
    await userEvent.clear(screen.getByLabelText("Row value"));
    await userEvent.type(screen.getByLabelText("Row value"), "XL_ROUTE_001");
    await userEvent.click(screen.getByRole("button", { name: "Add table row" }));
    expect(await screen.findByText("Table row staged.")).toBeInTheDocument();
    expect(tableRequests).toHaveLength(1);

    await userEvent.click(screen.getByRole("link", { name: "Review issues" }));
    expect(await screen.findByRole("heading", { name: "Rate batch issues" })).toBeInTheDocument();
    expect(screen.getByLabelText("Route batch issues")).toHaveTextContent("MISSING_OPTIONAL_FIELD");
    expect(screen.getByLabelText("Route batch issues")).toHaveTextContent("Optional cost code should be reviewed before export.");

    const routeDestinations = screen.getByLabelText("Rate batch route destinations");
    await userEvent.click(within(routeDestinations).getByRole("link", { name: "CSV preview" }));
    expect(await screen.findByRole("heading", { name: "Rate CSV preview" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Preview CSV" }));
    expect(await screen.findByText("CSV preview ready.")).toBeInTheDocument();
    expect(screen.getByLabelText("Route CSV preview output")).toHaveTextContent("ACCESSORIAL_COST_GID,COST_CODE_GID");
    expect(previewRequests).toHaveLength(1);

    await userEvent.click(within(routeDestinations).getByRole("link", { name: "Export review" }));
    expect(await screen.findByRole("heading", { name: "Rate export review" })).toBeInTheDocument();
    expect(screen.getByLabelText("Route export review")).toHaveTextContent("1 preview file(s)");
    expect(exportRequests).toHaveLength(0);
    await userEvent.click(screen.getByRole("button", { name: "Confirm export" }));
    expect(await screen.findByText("CSV export created: synthetic_route_rates_export.zip.")).toBeInTheDocument();
    expect(exportRequests).toHaveLength(1);

    await userEvent.click(within(routeDestinations).getByRole("link", { name: "Approval review" }));
    expect(await screen.findByRole("heading", { name: "Rate approval review" })).toBeInTheDocument();
    expect(screen.getByLabelText("Route approval review")).toHaveTextContent("Synthetic ready batch");
    await userEvent.type(screen.getByLabelText("Approval note"), "Route approval reviewed.");
    await userEvent.click(screen.getByRole("button", { name: "Confirm approval" }));
    expect(await screen.findByText("Approve completed.")).toBeInTheDocument();
    expect(approvalRequests).toEqual([{ approval_note: "Route approval reviewed." }]);

    await userEvent.click(within(screen.getByLabelText("Rate batch route destinations")).getByRole("link", { name: "Artifacts" }));
    expect(await screen.findByRole("heading", { name: "Rate batch artifacts" })).toBeInTheDocument();
    expect(screen.getByLabelText("Route batch artifacts")).toHaveTextContent("synthetic_route_rates_export.zip");
    await userEvent.click(screen.getByRole("button", { name: "Download" }));
    expect(await screen.findByText("Download started: synthetic_route_rates_export.zip.")).toBeInTheDocument();
    expect(createObjectURL).toHaveBeenCalledOnce();
    expect(anchorClick).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:synthetic-route-export");

    await userEvent.click(within(screen.getByLabelText("Rate batch route destinations")).getByRole("link", { name: "Evidence" }));
    expect(await screen.findByRole("heading", { name: "Rate batch evidence" })).toBeInTheDocument();
    expect(screen.getByLabelText("Route batch evidence")).toHaveTextContent("rates_export");
    expect(screen.getByLabelText("Route batch evidence")).toHaveTextContent("rates_batch_approval");

    await userEvent.click(within(screen.getByLabelText("Rate batch route destinations")).getByRole("link", { name: "Load Plan handoff" }));
    expect(await screen.findByRole("heading", { name: "Rate Load Plan handoff" })).toBeInTheDocument();
    expect(screen.getByLabelText("Route Load Plan handoff")).toHaveTextContent("RATE_RECORD");
    expect(screen.getByLabelText("Route Load Plan handoff")).toHaveTextContent("1 artifact(s)");
    expect(screen.getByLabelText("Route Load Plan handoff")).toHaveTextContent("2 evidence record(s)");
    expect(loadPlanRequests).toHaveLength(0);
    await userEvent.click(screen.getByRole("button", { name: "Register Load Plan package" }));
    expect(await screen.findByText("Load Plan package registered: load_plan_rate_package.")).toBeInTheDocument();
    expect(loadPlanRequests).toHaveLength(1);
  });
});
