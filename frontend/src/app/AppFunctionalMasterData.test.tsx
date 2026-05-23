import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "../platform/auth";

function renderFunctionalApp(initialPath = "/master-data") {
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

function regionsTemplate() {
  return {
    available_actions: [
      { disabled: false, disabled_reason: null, href: "", icon_key: "check-circle", key: "validate_definition", label: "Validate definition", method: "POST", recommended: false, requires_confirmation: false, result_hint: "refresh_object", variant: "secondary" },
      { disabled: true, disabled_reason: "TEMPLATE_ALREADY_PUBLISHED", href: "", icon_key: "upload-cloud", key: "publish_template", label: "Publish template", method: "POST", recommended: false, requires_confirmation: false, result_hint: "refresh_object", variant: "secondary" },
      { disabled: false, disabled_reason: null, href: "", icon_key: "file-spreadsheet", key: "build_workbook", label: "Build workbook", method: "POST", recommended: true, requires_confirmation: false, result_hint: "refresh_object", variant: "secondary" },
      { disabled: false, disabled_reason: null, href: "", icon_key: "copy", key: "create_version", label: "Create next version", method: "POST", recommended: false, requires_confirmation: false, result_hint: "refresh_object", variant: "secondary" }
    ],
    catalog_macro_object_code: "REGION",
    code: "REGIONS_BASIC",
    created_at: "2026-05-22T00:00:00",
    data_category: "MASTER_DATA",
    description: "Synthetic starter template for region master data.",
    id: "template_regions",
    name: "Regions Basic",
    sheets: [
      {
        code: "REGIONS",
        fields: [
          { data_type: "string", label: "Region GID", name: "region_gid", required: true, target_column: "REGION_GID" },
          { data_type: "string", label: "Region XID", name: "region_xid", required: true, target_column: "REGION_XID" },
          { data_type: "string", label: "Region Name", name: "region_name", required: false, target_column: "REGION_NAME" }
        ],
        name: "Regions",
        target_table: "REGION"
      },
      {
        code: "REGION_DETAILS",
        fields: [
          { data_type: "string", label: "Region GID", name: "region_gid", required: true, target_column: "REGION_GID" },
          { data_type: "string", label: "Location GID", name: "location_gid", required: true, target_column: "LOCATION_GID" }
        ],
        name: "Region Details",
        target_table: "REGION_DETAIL"
      }
    ],
    status: "PUBLISHED",
    target_tables: ["REGION", "REGION_DETAIL"],
    updated_at: null,
    version: 1
  };
}

function recoveredLocationsTemplate() {
  return {
    ...regionsTemplate(),
    catalog_macro_object_code: "LOCATION",
    code: "LOCATIONS_RECOVERED",
    data_category: "MASTER_DATA",
    definition: {
      documentation_refs: [
        {
          note: "Validated against local OTM Data Dictionary.",
          scope: "LOCATION",
          source_type: "DATA_DICTIONARY"
        }
      ],
      fields: [
        { data_type: "string", field_key: "location_gid", label: "Location ID", required: true, sheet_code: "LOCATIONS" },
        {
          data_type: "string",
          field_key: "location_address_address_line",
          label: "Street line recovered",
          required: false,
          sheet_code: "LOCATION_ADDRESS"
        }
      ],
      mappings: [
        {
          mapping_key: "location_location_gid_to_location_gid",
          required: true,
          source_field_key: "location_gid",
          source_type: "USER_FIELD",
          target_column: "LOCATION_GID",
          target_table: "LOCATION"
        },
        {
          default_value: "UNKNOWN_CITY",
          mapping_key: "location_city_default",
          required: false,
          source_type: "DEFAULT_VALUE",
          target_column: "CITY",
          target_table: "LOCATION"
        },
        {
          mapping_key: "location_address_address_line_to_address_line",
          required: false,
          source_field_key: "location_address_address_line",
          source_type: "USER_FIELD",
          target_column: "ADDRESS_LINE",
          target_table: "LOCATION_ADDRESS"
        },
        {
          mapping_key: "location_address_location_gid_to_location_gid",
          required: false,
          source_field_key: "location_address_location_gid",
          source_type: "USER_FIELD",
          target_column: "LOCATION_GID",
          target_table: "LOCATION_ADDRESS"
        }
      ],
      relationship_rules: [
        {
          child_field_key: "location_address_location_gid",
          child_sheet_code: "LOCATION_ADDRESS",
          parent_field_key: "location_gid",
          parent_sheet_code: "LOCATIONS",
          rule_key: "location_to_location_address",
          severity: "ERROR"
        }
      ],
      schema_version: "master-data-template-definition/v2",
      sheets: [
        { code: "LOCATIONS", field_keys: ["location_gid"], name: "Locations", sequence: 10 },
        {
          code: "LOCATION_ADDRESS",
          field_keys: ["location_address_address_line", "location_address_location_gid"],
          name: "Location Address",
          sequence: 20
        }
      ],
      target_tables: [
        { required: true, sequence: 10, table_name: "LOCATION" },
        { required: false, sequence: 20, table_name: "LOCATION_ADDRESS" }
      ],
      template: {
        catalog_macro_object_code: "LOCATION",
        code: "LOCATIONS_RECOVERED",
        data_category: "MASTER_DATA",
        name: "Locations Recovered",
        status: "DRAFT",
        version: 1
      }
    },
    description: "Synthetic recovered template.",
    id: "template_locations_recovered",
    name: "Locations Recovered",
    sheets: [
      {
        code: "LOCATIONS",
        fields: [
          { data_type: "string", label: "Location ID", name: "location_gid", required: true, target_column: "LOCATION_GID" }
        ],
        name: "Locations",
        target_table: "LOCATION"
      },
      {
        code: "LOCATION_ADDRESS",
        fields: [
          {
            data_type: "string",
            label: "Street line recovered",
            name: "location_address_address_line",
            required: false,
            target_column: "ADDRESS_LINE"
          }
        ],
        name: "Location Address",
        target_table: "LOCATION_ADDRESS"
      }
    ],
    status: "DRAFT",
    target_tables: ["LOCATION", "LOCATION_ADDRESS"],
    version: 1
  };
}

describe("Functional Master Data journey", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
  });

  it("validates a template, uploads a workbook, builds output, exports, and returns with backend state", async () => {
    const templateValidationRequests: unknown[] = [];
    const workbookRequests: unknown[] = [];
    const uploadRequests: unknown[] = [];
    const relationshipRequests: unknown[] = [];
    const mapRequests: unknown[] = [];
    const outputRequests: unknown[] = [];
    const csvRequests: unknown[] = [];
    const exportRequests: unknown[] = [];
    const batchDetailRequests: unknown[] = [];
    const loadPlanRegistrationRequests: unknown[] = [];
    const cutoverChecklistRequests: unknown[] = [];
    const cutoverChecklistReadinessRequests: unknown[] = [];
    const outputRecordListRequests: unknown[] = [];
    const csvFileListRequests: unknown[] = [];
    const batchListRequests: unknown[] = [];
    const batchSummaryRequests: unknown[] = [];
    const artifactListRequests: unknown[] = [];
    const artifactDownloadRequests: string[] = [];

    const fetchMock = vi.fn((input, init) => {
      const url = String(input);
      const parsedUrl = new URL(url, "http://local.test");
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
      if (url.endsWith("/api/v1/modules/master-data/templates")) {
        return Promise.resolve(jsonResponse({ items: [regionsTemplate()], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/REGIONS_BASIC")) {
        return Promise.resolve(jsonResponse(regionsTemplate()));
      }
      if (parsedUrl.pathname === "/api/v1/modules/master-data/batches/summary") {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        batchSummaryRequests.push({
          file_name_contains: parsedUrl.searchParams.get("file_name_contains"),
          min_row_count: parsedUrl.searchParams.get("min_row_count"),
          method: init?.method ?? "GET",
          page: parsedUrl.searchParams.get("page"),
          page_size: parsedUrl.searchParams.get("page_size"),
          status: parsedUrl.searchParams.get("status"),
          template_code: parsedUrl.searchParams.get("template_code")
        });
        return Promise.resolve(
          jsonResponse({
            latest_batch_id: "batch_1",
            status_breakdown: [{ batch_count: 1, issue_count: 0, row_count: 2, status: "EXPORTED" }],
            template_breakdown: [{ batch_count: 1, issue_count: 0, row_count: 2, template_code: "REGIONS_BASIC" }],
            total_batches: 1,
            total_issues: 0,
            total_rows: 2
          })
        );
      }
      if (parsedUrl.pathname === "/api/v1/modules/master-data/batches") {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        batchListRequests.push({
          file_name_contains: parsedUrl.searchParams.get("file_name_contains"),
          min_row_count: parsedUrl.searchParams.get("min_row_count"),
          method: init?.method ?? "GET",
          page_size: parsedUrl.searchParams.get("page_size"),
          status: parsedUrl.searchParams.get("status"),
          template_code: parsedUrl.searchParams.get("template_code")
        });
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                batch_id: "batch_1",
                csv_file_count: 2,
                file_name: "regions_basic_upload.xlsx",
                issue_count: 0,
                row_count: 2,
                sheet_count: 2,
                sheet_summaries: [
                  { row_count: 1, sheet_code: "REGIONS", target_table: "REGION" },
                  { row_count: 1, sheet_code: "REGION_DETAILS", target_table: "REGION_DETAIL" }
                ],
                status: "EXPORTED",
                template_code: "REGIONS_BASIC"
              },
              {
                batch_id: "batch_history",
                csv_file_count: 1,
                file_name: "regions_history_upload.xlsx",
                issue_count: 0,
                row_count: 1,
                sheet_count: 1,
                sheet_summaries: [{ row_count: 1, sheet_code: "REGIONS", target_table: "REGION" }],
                status: "CSV_BUILT",
                template_code: "REGIONS_BASIC"
              }
            ],
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/REGIONS_BASIC/validate")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        templateValidationRequests.push({ method: init?.method });
        return Promise.resolve(
          jsonResponse({
            issues: [],
            severity: "INFO",
            summary: { field_count: 5, sheet_count: 2, validated_column_count: 5, validated_table_count: 2 },
            template_code: "REGIONS_BASIC",
            valid: true
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/REGIONS_BASIC/build-workbook")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        workbookRequests.push({ method: init?.method });
        return Promise.resolve(
          jsonResponse({
            artifact_id: "artifact_workbook",
            content_type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            field_count: 5,
            file_name: "regions_basic_v1.xlsx",
            sheet_count: 2,
            template_code: "REGIONS_BASIC"
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/REGIONS_BASIC/batches")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        expect(init?.body).toBeInstanceOf(FormData);
        uploadRequests.push({ method: init?.method });
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_1",
            file_name: "regions_basic_upload.xlsx",
            row_count: 2,
            sheet_count: 2,
            sheets: [
              { row_count: 1, sheet_code: "REGIONS" },
              { row_count: 1, sheet_code: "REGION_DETAILS" }
            ],
            status: "PARSED",
            template_code: "REGIONS_BASIC"
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_1/validate-relationships")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        relationshipRequests.push({ method: init?.method });
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_1",
            issues: [],
            status: "VALID",
            summary: { checked_relationships: 1, issue_count: 0 },
            valid: true
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_1/map")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        mapRequests.push({ method: init?.method });
        return Promise.resolve(jsonResponse({ batch_id: "batch_1", status: "MAPPED", summary: { record_count: 2 } }));
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_1/build-output")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        outputRequests.push({ method: init?.method });
        return Promise.resolve(jsonResponse({ batch_id: "batch_1", status: "OUTPUT_BUILT", summary: { output_count: 2 } }));
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_1/build-csv")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        csvRequests.push({ method: init?.method });
        return Promise.resolve(jsonResponse({ batch_id: "batch_1", status: "CSV_BUILT", summary: { file_count: 2 } }));
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_1/export-csv-package")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        exportRequests.push({ method: init?.method });
        return Promise.resolve(
          jsonResponse({
            artifact_id: "artifact_csv_package",
            batch_id: "batch_1",
            file_name: "master_data_regions_basic.zip",
            manifest_id: "manifest_csv_package",
            status: "EXPORTED",
            summary: { file_count: 2 }
          })
        );
      }
      if (parsedUrl.pathname === "/api/v1/modules/master-data/batches/batch_1") {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        batchDetailRequests.push({ method: init?.method ?? "GET" });
        return Promise.resolve(
          jsonResponse({
            available_actions: [
              { disabled: false, disabled_reason: null, href: "", icon_key: "check-circle", key: "validate_relationships", label: "Validate relationships", method: "POST", requires_confirmation: false, result_hint: "refresh_object", variant: "primary" },
              { disabled: false, disabled_reason: null, href: "", icon_key: "map", key: "map_records", label: "Map records", method: "POST", requires_confirmation: false, result_hint: "refresh_object", variant: "primary" },
              { disabled: false, disabled_reason: null, href: "", icon_key: "database", key: "build_output", label: "Build output", method: "POST", requires_confirmation: false, result_hint: "refresh_object", variant: "primary" },
              { disabled: false, disabled_reason: null, href: "", icon_key: "file-text", key: "build_csv", label: "Build CSV", method: "POST", requires_confirmation: false, result_hint: "refresh_object", variant: "secondary" },
              { disabled: false, disabled_reason: null, href: "", icon_key: "package", key: "export_csv_package", label: "Export package", method: "POST", requires_confirmation: false, result_hint: "refresh_object", variant: "secondary" },
              { disabled: false, disabled_reason: null, href: "", icon_key: "send", key: "register_load_plan_package", label: "Register for Load Plan", method: "POST", requires_confirmation: false, result_hint: "refresh_object", variant: "secondary" }
            ],
            batch_id: "batch_1",
            file_name: "regions_basic_upload.xlsx",
            row_count: 2,
            sheet_count: 2,
            status: "EXPORTED",
            template_code: "REGIONS_BASIC"
          })
        );
      }
      if (parsedUrl.pathname === "/api/v1/modules/master-data/batches/batch_history") {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        batchDetailRequests.push({ method: init?.method ?? "GET", batch_id: "batch_history" });
        return Promise.resolve(
          jsonResponse({
            available_actions: [
              { disabled: true, disabled_reason: "OUTPUT_BUILT_STATUS_REQUIRED", href: "", icon_key: "file-text", key: "build_csv", label: "Build CSV", method: "POST", recommended: false, requires_confirmation: false, result_hint: "refresh_object", variant: "secondary" },
              { disabled: false, disabled_reason: null, href: "", icon_key: "package", key: "export_csv_package", label: "Export package", method: "POST", recommended: true, requires_confirmation: false, result_hint: "refresh_object", variant: "secondary" }
            ],
            batch_id: "batch_history",
            file_name: "regions_history_upload.xlsx",
            row_count: 1,
            sheet_count: 1,
            status: "CSV_BUILT",
            template_code: "REGIONS_BASIC"
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_1/output-records")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        outputRecordListRequests.push({ method: init?.method ?? "GET" });
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                batch_id: "batch_1",
                id: "output_record_region",
                payload: { REGION_GID: "SYN.REGION_BROWSER", REGION_XID: "REGION_BROWSER" },
                record_index: 1,
                target_table: "REGION",
                template_code: "REGIONS_BASIC"
              }
            ],
            total: 1
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_history/output-records")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        outputRecordListRequests.push({ method: init?.method ?? "GET", batch_id: "batch_history" });
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_1/csv-files")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        csvFileListRequests.push({ method: init?.method ?? "GET" });
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                batch_id: "batch_1",
                content_preview: "REGION\nREGION_GID,REGION_XID\nSYN.REGION_BROWSER,REGION_BROWSER",
                file_name: "001_REGION.csv",
                id: "csv_region",
                line_count: 3,
                row_count: 1,
                table_name: "REGION",
                template_code: "REGIONS_BASIC"
              }
            ],
            total: 1
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_history/csv-files")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        csvFileListRequests.push({ method: init?.method ?? "GET", batch_id: "batch_history" });
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/load-plan/packages/from-master-data/batch_1")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        loadPlanRegistrationRequests.push({ method: init?.method });
        return Promise.resolve(
          jsonResponse({
            approval_evidence_id: null,
            artifact_id: "artifact_csv_package",
            created_by: "admin@example.test",
            environment_id: null,
            evidence_id: "evidence_load_plan_package",
            id: "load_plan_master_data_package_1",
            load_sequence: [
              { position: 1, requirement_level: "REQUIRED", row_count: 1, table_name: "REGION" },
              { position: 2, requirement_level: "REQUIRED", row_count: 1, table_name: "REGION_DETAIL" }
            ],
            manifest_id: "manifest_csv_package",
            package_type: "master_data_csv_zip",
            profile_id: null,
            project_id: null,
            registered_at: "2026-05-23T00:00:00",
            source_entity_id: "batch_1",
            source_entity_type: "master_data_batch",
            source_module: "master_data",
            status: "REGISTERED",
            summary: {
              catalog_load_plan_path: "/api/v1/catalog/macro-objects/REGION/load-plan",
              catalog_macro_object_code: "REGION",
              package_type: "master_data_csv_zip",
              row_count: 2,
              table_count: 2
            }
          })
        );
      }
      if (url.endsWith("/api/v1/modules/load-plan/cutover-checklists/from-package/load_plan_master_data_package_1")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        cutoverChecklistRequests.push({ method: init?.method });
        return Promise.resolve(
          jsonResponse({
            catalog_macro_object_code: "REGION",
            created_by: "admin@example.test",
            environment_id: null,
            evidence_id: "evidence_cutover_checklist",
            id: "cutover_checklist_1",
            items: [
              {
                checklist_id: "cutover_checklist_1",
                details: {},
                evidence_id: null,
                evidence_required: true,
                id: "cutover_item_1",
                item_code: "PACKAGE_REGISTERED",
                method: "MANUAL",
                package_id: "load_plan_master_data_package_1",
                sort_order: 1,
                status: "PENDING",
                table_name: null,
                template_item_id: "template_item_1",
                title: "Confirm package registration"
              }
            ],
            package_id: "load_plan_master_data_package_1",
            package_type: "master_data_csv_zip",
            profile_id: null,
            project_id: null,
            status: "DRAFT",
            summary: {
              catalog_macro_object_code: "REGION",
              item_count: 1,
              package_type: "master_data_csv_zip"
            },
            template_code: "DEFAULT_CUTOVER"
          })
        );
      }
      if (url.endsWith("/api/v1/modules/load-plan/cutover-checklists/cutover_checklist_1/readiness")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        cutoverChecklistReadinessRequests.push({ method: init?.method });
        return Promise.resolve(
          jsonResponse({
            blockers: [
              {
                code: "ITEM_PENDING",
                item_code: "PACKAGE_REGISTERED",
                message: "Checklist item is still pending.",
                severity: "ERROR"
              }
            ],
            checklist_id: "cutover_checklist_1",
            evidence_id: "evidence_checklist_readiness",
            package_id: "load_plan_master_data_package_1",
            status: "REVIEW",
            summary: {
              blocker_count: 1,
              blocked_count: 0,
              done_count: 0,
              error_count: 1,
              item_count: 1,
              missing_evidence_count: 1,
              pending_count: 1,
              ready: false,
              skipped_count: 0,
              status_counts: { PENDING: 1 },
              warning_count: 0
            }
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_1/artifacts")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        artifactListRequests.push({ method: init?.method ?? "GET" });
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                artifact_type: "master_data_csv_zip",
                content_type: "application/zip",
                download_url: "/api/v1/modules/master-data/batches/batch_1/artifacts/artifact_csv_package/download",
                evidence_id: "evidence_csv_package",
                file_name: "master_data_regions_basic.zip",
                id: "artifact_csv_package",
                sensitivity_level: "client_safe",
                sha256: "abc123",
                size_bytes: 128
              }
            ],
            total: 1
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_history/artifacts")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        artifactListRequests.push({ method: init?.method ?? "GET", batch_id: "batch_history" });
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                artifact_type: "master_data_csv_file",
                content_type: "text/csv",
                download_url: "/api/v1/modules/master-data/batches/batch_history/artifacts/artifact_history_csv/download",
                evidence_id: "evidence_history_csv",
                file_name: "001_REGION_HISTORY.csv",
                id: "artifact_history_csv",
                sensitivity_level: "client_safe",
                sha256: "def456",
                size_bytes: 64
              }
            ],
            total: 1
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_1/artifacts/artifact_csv_package/download")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        artifactDownloadRequests.push(url);
        return Promise.resolve(
          new Response(new Blob(["synthetic zip"], { type: "application/zip" }), {
            headers: { "Content-Disposition": 'attachment; filename="master_data_regions_basic.zip"' },
            status: 200
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp();
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Data Factory" });
    expect(screen.getByLabelText("Data Factory workflow")).toBeInTheDocument();
    expect(screen.getByLabelText("Master Data templates")).toHaveTextContent("REGIONS_BASIC");
    await screen.findByText("Synthetic starter template for region master data.");
    expect(screen.getByLabelText("Selected Master Data action guidance")).toHaveTextContent("Build workbook");
    expect(screen.getByLabelText("Selected Master Data action guidance")).toHaveTextContent("Recommended next");
    expect(screen.getByLabelText("Selected Master Data action guidance")).toHaveTextContent("TEMPLATE_ALREADY_PUBLISHED");

    await userEvent.click(screen.getByRole("button", { name: /3Workbook/ }));
    await userEvent.click(screen.getByRole("button", { name: "Validate template" }));
    await screen.findByText("Template validation is VALID.");
    expect(screen.getByLabelText("Template validation summary")).toHaveTextContent("VALID");
    await userEvent.click(screen.getByRole("button", { name: "Build workbook" }));
    await screen.findByText("Workbook regions_basic_v1.xlsx generated.");
    expect(screen.getByLabelText("Workbook artifact")).toHaveTextContent("regions_basic_v1.xlsx");

    await userEvent.click(screen.getByRole("button", { name: /4Upload/ }));
    const uploadFile = new File(["synthetic workbook bytes"], "regions_basic_upload.xlsx", {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    });
    await userEvent.upload(screen.getByLabelText("Workbook file"), uploadFile);
    await userEvent.click(screen.getByRole("button", { name: "Upload workbook" }));
    await screen.findByText("Workbook uploaded as batch batch_1.");
    expect(screen.getByLabelText("Active batch summary")).toHaveTextContent("PARSED");

    await userEvent.click(screen.getByRole("button", { name: /5Validate/ }));
    await userEvent.click(screen.getByRole("button", { name: "Validate relationships" }));
    await screen.findByText("Relationship validation is VALID.");
    expect(screen.getByLabelText("Relationship validation summary")).toHaveTextContent("VALID");

    await userEvent.click(screen.getByRole("button", { name: /6Map/ }));
    await userEvent.click(screen.getByRole("button", { name: "Map records" }));
    await screen.findByText("Batch mapping is MAPPED.");
    expect(screen.getByLabelText("Mapping summary")).toHaveTextContent("MAPPED");

    await userEvent.click(screen.getByRole("button", { name: /7Output/ }));
    const outputPanel = screen.getByLabelText("Output and export workflow");
    await userEvent.click(within(outputPanel).getByRole("button", { name: "Build output" }));
    await screen.findByText("Output build is OUTPUT_BUILT.");
    expect(screen.getByLabelText("Master Data output record preview")).toHaveTextContent("REGION");
    await userEvent.click(within(outputPanel).getByRole("button", { name: "Build CSV" }));
    await screen.findByText("CSV build is CSV_BUILT.");
    expect(screen.getByLabelText("Master Data CSV file preview")).toHaveTextContent("001_REGION.csv");
    await userEvent.click(within(outputPanel).getByRole("button", { name: "Export package" }));
    await screen.findByText("CSV package export is EXPORTED.");
    expect(screen.getByLabelText("Export package summary")).toHaveTextContent("artifact_csv_package");
    await userEvent.click(within(outputPanel).getByRole("button", { name: "Register for Load Plan" }));
    await screen.findByText("Load Plan package load_plan_master_data_package_1 registered.");
    expect(screen.getByLabelText("Load Plan package registration")).toHaveTextContent("master_data_csv_zip");
    await userEvent.click(within(outputPanel).getByRole("button", { name: "Create cutover checklist" }));
    await screen.findByText("Cutover checklist cutover_checklist_1 created.");
    expect(screen.getByLabelText("Cutover checklist handoff")).toHaveTextContent("DEFAULT_CUTOVER");
    await userEvent.click(within(outputPanel).getByRole("button", { name: "Generate checklist readiness" }));
    await screen.findByText("Cutover checklist readiness is REVIEW.");
    expect(screen.getByLabelText("Cutover checklist readiness handoff")).toHaveTextContent("1 blocker");
    expect(screen.getByText("Cutover checklist readiness blockers")).toBeInTheDocument();
    expect(screen.getByText("ITEM_PENDING, PACKAGE_REGISTERED")).toBeInTheDocument();
    expect(screen.getByText("Checklist item is still pending.")).toBeInTheDocument();
    await userEvent.selectOptions(screen.getByLabelText("Template filter"), "REGIONS_BASIC");
    await userEvent.selectOptions(screen.getByLabelText("Batch status filter"), "EXPORTED");
    await userEvent.type(screen.getByLabelText("Batch file name filter"), "regions");
    await userEvent.type(screen.getByLabelText("Batch minimum row count"), "2");
    await userEvent.selectOptions(screen.getByLabelText("Batch page size"), "10");
    await screen.findByLabelText("Master Data batch history metrics");
    expect(screen.getByLabelText("Master Data batch history metrics")).toHaveTextContent("Matching batches");
    expect(screen.getByLabelText("Master Data batch history metrics")).toHaveTextContent("Matching rows");
    await screen.findByLabelText("Durable Master Data batches");
    expect(screen.getByLabelText("Durable Master Data batches")).toHaveTextContent("batch_1");
    expect(screen.getByLabelText("Durable Master Data batches")).toHaveTextContent("batch_history");
    expect(screen.getByLabelText("Master Data export artifacts")).toHaveTextContent("master_data_regions_basic.zip");
    await userEvent.click(within(screen.getByLabelText("Master Data export artifacts")).getByRole("button", { name: "Download" }));
    await screen.findByText("Download started: master_data_regions_basic.zip.");
    await userEvent.click(screen.getByRole("button", { name: "Inspect batch batch_history" }));
    expect(screen.getByLabelText("Selected Master Data template")).toHaveTextContent("batch_history");
    expect(screen.getByRole("button", { name: "Active batch batch_history" })).toBeDisabled();
    await screen.findByText("001_REGION_HISTORY.csv");
    await userEvent.click(screen.getByRole("button", { name: "Use latest matching batch" }));
    expect(screen.getByLabelText("Selected Master Data template")).toHaveTextContent("batch_1");
    expect(screen.getByRole("button", { name: "Active batch batch_1" })).toBeDisabled();
    await screen.findByText("master_data_regions_basic.zip");
    await userEvent.click(screen.getByRole("button", { name: "Inspect batch batch_history" }));
    expect(screen.getByLabelText("Selected Master Data template")).toHaveTextContent("batch_history");

    expect(templateValidationRequests).toEqual([{ method: "POST" }]);
    expect(workbookRequests).toEqual([{ method: "POST" }]);
    expect(uploadRequests).toEqual([{ method: "POST" }]);
    expect(relationshipRequests).toEqual([{ method: "POST" }]);
    expect(mapRequests).toEqual([{ method: "POST" }]);
    expect(outputRequests).toEqual([{ method: "POST" }]);
    expect(csvRequests).toEqual([{ method: "POST" }]);
    expect(exportRequests).toEqual([{ method: "POST" }]);
    expect(batchDetailRequests.length).toBeGreaterThanOrEqual(5);
    expect(loadPlanRegistrationRequests).toEqual([{ method: "POST" }]);
    expect(cutoverChecklistRequests).toEqual([{ method: "POST" }]);
    expect(cutoverChecklistReadinessRequests).toEqual([{ method: "POST" }]);
    expect(outputRecordListRequests.length).toBeGreaterThan(0);
    expect(csvFileListRequests.length).toBeGreaterThan(0);
    expect(batchListRequests).toContainEqual({
      file_name_contains: "regions",
      min_row_count: "2",
      method: "GET",
      page_size: "10",
      status: "EXPORTED",
      template_code: "REGIONS_BASIC"
    });
    expect(batchSummaryRequests).toContainEqual({
      file_name_contains: "regions",
      min_row_count: "2",
      method: "GET",
      page: null,
      page_size: null,
      status: "EXPORTED",
      template_code: "REGIONS_BASIC"
    });
    await userEvent.click(screen.getByRole("button", { name: "Reset batch filters" }));
    expect(screen.getByLabelText("Selected Master Data template")).toHaveTextContent("batch_1");
    expect(screen.getByLabelText("Template filter")).toHaveValue("");
    expect(screen.getByLabelText("Batch status filter")).toHaveValue("");
    expect(screen.getByLabelText("Batch file name filter")).toHaveValue("");
    expect(screen.getByLabelText("Batch minimum row count")).toHaveValue(null);
    expect(screen.getByLabelText("Batch page size")).toHaveValue("50");
    await screen.findByLabelText("Master Data batch history metrics");
    expect(batchListRequests).toContainEqual({
      file_name_contains: null,
      min_row_count: null,
      method: "GET",
      page_size: null,
      status: null,
      template_code: null
    });
    expect(batchSummaryRequests).toContainEqual({
      file_name_contains: null,
      min_row_count: null,
      method: "GET",
      page: null,
      page_size: null,
      status: null,
      template_code: null
    });
    expect(batchListRequests.length).toBeGreaterThan(0);
    expect(artifactListRequests.length).toBeGreaterThan(0);
    expect(artifactDownloadRequests).toEqual([
      "/api/v1/modules/master-data/batches/batch_1/artifacts/artifact_csv_package/download"
    ]);

    await userEvent.click(screen.getByRole("link", { name: /Project Cockpit/ }));
    await userEvent.click(screen.getByRole("link", { name: /Data Factory/ }));
    await screen.findByRole("heading", { name: "Data Factory" });
    expect((await screen.findAllByText("REGIONS_BASIC")).length).toBeGreaterThan(0);
  }, 60000);

  it("shows workbook upload details and recovers after replacing the file", async () => {
    const uploadRequests: string[] = [];
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
      if (url.endsWith("/api/v1/modules/master-data/templates")) {
        return Promise.resolve(jsonResponse({ items: [regionsTemplate()], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/REGIONS_BASIC")) {
        return Promise.resolve(jsonResponse(regionsTemplate()));
      }
      if (url.endsWith("/api/v1/modules/master-data/batches")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/REGIONS_BASIC/batches")) {
        expect(init?.body).toBeInstanceOf(FormData);
        uploadRequests.push(init?.method ?? "GET");
        if (uploadRequests.length === 1) {
          return Promise.resolve(
            jsonResponse(
              {
                code: "MASTER_DATA_WORKBOOK_INVALID",
                details: { error: "Uploaded workbook headers do not match REGIONS." },
                message: "Uploaded workbook does not match the template."
              },
              422
            )
          );
        }
        return Promise.resolve(
          jsonResponse({
            batch_id: "batch_recovered",
            file_name: "regions_basic_fixed.xlsx",
            row_count: 2,
            sheet_count: 2,
            sheets: [
              { row_count: 1, sheet_code: "REGIONS" },
              { row_count: 1, sheet_code: "REGION_DETAILS" }
            ],
            status: "PARSED",
            template_code: "REGIONS_BASIC"
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/batches/batch_recovered/artifacts")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp();
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Data Factory" });
    await userEvent.click(screen.getByRole("button", { name: /4Upload/ }));
    const fileInput = screen.getByLabelText("Workbook file");
    await userEvent.upload(
      fileInput,
      new File(["bad workbook"], "regions_basic_bad.xlsx", {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      })
    );
    await userEvent.click(screen.getByRole("button", { name: "Upload workbook" }));
    await screen.findByText("Uploaded workbook does not match the template. Uploaded workbook headers do not match REGIONS.");

    await userEvent.upload(
      fileInput,
      new File(["fixed workbook"], "regions_basic_fixed.xlsx", {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      })
    );
    await userEvent.click(screen.getByRole("button", { name: "Upload workbook" }));
    await screen.findByText("Workbook uploaded as batch batch_recovered.");
    expect(screen.getByLabelText("Active batch summary")).toHaveTextContent("PARSED");
    expect(uploadRequests).toEqual(["POST", "POST"]);
  }, 60000);

  it("authors a dynamic Master Data template through backend-owned contracts", async () => {
    const draftRequests: unknown[] = [];
    const validateDefinitionRequests: unknown[] = [];
    const publishRequests: unknown[] = [];
    const versionRequests: unknown[] = [];
    const columnRequests: unknown[] = [];
    const dynamicTemplate = {
      ...regionsTemplate(),
      available_actions: [
        { disabled: false, disabled_reason: null, href: "", icon_key: "check-circle", key: "validate_definition", label: "Validate definition", method: "POST", requires_confirmation: false, result_hint: "refresh_object", variant: "secondary" },
        { disabled: false, disabled_reason: null, href: "", icon_key: "upload-cloud", key: "publish_template", label: "Publish template", method: "POST", requires_confirmation: false, result_hint: "refresh_object", variant: "secondary" },
        { disabled: true, disabled_reason: "PUBLISHED_TEMPLATE_REQUIRED", href: "", icon_key: "file-spreadsheet", key: "build_workbook", label: "Build workbook", method: "POST", requires_confirmation: false, result_hint: "refresh_object", variant: "secondary" },
        { disabled: true, disabled_reason: "PUBLISHED_TEMPLATE_REQUIRED", href: "", icon_key: "copy", key: "create_version", label: "Create next version", method: "POST", requires_confirmation: false, result_hint: "refresh_object", variant: "secondary" }
      ],
      catalog_macro_object_code: "LOCATION",
      code: "LOCATIONS_DYNAMIC_UI",
      data_category: "MASTER_DATA",
      description: "Synthetic UI authored template.",
      id: "template_locations_dynamic_ui",
      name: "Locations Dynamic UI",
      sheets: [
        {
          code: "LOCATIONS",
          fields: [
            { data_type: "string", label: "Location ID", name: "location_gid", required: true, target_column: "LOCATION_GID" },
            { data_type: "string", label: "Location Name", name: "location_name", required: false, target_column: "LOCATION_NAME" }
          ],
          name: "Locations",
          target_table: "LOCATION"
        }
      ],
      status: "DRAFT",
      target_tables: ["LOCATION"],
      version: 1
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
      if (url.endsWith("/api/v1/modules/master-data/templates")) {
        if (init?.method === "POST") {
          return Promise.reject(new Error("Use /templates/drafts for template authoring."));
        }
        return Promise.resolve(jsonResponse({ items: [regionsTemplate()], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/REGIONS_BASIC")) {
        return Promise.resolve(jsonResponse(regionsTemplate()));
      }
      if (url.endsWith("/api/v1/catalog/macro-objects/LOCATION/tables")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                allow_csvutil: true,
                allow_cutover: true,
                data_category: "MASTER_DATA",
                id: "macro_location",
                is_primary_table: true,
                is_required: true,
                relationship_role: "PRIMARY",
                table_name: "LOCATION",
                validated_by_datadict: true
              },
              {
                allow_csvutil: true,
                allow_cutover: true,
                data_category: "MASTER_DATA",
                id: "macro_location_address",
                is_primary_table: false,
                is_required: false,
                relationship_role: "CHILD",
                table_name: "LOCATION_ADDRESS",
                validated_by_datadict: true
              }
            ],
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/catalog/tables/LOCATION/columns")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        columnRequests.push({ method: init?.method ?? "GET" });
        return Promise.resolve(
          jsonResponse({
            items: [
              { column_name: "LOCATION_GID", data_type: "VARCHAR2", default_value: "", is_constraint: false, is_nullable: false },
              { column_name: "LOCATION_XID", data_type: "VARCHAR2", default_value: "", is_constraint: false, is_nullable: false },
              { column_name: "LOCATION_NAME", data_type: "VARCHAR2", default_value: "", is_constraint: false, is_nullable: true },
              { column_name: "COUNTRY_CODE3_GID", data_type: "VARCHAR2", default_value: "", is_constraint: false, is_nullable: true },
              { column_name: "CITY", data_type: "VARCHAR2", default_value: "", is_constraint: false, is_nullable: true }
            ],
            total: 5
          })
        );
      }
      if (url.endsWith("/api/v1/catalog/tables/LOCATION_ADDRESS/columns")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return Promise.resolve(
          jsonResponse({
            items: [
              { column_name: "LOCATION_GID", data_type: "VARCHAR2", default_value: "", is_constraint: false, is_nullable: false },
              { column_name: "ADDRESS_LINE", data_type: "VARCHAR2", default_value: "", is_constraint: false, is_nullable: true }
            ],
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/drafts")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init?.body));
        draftRequests.push({
          code: body.code,
          fields: body.fields.map((field: { field_key: string; label: string }) => ({
            field_key: field.field_key,
            label: field.label
          })),
          method: init?.method,
          mappings: body.mappings.map((mapping: { default_value?: string; source_type: string; target_column: string; target_table: string }) => ({
            default_value: mapping.default_value,
            source_type: mapping.source_type,
            target: `${mapping.target_table}.${mapping.target_column}`
          })),
          relationship_rules: body.relationship_rules,
          target_tables: body.target_tables.map((table: { table_name: string }) => table.table_name)
        });
        return Promise.resolve(jsonResponse(dynamicTemplate));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/LOCATIONS_DYNAMIC_UI/validate-definition")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        validateDefinitionRequests.push({ method: init?.method });
        return Promise.resolve(
          jsonResponse({
            issues: [],
            severity: "INFO",
            summary: { field_count: 2, mapping_count: 4, sheet_count: 1, target_table_count: 1, validated_table_count: 1 },
            template_code: "LOCATIONS_DYNAMIC_UI",
            valid: true
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/LOCATIONS_DYNAMIC_UI/publish")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        publishRequests.push({ method: init?.method });
        return Promise.resolve(
          jsonResponse({
            ...dynamicTemplate,
            available_actions: regionsTemplate().available_actions,
            status: "PUBLISHED"
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/LOCATIONS_DYNAMIC_UI/versions")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init?.body));
        versionRequests.push({ method: init?.method, new_code: body.new_code });
        return Promise.resolve(
          jsonResponse({
            ...dynamicTemplate,
            code: "LOCATIONS_DYNAMIC_UI_V2",
            id: "template_locations_dynamic_ui_v2",
            status: "DRAFT",
            version: 2
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp();
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Data Factory" });
    await userEvent.click(screen.getByRole("button", { name: /2Author/ }));
    await screen.findByLabelText("Catalog tables for LOCATION");
    await userEvent.click(screen.getByRole("checkbox", { name: "LOCATION_ADDRESS" }));
    await screen.findByLabelText("Catalog columns for LOCATION");
    await userEvent.click(screen.getByRole("checkbox", { name: "CITY" }));
    const addressColumns = await screen.findByLabelText("Catalog columns for LOCATION_ADDRESS");
    await userEvent.click(within(addressColumns).getByRole("checkbox", { name: "LOCATION_GID" }));
    await userEvent.click(screen.getByRole("checkbox", { name: "Require LOCATION parent for LOCATION_ADDRESS" }));
    await userEvent.click(screen.getByRole("checkbox", { name: "LOCATION_ADDRESS" }));
    expect(screen.queryByLabelText("Catalog columns for LOCATION_ADDRESS")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("checkbox", { name: "LOCATION_ADDRESS" }));
    await screen.findByLabelText("Catalog columns for LOCATION_ADDRESS");
    expect(screen.getByRole("checkbox", { name: "Require LOCATION parent for LOCATION_ADDRESS" })).toBeDisabled();
    expect(screen.getByRole("checkbox", { name: "Require LOCATION parent for LOCATION_ADDRESS" })).not.toBeChecked();
    const resetAddressColumns = await screen.findByLabelText("Catalog columns for LOCATION_ADDRESS");
    await userEvent.click(within(resetAddressColumns).getByRole("checkbox", { name: "LOCATION_GID" }));
    await userEvent.click(within(resetAddressColumns).getByRole("checkbox", { name: "ADDRESS_LINE" }));
    await userEvent.clear(screen.getByLabelText("Friendly label for LOCATION_ADDRESS.ADDRESS_LINE"));
    await userEvent.type(screen.getByLabelText("Friendly label for LOCATION_ADDRESS.ADDRESS_LINE"), "Street line for user upload");
    await userEvent.selectOptions(screen.getByLabelText("Source type for LOCATION.CITY"), "DEFAULT_VALUE");
    await userEvent.type(screen.getByLabelText("Default value for LOCATION.CITY"), "UNKNOWN_CITY");
    await userEvent.click(screen.getByRole("checkbox", { name: "Require LOCATION parent for LOCATION_ADDRESS" }));
    expect(screen.getByLabelText("Authoring mapping preview")).toHaveTextContent("LOCATION + LOCATION_ADDRESS");
    expect(screen.getByLabelText("Authoring mapping preview")).toHaveTextContent("5 user field(s)");
    expect(screen.getByLabelText("Authoring mapping preview")).toHaveTextContent("7 OTM mapping(s)");
    expect(screen.getByLabelText("Authoring mapping preview")).toHaveTextContent("1 relationship rule(s)");
    await userEvent.clear(screen.getByLabelText("Template code"));
    await userEvent.type(screen.getByLabelText("Template code"), "LOCATIONS_DYNAMIC_UI");
    await userEvent.clear(screen.getByLabelText("Template name"));
    await userEvent.type(screen.getByLabelText("Template name"), "Locations Dynamic UI");
    await userEvent.click(screen.getByRole("button", { name: "Create draft" }));

    await screen.findByText("Draft LOCATIONS_DYNAMIC_UI created.");
    expect(screen.getByLabelText("Authoring result")).toHaveTextContent("DRAFT");
    await userEvent.click(screen.getByRole("button", { name: "Validate definition" }));
    await screen.findByText("Definition validation is VALID.");
    await userEvent.click(screen.getByRole("button", { name: "Publish template" }));
    await screen.findByText("Template LOCATIONS_DYNAMIC_UI published.");
    await userEvent.click(screen.getByRole("button", { name: "Create next version" }));
    await screen.findByText("Version LOCATIONS_DYNAMIC_UI_V2 created.");

    expect(columnRequests).toEqual([{ method: "GET" }]);
    expect(draftRequests).toEqual([
      {
        code: "LOCATIONS_DYNAMIC_UI",
        fields: expect.arrayContaining([
          { field_key: "location_address_address_line", label: "Street line for user upload" }
        ]),
        method: "POST",
        mappings: [
          { default_value: undefined, source_type: "USER_FIELD", target: "LOCATION.LOCATION_GID" },
          { default_value: undefined, source_type: "USER_FIELD", target: "LOCATION.LOCATION_XID" },
          { default_value: undefined, source_type: "USER_FIELD", target: "LOCATION.LOCATION_NAME" },
          { default_value: undefined, source_type: "FIXED_VALUE", target: "LOCATION.COUNTRY_CODE3_GID" },
          { default_value: "UNKNOWN_CITY", source_type: "DEFAULT_VALUE", target: "LOCATION.CITY" },
          { default_value: undefined, source_type: "USER_FIELD", target: "LOCATION_ADDRESS.LOCATION_GID" },
          { default_value: undefined, source_type: "USER_FIELD", target: "LOCATION_ADDRESS.ADDRESS_LINE" }
        ],
        relationship_rules: [
          {
            child_field_key: "location_address_location_gid",
            child_sheet_code: "LOCATION_ADDRESS",
            parent_field_key: "location_gid",
            parent_sheet_code: "LOCATIONS",
            rule_key: "location_to_location_address",
            severity: "ERROR"
          }
        ],
        target_tables: ["LOCATION", "LOCATION_ADDRESS"]
      }
    ]);
    expect(validateDefinitionRequests).toEqual([{ method: "POST" }]);
    expect(publishRequests).toEqual([{ method: "POST" }]);
    expect(versionRequests).toEqual([{ method: "POST", new_code: "LOCATIONS_DYNAMIC_UI_V2" }]);
  }, 60000);

  it("recovers an existing backend-owned template definition into the Author stage", async () => {
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
              { id: "master_data", label: "Data Factory", path: "/master-data", status: "ACTIVE" }
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
      if (url.endsWith("/api/v1/modules/master-data/templates")) {
        return Promise.resolve(jsonResponse({ items: [regionsTemplate(), recoveredLocationsTemplate()], total: 2 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/REGIONS_BASIC")) {
        return Promise.resolve(jsonResponse(regionsTemplate()));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/LOCATIONS_RECOVERED")) {
        return Promise.resolve(jsonResponse(recoveredLocationsTemplate()));
      }
      if (url.endsWith("/api/v1/catalog/macro-objects/LOCATION/tables")) {
        return Promise.resolve(
          jsonResponse({
            items: [
              { relationship_role: "PRIMARY", table_name: "LOCATION" },
              { relationship_role: "CHILD", table_name: "LOCATION_ADDRESS" }
            ],
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/catalog/tables/LOCATION/columns")) {
        return Promise.resolve(
          jsonResponse({
            items: [
              { column_name: "LOCATION_GID", data_type: "VARCHAR2", is_constraint: false, is_nullable: false },
              { column_name: "CITY", data_type: "VARCHAR2", is_constraint: false, is_nullable: true }
            ],
            total: 2
          })
        );
      }
      if (url.endsWith("/api/v1/catalog/tables/LOCATION_ADDRESS/columns")) {
        return Promise.resolve(
          jsonResponse({
            items: [
              { column_name: "LOCATION_GID", data_type: "VARCHAR2", is_constraint: false, is_nullable: false },
              { column_name: "ADDRESS_LINE", data_type: "VARCHAR2", is_constraint: false, is_nullable: true }
            ],
            total: 2
          })
        );
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp();
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Data Factory" });
    await userEvent.click(screen.getByText("LOCATIONS_RECOVERED"));
    await userEvent.click(screen.getByRole("button", { name: /2Author/ }));
    await userEvent.click(screen.getByRole("button", { name: "Load selected template" }));

    expect(screen.getByLabelText("Template code")).toHaveValue("LOCATIONS_RECOVERED");
    expect(screen.getByLabelText("Template name")).toHaveValue("Locations Recovered");
    expect(screen.getByRole("checkbox", { name: "LOCATION_ADDRESS" })).toBeChecked();
    expect(screen.getByLabelText("Friendly label for LOCATION_ADDRESS.ADDRESS_LINE")).toHaveValue("Street line recovered");
    expect(screen.getByLabelText("Source type for LOCATION.CITY")).toHaveValue("DEFAULT_VALUE");
    expect(screen.getByLabelText("Default value for LOCATION.CITY")).toHaveValue("UNKNOWN_CITY");
    expect(screen.getByRole("checkbox", { name: "Require LOCATION parent for LOCATION_ADDRESS" })).toBeChecked();
  }, 60000);
});
