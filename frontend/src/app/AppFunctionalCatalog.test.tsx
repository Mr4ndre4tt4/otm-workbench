import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "../platform/auth";

function renderFunctionalApp(initialPath = "/catalog") {
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

function cockpitSummary() {
  return {
    module_id: "home",
    title: "Project Cockpit",
    status: "ready",
    description: "Project-level operational overview.",
    active_context: {},
    setup_status: {
      status: "READY",
      profile_count: 1,
      environment_count: 1,
      active_context_selected: true,
      missing_requirements: []
    },
    counts: { recent_jobs: 0, recent_artifacts: 0, recent_evidence: 0 },
    module_summary: { total: 2, counts_by_status: { ACTIVE: 2 }, items: [] },
    recent_jobs: [],
    recent_artifacts: [],
    recent_evidence: [],
    available_actions: []
  };
}

function macroObjectSummary() {
  return {
    items: [
      {
        id: "macro_rate_record",
        code: "RATE_RECORD",
        name: "Rate record",
        category: "RATES_SETUP",
        description: "Synthetic catalog macro object for rate packages.",
        default_load_order: 20,
        default_method: "CSVUTIL",
        method_options: ["CSVUTIL"],
        allow_cutover: true,
        allow_csvutil: true,
        evidence_required_default: true,
        summary: {
          table_count: 2,
          dependency_count: 1,
          validated_table_count: 2,
          all_tables_validated: true,
          csvutil_table_count: 2,
          cutover_table_count: 2
        }
      },
      {
        id: "macro_region",
        code: "REGION",
        name: "Region",
        category: "MASTER_DATA",
        description: "Synthetic region macro object.",
        default_load_order: 10,
        default_method: "CSVUTIL",
        method_options: ["CSVUTIL"],
        allow_cutover: true,
        allow_csvutil: true,
        evidence_required_default: false,
        summary: {
          table_count: 1,
          dependency_count: 0,
          validated_table_count: 1,
          all_tables_validated: true,
          csvutil_table_count: 1,
          cutover_table_count: 1
        }
      }
    ],
    total: 2,
    page: 1,
    page_size: 50
  };
}

function rateRecordDetail() {
  return {
    ...macroObjectSummary().items[0],
    tables: [],
    dependencies: []
  };
}

function rateRecordTables() {
  return {
    items: [
      {
        id: "macro_table_rate_geo",
        table_name: "RATE_GEO",
        relationship_role: "TARGET",
        is_primary_table: true,
        is_required: true,
        data_category: "RATES",
        validated_by_datadict: true,
        allow_csvutil: true,
        allow_cutover: true
      },
      {
        id: "macro_table_rate_geo_cost",
        table_name: "RATE_GEO_COST",
        relationship_role: "TARGET",
        is_primary_table: false,
        is_required: true,
        data_category: "RATES",
        validated_by_datadict: true,
        allow_csvutil: true,
        allow_cutover: true
      }
    ],
    total: 2,
    page: 1,
    page_size: 50
  };
}

function rateRecordLoadPlan() {
  return {
    macro_object_code: "RATE_RECORD",
    items: [
      {
        macro_object_code: "RATE_OFFERING",
        macro_object_name: "Rate offering",
        dependency_role: "DEPENDENCY",
        dependency_type: "REQUIRED",
        is_required: true,
        tables: ["RATE_OFFERING"],
        table_count: 1,
        all_tables_validated: true
      },
      {
        macro_object_code: "RATE_RECORD",
        macro_object_name: "Rate record",
        dependency_role: "TARGET",
        dependency_type: "TARGET",
        is_required: true,
        tables: ["RATE_GEO", "RATE_GEO_COST"],
        table_count: 2,
        all_tables_validated: true
      }
    ],
    summary: {
      step_count: 2,
      dependency_count: 1,
      target_table_count: 2,
      all_target_tables_validated: true
    }
  };
}

function rateRecordCrossCheck() {
  return {
    macro_object_code: "RATE_RECORD",
    macro_object_name: "Rate record",
    table_checks: [],
    schema_links: [
      {
        id: "link_rate_geo",
        macro_object_code: "RATE_RECORD",
        schema_root_id: "root_rate_geo",
        schema_pack_id: "pack_26a",
        schema_pack_code: "OTM_26A_CORE",
        otm_version: "26A",
        schema_file: "Rate.xsd",
        root_name: "RATE_GEO",
        root_display_label: "Rate Record / Rate Geo",
        canonical_root_name: "RATE_GEO",
        schema_root_aliases: ["RateGeo", "Rate Record", "RATE_GEO"],
        data_dictionary_family: "RATE_GEO",
        schema_guidance_role: "MACRO_OBJECT",
        domain_area: "RATE",
        root_type: "ROWSET",
        relationship_role: "SEMANTIC_ROOT",
        confidence: "HIGH",
        functional_confidence: "DATA_DICTIONARY_CROSSED",
        source_reference_status: "PINNED",
        source_reference_label: "Oracle Rate Record",
        source_reference_url: "https://docs.oracle.com/example",
        notes: "Synthetic link."
      }
    ],
    summary: {
      target_table_count: 2,
      validated_table_count: 2,
      missing_table_count: 0,
      schema_link_count: 1,
      all_target_tables_validated: true,
      all_schema_links_have_source_reference: true,
      guidance_ready: true,
      readiness_status: "READY"
    }
  };
}

function regionDetail() {
  return {
    ...macroObjectSummary().items[1],
    tables: [],
    dependencies: []
  };
}

function regionTables() {
  return {
    items: [
      {
        id: "macro_table_region",
        table_name: "REGION",
        relationship_role: "TARGET",
        is_primary_table: true,
        is_required: true,
        data_category: "MASTER_DATA",
        validated_by_datadict: true,
        allow_csvutil: true,
        allow_cutover: true
      }
    ],
    total: 1,
    page: 1,
    page_size: 50
  };
}

function regionLoadPlan() {
  return {
    macro_object_code: "REGION",
    items: [
      {
        macro_object_code: "REGION",
        macro_object_name: "Region",
        dependency_role: "TARGET",
        dependency_type: "TARGET",
        is_required: true,
        tables: ["REGION"],
        table_count: 1,
        all_tables_validated: true
      }
    ],
    summary: {
      step_count: 1,
      dependency_count: 0,
      target_table_count: 1,
      all_target_tables_validated: true
    }
  };
}

function regionCrossCheck() {
  return {
    macro_object_code: "REGION",
    macro_object_name: "Region",
    table_checks: [],
    schema_links: [],
    summary: {
      target_table_count: 1,
      validated_table_count: 1,
      missing_table_count: 0,
      schema_link_count: 0,
      all_target_tables_validated: true,
      all_schema_links_have_source_reference: false,
      guidance_ready: false,
      readiness_status: "BLOCKED_SCHEMA_LINKS"
    }
  };
}

function schemaGuidanceReadiness() {
  return {
    items: [
      {
        macro_object_code: "RATE_RECORD",
        macro_object_name: "Rate record",
        category: "RATES_SETUP",
        guidance_ready: true,
        readiness_status: "READY",
        target_table_count: 4,
        validated_table_count: 4,
        missing_table_count: 0,
        schema_link_count: 2,
        all_target_tables_validated: true,
        all_schema_links_have_source_reference: true
      },
      {
        macro_object_code: "ITEM",
        macro_object_name: "Item",
        category: "MASTER_DATA",
        guidance_ready: false,
        readiness_status: "BLOCKED_SCHEMA_LINKS",
        target_table_count: 4,
        validated_table_count: 4,
        missing_table_count: 0,
        schema_link_count: 0,
        all_target_tables_validated: true,
        all_schema_links_have_source_reference: false
      }
    ],
    summary: {
      macro_object_count: 2,
      ready_count: 1,
      blocked_count: 1
    }
  };
}

function schemaRootsByRole(role: string) {
  const roots = {
    ENVELOPE_ONLY: [
      {
        id: "root_transmission",
        schema_pack_id: "pack_26a",
        schema_file_id: "file_transmission",
        root_name: "Transmission",
        root_display_label: "Transmission",
        canonical_root_name: "Transmission",
        schema_root_aliases: ["Transmission"],
        data_dictionary_family: "",
        schema_guidance_role: "ENVELOPE_ONLY",
        namespace: "http://xmlns.oracle.com/apps/otm/transmission",
        domain_area: "TRANSMISSION",
        root_type: "ENVELOPE",
        envelope_role: "TRANSMISSION",
        recommended_modules: ["integration_mapping"],
        documentation: "Synthetic envelope root."
      }
    ],
    MACRO_OBJECT: [
      {
        id: "root_planned_shipment",
        schema_pack_id: "pack_26a",
        schema_file_id: "file_shipment",
        root_name: "PlannedShipment",
        root_display_label: "Planned Shipment",
        canonical_root_name: "PlannedShipment",
        schema_root_aliases: ["Planned Shipment", "Shipment", "PlannedShipment"],
        data_dictionary_family: "SHIPMENT",
        schema_guidance_role: "MACRO_OBJECT",
        namespace: "http://xmlns.oracle.com/apps/otm/shipment",
        domain_area: "SHIPMENT",
        root_type: "DOMAIN_ROOT",
        envelope_role: "NONE",
        recommended_modules: ["integration_mapping"],
        documentation: "Synthetic planned shipment root."
      }
    ]
  };
  return {
    items: roots[role as keyof typeof roots] ?? [],
    total: roots[role as keyof typeof roots]?.length ?? 0,
    page: 1,
    page_size: roots[role as keyof typeof roots]?.length ?? 0
  };
}

describe("Functional Catalog journey", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("validates table, column, and reference contracts from Catalog Core", async () => {
    const tableValidationRequests: unknown[] = [];
    const columnValidationRequests: unknown[] = [];
    const referenceValidationRequests: unknown[] = [];
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
              { id: "catalog", label: "OTM Catalog Core", path: "/catalog", status: "ACTIVE" }
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
      if (url.endsWith("/api/v1/platform/project-cockpit/summary")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(cockpitSummary()));
      }
      if (url.endsWith("/api/v1/catalog/macro-objects")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(macroObjectSummary()));
      }
      if (url.endsWith("/api/v1/catalog/macro-objects/RATE_RECORD")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(rateRecordDetail()));
      }
      if (url.endsWith("/api/v1/catalog/macro-objects/RATE_RECORD/tables")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(rateRecordTables()));
      }
      if (url.endsWith("/api/v1/catalog/macro-objects/RATE_RECORD/load-plan")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(rateRecordLoadPlan()));
      }
      if (url.endsWith("/api/v1/catalog/macro-objects/RATE_RECORD/data-dictionary-cross-check")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(rateRecordCrossCheck()));
      }
      if (url.endsWith("/api/v1/catalog/schema-guidance/readiness")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(schemaGuidanceReadiness()));
      }
      if (url.includes("/api/v1/catalog/schema-roots")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const parsedUrl = new URL(url, "http://localhost");
        return Promise.resolve(jsonResponse(schemaRootsByRole(parsedUrl.searchParams.get("schema_guidance_role") ?? "")));
      }
      if (url.endsWith("/api/v1/catalog/macro-objects/REGION")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(regionDetail()));
      }
      if (url.endsWith("/api/v1/catalog/macro-objects/REGION/tables")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(regionTables()));
      }
      if (url.endsWith("/api/v1/catalog/macro-objects/REGION/load-plan")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(regionLoadPlan()));
      }
      if (url.endsWith("/api/v1/catalog/macro-objects/REGION/data-dictionary-cross-check")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(jsonResponse(regionCrossCheck()));
      }
      if (url.endsWith("/api/v1/catalog/validate/table")) {
        expect(init?.method).toBe("POST");
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init.body));
        tableValidationRequests.push(body);
        expect(body).toEqual({ table_name: "SHIPMENT", usage: "cutover" });
        return Promise.resolve(
          jsonResponse({
            table_name: "SHIPMENT",
            exists: true,
            allow_cutover: false,
            allow_csvutil: false,
            severity: "ERROR",
            message: "Transactional table cannot be used for cutover."
          })
        );
      }
      if (url.endsWith("/api/v1/catalog/validate/column")) {
        expect(init?.method).toBe("POST");
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init.body));
        columnValidationRequests.push(body);
        expect(body).toEqual({ table_name: "RATE_GEO_COST", column_name: "RATE_GEO_COST_GROUP_GID" });
        return Promise.resolve(
          jsonResponse({
            table_name: "RATE_GEO_COST",
            column_name: "RATE_GEO_COST_GROUP_GID",
            exists: true,
            severity: "INFO",
            message: "Column exists in OTM Data Dictionary."
          })
        );
      }
      if (url.endsWith("/api/v1/catalog/validate/reference")) {
        expect(init?.method).toBe("POST");
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init.body));
        referenceValidationRequests.push(body);
        expect(body).toEqual({
          module_id: "rates",
          field_name: "currency_gid",
          value: "OTM2.BRL",
          domain_name: "OTM1"
        });
        return Promise.resolve(
          jsonResponse({
            valid: false,
            severity: "ERROR",
            policy: "MUST_EXIST",
            object_type: "CURRENCY",
            gid: "OTM2.BRL",
            domain_name: "OTM1",
            message: "Reference is outside the active domain scope."
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

    await screen.findByRole("heading", { name: "OTM Catalog Core" });
    expect(await screen.findByRole("heading", { name: "Schema guidance" })).toBeInTheDocument();
    expect(screen.getByText("Ready guidance")).toBeInTheDocument();
    expect(screen.getByText("Blocked guidance")).toBeInTheDocument();
    expect(within(screen.getByLabelText("Integration envelope roots")).getByText("Transmission")).toBeInTheDocument();
    expect(within(screen.getByLabelText("Macro schema roots")).getByText("Planned Shipment")).toBeInTheDocument();
    expect(within(screen.getByLabelText("Schema guidance readiness")).getByText("RATE_RECORD")).toBeInTheDocument();
    expect(within(screen.getByLabelText("Schema guidance readiness")).getByText("BLOCKED SCHEMA LINKS")).toBeInTheDocument();
    expect(await within(await screen.findByLabelText("Selected macro object tables")).findByText("RATE_GEO_COST")).toBeInTheDocument();
    expect(await within(await screen.findByLabelText("Selected macro object load plan")).findByText("RATE_OFFERING")).toBeInTheDocument();

    await userEvent.clear(screen.getByLabelText("Table name"));
    await userEvent.type(screen.getByLabelText("Table name"), "SHIPMENT");
    await userEvent.selectOptions(screen.getByLabelText("Usage"), "cutover");
    await userEvent.click(screen.getByRole("button", { name: "Validate table" }));
    expect(await screen.findByText("Table validation: ERROR")).toBeInTheDocument();
    expect(screen.getByText("Transactional table cannot be used for cutover.")).toBeInTheDocument();
    expect(tableValidationRequests).toHaveLength(1);

    await userEvent.clear(screen.getByLabelText("Column table"));
    await userEvent.type(screen.getByLabelText("Column table"), "RATE_GEO_COST");
    await userEvent.clear(screen.getByLabelText("Column name"));
    await userEvent.type(screen.getByLabelText("Column name"), "RATE_GEO_COST_GROUP_GID");
    await userEvent.click(screen.getByRole("button", { name: "Validate column" }));
    expect(await screen.findByText("Column validation: INFO")).toBeInTheDocument();
    expect(screen.getByText("Column exists in OTM Data Dictionary.")).toBeInTheDocument();
    expect(columnValidationRequests).toHaveLength(1);

    await userEvent.clear(screen.getByLabelText("Reference value"));
    await userEvent.type(screen.getByLabelText("Reference value"), "OTM2.BRL");
    await userEvent.click(screen.getByRole("button", { name: "Validate reference" }));
    expect(await screen.findByText("Reference validation: ERROR")).toBeInTheDocument();
    expect(screen.getByText("Reference is outside the active domain scope.")).toBeInTheDocument();
    expect(referenceValidationRequests).toHaveLength(1);

    await userEvent.click(screen.getByRole("button", { name: /REGION/ }));
    expect(screen.queryByText("Reference validation: ERROR")).not.toBeInTheDocument();
    expect(screen.queryByText("Reference is outside the active domain scope.")).not.toBeInTheDocument();
    expect(await within(await screen.findByLabelText("Selected macro object tables")).findByText("REGION")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /RATE_RECORD/ }));
    expect(await within(await screen.findByLabelText("Selected macro object tables")).findByText("RATE_GEO_COST")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Reset catalog validation" }));
    expect(screen.getByLabelText("Table name")).toHaveValue("RATE_GEO_COST");
    expect(screen.getByLabelText("Usage")).toHaveValue("cutover");
    expect(screen.getByLabelText("Column table")).toHaveValue("RATE_GEO_COST");
    expect(screen.getByLabelText("Column name")).toHaveValue("RATE_GEO_COST_GROUP_GID");
    expect(screen.getByLabelText("Module")).toHaveValue("rates");
    expect(screen.getByLabelText("Field")).toHaveValue("currency_gid");
    expect(screen.getByLabelText("Reference value")).toHaveValue("OTM1.BRL");
    expect(screen.getByLabelText("Domain")).toHaveValue("OTM1");
    expect(screen.queryByText("Table validation: ERROR")).not.toBeInTheDocument();
    expect(screen.queryByText("Column validation: INFO")).not.toBeInTheDocument();
    expect(screen.queryByText("Reference validation: ERROR")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("link", { name: /Project Cockpit/ }));
    await screen.findByRole("heading", { name: "Project Cockpit" });
    await userEvent.click(screen.getByRole("link", { name: /OTM Catalog Core/ }));
    await screen.findByRole("heading", { name: "OTM Catalog Core" });
    await waitFor(() => expect(screen.getAllByText("RATE_RECORD").length).toBeGreaterThan(0));
  });
});
