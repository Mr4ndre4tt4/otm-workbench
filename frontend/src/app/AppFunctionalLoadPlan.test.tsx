import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "../platform/auth";

function renderFunctionalApp(initialPath = "/load-plan") {
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

function loadPlanPackage(status = "REGISTERED") {
  return {
    approval_evidence_id: "evidence_approval",
    artifact_id: "artifact_export",
    created_by: "admin@example.test",
    environment_id: null,
    evidence_id: "evidence_package",
    id: "package_1",
    load_sequence: [
      { position: 10, requirement_level: "REQUIRED", row_count: 2, table_name: "RATE_GEO_COST" },
      { position: 20, requirement_level: "REQUIRED", row_count: 1, table_name: "RATE_GEO_COST_GROUP" }
    ],
    manifest_id: "manifest_1",
    package_type: "rates_csv_zip",
    profile_id: null,
    project_id: null,
    registered_at: "2026-05-22T00:00:00",
    source_entity_id: "batch_1",
    source_entity_type: "rate_batch",
    source_module: "rates",
    status,
    summary: {
      catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
      catalog_macro_object_code: "RATE_RECORD",
      row_count: 3,
      table_count: 2
    }
  };
}

function cutoverChecklist(itemStatus = "PENDING") {
  return {
    catalog_macro_object_code: "RATE_RECORD",
    created_by: "admin@example.test",
    environment_id: null,
    evidence_id: null,
    id: "checklist_1",
    items: [
      {
        checklist_id: "checklist_1",
        details: { position: 10, row_count: 2, requirement_level: "REQUIRED" },
        evidence_id: itemStatus === "DONE" ? "SYN_EVIDENCE_001" : null,
        evidence_required: true,
        id: "item_1",
        item_code: "TABLE_READY",
        method: itemStatus === "DONE" ? "MANUAL" : "CSVUTIL",
        package_id: "package_1",
        sort_order: 100,
        status: itemStatus,
        table_name: "RATE_GEO_COST",
        template_item_id: "template_item_1",
        title: "Confirm RATE_GEO_COST readiness"
      }
    ],
    package_id: "package_1",
    package_type: "rates_csv_zip",
    profile_id: null,
    project_id: null,
    status: "DRAFT",
    summary: {
      catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
      catalog_macro_object_code: "RATE_RECORD",
      item_count: 1,
      package_item_count: 2,
      package_status: "REGISTERED",
      package_type: "rates_csv_zip",
      source_module: "rates",
      status_counts: { [itemStatus]: 1 },
      table_item_count: 1
    },
    template_code: "MVP0_STANDARD_CUTOVER",
    template_id: "template_1"
  };
}

function csvutilBuild() {
  return {
    built_at: "2026-05-22T00:05:00",
    cl_artifact_id: "artifact_csvutil_cl",
    created_by: "admin@example.test",
    ctl_artifact_id: "artifact_csvutil_ctl",
    environment_id: null,
    evidence_id: "evidence_csvutil",
    id: "csvutil_build_1",
    manifest_id: "manifest_csvutil",
    package_id: "package_1",
    profile_id: null,
    project_id: null,
    status: "BUILT",
    summary: {
      catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
      catalog_macro_object_code: "RATE_RECORD",
      package_type: "rates_csv_zip",
      parameter_set: {
        date_format: "YYYY-MM-DD HH24:MI:SS",
        delimiter: "COMMA",
        encoding: "UTF-8",
        mode: "INSERT"
      },
      row_count: 3,
      table_count: 2
    }
  };
}

function zipAnalysis() {
  return {
    analyzed_at: "2026-05-22T00:10:00",
    created_by: "admin@example.test",
    environment_id: null,
    evidence_id: "evidence_zip_analysis",
    findings: [
      {
        code: "CSV_UNKNOWN_COLUMN",
        details: { column_name: "SYNTHETIC_UNKNOWN_COLUMN" },
        file_name: "csv/001_RATE_GEO_COST.csv",
        message: "A CSV column was not found in the local OTM Data Dictionary.",
        severity: "ERROR",
        table_name: "RATE_GEO_COST"
      }
    ],
    id: "zip_analysis_1",
    manifest_id: "manifest_zip_analysis",
    package_id: "package_1",
    profile_id: null,
    project_id: null,
    source_artifact_id: "artifact_export",
    source_manifest_id: "manifest_1",
    status: "ANALYZED",
    summary: {
      catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
      catalog_macro_object_code: "RATE_RECORD",
      csv_file_count: 1,
      error_count: 1,
      finding_count: 1,
      package_type: "rates_csv_zip",
      row_count: 3,
      table_count: 2,
      warning_count: 0
    }
  };
}

function reviewItem(status = "PENDING_REVIEW", latestDecisionStatus: string | null = null) {
  return {
    category: "DATA_DICTIONARY",
    created_at: "2026-05-22T00:11:00",
    created_by: "admin@example.test",
    description: "A CSV column was not found in the local OTM Data Dictionary and needs review before load planning continues.",
    details: { column_name: "SYNTHETIC_UNKNOWN_COLUMN" },
    environment_id: null,
    file_name: "csv/001_RATE_GEO_COST.csv",
    id: "review_item_1",
    latest_decided_at: latestDecisionStatus ? "2026-05-22T00:12:00" : null,
    latest_decision_id: latestDecisionStatus ? "review_decision_1" : null,
    latest_decision_status: latestDecisionStatus,
    package_id: "package_1",
    profile_id: null,
    project_id: null,
    severity: "ERROR",
    source_code: "CSV_UNKNOWN_COLUMN",
    source_type: "zip_analysis_finding",
    status,
    table_name: "RATE_GEO_COST",
    title: "Unknown OTM Data Dictionary column",
    zip_analysis_id: "zip_analysis_1"
  };
}

function packageReadiness() {
  return {
    blockers: [
      {
        code: "SEQUENCE_SNAPSHOT_MISSING",
        details: {},
        message: "Generate a sequence snapshot before final readiness.",
        severity: "ERROR",
        source_id: null,
        source_type: null,
        table_name: null
      }
    ],
    environment_id: null,
    evidence_id: "evidence_package_readiness",
    generated_at: "2026-05-22T00:13:00",
    generated_by: "admin@example.test",
    id: "package_readiness_1",
    package_id: "package_1",
    profile_id: null,
    project_id: null,
    readiness: {
      checks: [],
      status: "MISSING_SEQUENCE"
    },
    sequence_snapshot_id: null,
    status: "MISSING_SEQUENCE",
    summary: {
      blocker_count: 1,
      catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
      catalog_macro_object_code: "RATE_RECORD",
      next_actions: ["generate_sequence_snapshot"]
    }
  };
}

function readinessExport() {
  return {
    artifact_id: "artifact_readiness_export",
    environment_id: null,
    evidence_id: "evidence_readiness_export",
    exported_at: "2026-05-22T00:14:00",
    exported_by: "admin@example.test",
    id: "readiness_export_1",
    manifest_id: "manifest_readiness_export",
    package_id: "package_1",
    profile_id: null,
    project_id: null,
    readiness_id: "package_readiness_1",
    status: "EXPORTED",
    summary: {
      blocker_count: 1,
      catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
      catalog_macro_object_code: "RATE_RECORD",
      readiness_status: "MISSING_SEQUENCE"
    }
  };
}

function cutoverPackageExport() {
  return {
    artifact_id: "artifact_cutover_package",
    catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
    catalog_macro_object_code: "RATE_RECORD",
    checklist_id: "checklist_1",
    content_type: "application/zip",
    csvutil_build_count: 1,
    evidence_id: "evidence_cutover_package",
    exported_at: "2026-05-22T00:15:00",
    exported_by: "admin@example.test",
    file_name: "cutover_package_checklist_1.zip",
    manifest_id: "manifest_cutover_package",
    package_id: "package_1",
    readiness_evidence_id: "evidence_readiness",
    readiness_status: "READY",
    status: "EXPORTED"
  };
}

function sequenceSnapshot() {
  return {
    blockers: [
      {
        code: "PACKAGE_PARENT_TABLE_MISSING",
        details: { parent_table_name: "RATE_GEO_COST_GROUP" },
        message: "A Data Dictionary parent table is not present in this package sequence.",
        severity: "ERROR",
        source_id: "RATE_GEO_COST_GROUP",
        source_type: "otm_data_dictionary",
        table_name: "RATE_GEO_COST"
      }
    ],
    environment_id: null,
    evidence_id: "evidence_sequence_snapshot",
    generated_at: "2026-05-22T00:12:30",
    generated_by: "admin@example.test",
    id: "sequence_snapshot_1",
    package_id: "package_1",
    profile_id: null,
    project_id: null,
    sequence: [
      {
        dictionary_table_found: true,
        missing_parent_tables_in_package: ["RATE_GEO_COST_GROUP"],
        parent_tables: ["RATE_GEO_COST_GROUP"],
        position: 10,
        requirement_level: "REQUIRED",
        review: { confirmed_count: 1, pending_count: 0 },
        row_count: 2,
        table_name: "RATE_GEO_COST",
        zip_analysis: {
          error_count: 0,
          finding_count: 0,
          latest_analysis_id: "zip_analysis_1",
          warning_count: 0
        }
      }
    ],
    status: "BLOCKED",
    summary: {
      blocker_count: 1,
      catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
      catalog_macro_object_code: "RATE_RECORD",
      error_count: 1,
      next_actions: ["review_package_dependencies"],
      row_count: 2,
      table_count: 1,
      warning_count: 0
    }
  };
}

function goNoGoDecision() {
  return {
    blocker_count: 0,
    blockers: [],
    catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
    catalog_macro_object_code: "RATE_RECORD",
    checklist_id: "checklist_1",
    cutover_package_evidence_id: "evidence_cutover_package",
    decided_at: "2026-05-22T00:16:00",
    decided_by: "admin@example.test",
    decision: "GO",
    evidence_id: "evidence_go_no_go",
    package_id: "package_1",
    readiness_evidence_id: "evidence_readiness",
    readiness_status: "READY"
  };
}

function cutoverHandoffCommit() {
  return {
    archive_evidence_id: "evidence_archive_1",
    committed_at: "2026-05-22T00:17:00",
    committed_by: "admin@example.test",
    environment_id: null,
    evidence_id: "evidence_cutover_handoff",
    id: "handoff_1",
    package_id: "package_1",
    profile_id: null,
    project_id: null,
    readiness_export_id: "readiness_export_1",
    readiness_id: "package_readiness_1",
    status: "READY_FOR_CUTOVER",
    summary: {
      archive_evidence_id: "evidence_archive_1",
      package_id: "package_1",
      readiness_export_id: "readiness_export_1",
      readiness_id: "package_readiness_1",
      status: "READY_FOR_CUTOVER"
    }
  };
}

function readinessArchivePackage() {
  return {
    archive_id: "artifact_archive_1",
    artifact_id: "artifact_archive_1",
    evidence_id: "evidence_archive_1",
    file_name: "evidence_hub_archive.zip",
    manifest_id: "manifest_archive_1",
    sha256: "c".repeat(64),
    size_bytes: 512,
    summary: {
      artifact_ref_count: 1,
      evidence_count: 1,
      manifest_ref_count: 1
    }
  };
}

describe("Functional Load Plan journey", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
  });

  it("creates a checklist, updates an item, generates readiness, and returns with backend state", async () => {
    let checklistCreated = false;
    let itemDone = false;
    let readinessGenerated = false;
    let reviewQueueGenerated = false;
    let reviewItemConfirmed = false;
    let readinessExported = false;
    let readinessArchived = false;
    let goNoGoDecided = false;
    const checklistRequests: unknown[] = [];
    const cutoverPackageRequests: unknown[] = [];
    const csvutilRequests: unknown[] = [];
    const itemRequests: unknown[] = [];
    const packageReadinessRequests: unknown[] = [];
    const readinessRequests: unknown[] = [];
    const readinessExportRequests: unknown[] = [];
    const archiveRequests: unknown[] = [];
    const reviewDecisionRequests: unknown[] = [];
    const reviewQueueRequests: unknown[] = [];
    const sequenceSnapshotRequests: unknown[] = [];
    const goNoGoRequests: unknown[] = [];
    const handoffCommitRequests: unknown[] = [];
    const zipAnalysisRequests: unknown[] = [];
    const artifactDownloadRequests: string[] = [];
    const createObjectURL = vi.fn(() => "blob:load-plan-artifact");
    const revokeObjectURL = vi.fn();
    const anchorClick = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
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
              { id: "load_plan", label: "Load Plan", path: "/load-plan", status: "ACTIVE" }
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
      if (url.endsWith("/api/v1/modules/load-plan/summary")) {
        return Promise.resolve(
          jsonResponse({
            by_catalog_macro_object: { RATE_RECORD: { catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan", package_count: 1 } },
            by_source_module: { rates: 1 },
            by_status: { REGISTERED: 1 },
            next_actions: ["create_cutover_checklist"],
            registered_packages: 1
          })
        );
      }
      if (url.endsWith("/api/v1/modules/load-plan/packages")) {
        return Promise.resolve(jsonResponse({ items: [loadPlanPackage()], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/load-plan/packages/package_1")) {
        return Promise.resolve(jsonResponse(loadPlanPackage()));
      }
      if (url.endsWith("/api/v1/modules/load-plan/cutover-checklists/from-package/package_1")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        checklistRequests.push({ method: init?.method });
        checklistCreated = true;
        return Promise.resolve(jsonResponse(cutoverChecklist()));
      }
      if (url.endsWith("/api/v1/modules/load-plan/cutover-checklists/items/item_1")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init?.body));
        itemRequests.push(body);
        itemDone = true;
        return Promise.resolve(jsonResponse(cutoverChecklist("DONE")));
      }
      if (url.endsWith("/api/v1/modules/load-plan/cutover-checklists/checklist_1/readiness")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        readinessRequests.push({ method: init?.method });
        readinessGenerated = true;
        return Promise.resolve(
          jsonResponse({
            blockers: [],
            checklist_id: "checklist_1",
            evidence_id: "evidence_readiness",
            package_id: "package_1",
            status: "READY",
            summary: {
              blocked_count: 0,
              blocker_count: 0,
              done_count: 1,
              error_count: 0,
              item_count: 1,
              missing_evidence_count: 0,
              pending_count: 0,
              ready: true,
              skipped_count: 0,
              status_counts: { DONE: 1 },
              warning_count: 0
            }
          })
        );
      }
      if (url.endsWith("/api/v1/modules/load-plan/csvutil/build/from-cutover-checklist/checklist_1")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        csvutilRequests.push({ body: JSON.parse(String(init?.body)), method: init?.method });
        return Promise.resolve(jsonResponse(csvutilBuild()));
      }
      if (url.endsWith("/api/v1/modules/load-plan/zip-analysis")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        zipAnalysisRequests.push(JSON.parse(String(init?.body)));
        return Promise.resolve(jsonResponse(zipAnalysis()));
      }
      if (url.endsWith("/api/v1/modules/load-plan/review-queue?package_id=package_1")) {
        return Promise.resolve(
          jsonResponse({
            items: reviewQueueGenerated ? [reviewItem(reviewItemConfirmed ? "CONFIRMED" : "PENDING_REVIEW", reviewItemConfirmed ? "CONFIRMED" : null)] : [],
            total: reviewQueueGenerated ? 1 : 0
          })
        );
      }
      if (url.endsWith("/api/v1/modules/load-plan/review-queue/from-zip-analysis/zip_analysis_1")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        reviewQueueRequests.push({ method: init?.method });
        reviewQueueGenerated = true;
        return Promise.resolve(
          jsonResponse({
            analysis_id: "zip_analysis_1",
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            catalog_macro_object_code: "RATE_RECORD",
            created_count: 1,
            existing_count: 0,
            items: [reviewItem()],
            package_id: "package_1"
          })
        );
      }
      if (url.endsWith("/api/v1/modules/load-plan/review-queue/review_item_1/decide")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init?.body));
        reviewDecisionRequests.push(body);
        reviewItemConfirmed = true;
        return Promise.resolve(
          jsonResponse({
            catalog_load_plan_path: "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
            catalog_macro_object_code: "RATE_RECORD",
            decided_at: "2026-05-22T00:12:00",
            decided_by: "admin@example.test",
            decision_note: "Synthetic UI review.",
            decision_status: "CONFIRMED",
            environment_id: null,
            evidence_id: "evidence_review_decision",
            id: "review_decision_1",
            package_id: "package_1",
            profile_id: null,
            project_id: null,
            review_item: reviewItem("CONFIRMED", "CONFIRMED"),
            review_item_id: "review_item_1"
          })
        );
      }
      if (url.endsWith("/api/v1/modules/load-plan/sequence/snapshots")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        sequenceSnapshotRequests.push(JSON.parse(String(init?.body)));
        return Promise.resolve(jsonResponse(sequenceSnapshot()));
      }
      if (url.endsWith("/api/v1/modules/load-plan/cutover-readiness/generate")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        packageReadinessRequests.push(JSON.parse(String(init?.body)));
        return Promise.resolve(
          jsonResponse({
            items: [packageReadiness()],
            summary: {
              blocker_count: 1,
              missing_sequence_count: 1,
              next_actions: ["generate_sequence_snapshot"],
              package_count: 1
            }
          })
        );
      }
      if (url.endsWith("/api/v1/modules/load-plan/cutover-readiness/package_readiness_1/export")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        readinessExportRequests.push({ method: init?.method });
        readinessExported = true;
        return Promise.resolve(jsonResponse(readinessExport()));
      }
      if (url.endsWith("/api/v1/modules/load-plan/cutover-checklists/checklist_1/export-package")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        cutoverPackageRequests.push({ method: init?.method });
        return Promise.resolve(jsonResponse(cutoverPackageExport()));
      }
      if (url.endsWith("/api/v1/evidence-hub/archive-packages")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        archiveRequests.push(JSON.parse(String(init?.body)));
        readinessArchived = true;
        return Promise.resolve(jsonResponse(readinessArchivePackage()));
      }
      if (url.includes("/api/v1/evidence-hub/artifacts/") && url.endsWith("/download")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        artifactDownloadRequests.push(url);
        const artifactId = url.split("/artifacts/")[1]?.split("/download")[0] ?? "artifact";
        return Promise.resolve(
          new Response("synthetic load plan artifact", {
            headers: {
              "Content-Disposition": `attachment; filename="${artifactId}.zip"`,
              "Content-Type": "application/zip"
            },
            status: 200
          })
        );
      }
      if (url.endsWith("/api/v1/modules/load-plan/cutover-checklists/checklist_1/go-no-go")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        goNoGoRequests.push(JSON.parse(String(init?.body)));
        goNoGoDecided = true;
        return Promise.resolve(jsonResponse(goNoGoDecision()));
      }
      if (url.endsWith("/api/v1/modules/load-plan/cutover-handoff") && init?.method === "POST") {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        handoffCommitRequests.push(JSON.parse(String(init?.body)));
        return Promise.resolve(jsonResponse(cutoverHandoffCommit()));
      }
      if (url.endsWith("/api/v1/modules/load-plan/cutover-handoff/eligibility?package_id=package_1")) {
        return Promise.resolve(
          jsonResponse({
            archive_evidence_id: readinessArchived ? "evidence_archive_1" : null,
            blockers: goNoGoDecided && readinessArchived
              ? []
              : readinessExported
                ? [{ code: "CUTOVER_READINESS_NOT_READY", message: "Latest readiness is not READY.", severity: "ERROR" }]
                : readinessGenerated
                  ? [{ code: "READINESS_EXPORT_MISSING", message: "Export readiness first.", severity: "ERROR" }]
                  : [{ code: "CUTOVER_READINESS_MISSING", message: "Generate cutover readiness first.", severity: "ERROR" }],
            checklist_id: checklistCreated ? "checklist_1" : null,
            checklist_readiness_evidence_id: readinessGenerated ? "evidence_readiness" : null,
            checklist_readiness_status: readinessGenerated ? "READY" : null,
            eligible: goNoGoDecided && readinessArchived,
            next_actions: readinessExported
              ? goNoGoDecided && readinessArchived
                ? ["commit_cutover_handoff"]
                : ["CUTOVER_READINESS_NOT_READY"]
              : readinessGenerated
                ? ["READINESS_EXPORT_MISSING"]
                : ["CUTOVER_READINESS_MISSING"],
            package_id: "package_1",
            readiness_export_evidence_id: goNoGoDecided ? "evidence_readiness_export" : null,
            readiness_export_id: goNoGoDecided ? "readiness_export_1" : null,
            readiness_id: readinessExported ? "package_readiness_1" : null,
            readiness_status: goNoGoDecided ? "READY" : readinessExported ? "MISSING_SEQUENCE" : null,
            status: goNoGoDecided ? "ELIGIBLE" : "INELIGIBLE"
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

    await screen.findByRole("heading", { name: "Load Plan" });
    expect(screen.getByLabelText("Load Plan workflow")).toBeInTheDocument();
    expect(screen.getByLabelText("Load plan packages")).toHaveTextContent("rates_csv_zip");

    await userEvent.click(screen.getByRole("button", { name: /2Checklist/ }));
    await userEvent.click(screen.getByRole("button", { name: "Create checklist" }));
    await screen.findByText("Checklist MVP0_STANDARD_CUTOVER created for selected package.");
    const checklistPanel = await screen.findByLabelText("Cutover checklist review queue");
    expect(within(checklistPanel).getByText("Confirm RATE_GEO_COST readiness")).toBeInTheDocument();

    await userEvent.clear(screen.getByLabelText("Evidence id"));
    await userEvent.type(screen.getByLabelText("Evidence id"), "SYN_EVIDENCE_001");
    await userEvent.click(within(checklistPanel).getByRole("button", { name: "Mark CSVUTIL ready" }));
    await screen.findByText("Checklist item updated.");

    await userEvent.click(screen.getByRole("button", { name: /3Readiness/ }));
    await userEvent.click(screen.getByRole("button", { name: "Generate readiness" }));
    await screen.findByText("Checklist readiness is READY.");
    expect(screen.getByLabelText("Cutover readiness summary")).toHaveTextContent("DONE");

    await userEvent.click(screen.getByRole("button", { name: /4CSVUTIL/ }));
    await userEvent.click(screen.getByRole("button", { name: "Build CSVUTIL" }));
    await screen.findByText("CSVUTIL build csvutil_build_1 is BUILT.");
    const csvutilPanel = await screen.findByLabelText("CSVUTIL build artifacts");
    expect(csvutilPanel).toHaveTextContent("artifact_csvutil_ctl");
    expect(csvutilPanel).toHaveTextContent("artifact_csvutil_cl");
    expect(csvutilPanel).toHaveTextContent("manifest_csvutil");
    expect(csvutilPanel).toHaveTextContent("evidence_csvutil");
    await userEvent.click(within(csvutilPanel).getAllByRole("button", { name: "Download" })[0]);
    await screen.findByText("Download started: artifact_csvutil_ctl.zip.");

    await userEvent.click(screen.getByRole("button", { name: /5ZIP review/ }));
    await userEvent.click(screen.getByRole("button", { name: "Run ZIP analysis" }));
    await screen.findByText("ZIP analysis zip_analysis_1 is ANALYZED.");
    expect(screen.getByLabelText("ZIP analysis findings")).toHaveTextContent("CSV_UNKNOWN_COLUMN");
    await userEvent.click(screen.getByRole("button", { name: "Generate review queue" }));
    await screen.findByText("Review queue generated with 1 new item(s).");
    const reviewPanel = await screen.findByLabelText("Load Plan review queue");
    expect(reviewPanel).toHaveTextContent("Unknown OTM Data Dictionary column");
    expect(reviewPanel).toHaveTextContent("PENDING_REVIEW");
    await userEvent.click(within(reviewPanel).getByRole("button", { name: "Confirm finding" }));
    await screen.findByText("Review item review_item_1 decided as CONFIRMED.");
    expect(reviewPanel).toHaveTextContent("CONFIRMED");

    await userEvent.click(screen.getByRole("button", { name: /6Sequence/ }));
    await userEvent.click(screen.getByRole("button", { name: "Generate sequence snapshot" }));
    await screen.findByText("Sequence snapshot sequence_snapshot_1 is BLOCKED.");
    const sequencePanel = await screen.findByLabelText("Load Plan sequence snapshot");
    expect(sequencePanel).toHaveTextContent("PACKAGE_PARENT_TABLE_MISSING");
    expect(sequencePanel).toHaveTextContent("review_package_dependencies");

    await userEvent.click(screen.getByRole("button", { name: /7Exports/ }));
    await userEvent.click(screen.getByRole("button", { name: "Generate package readiness" }));
    await screen.findByText("Package readiness package_readiness_1 is MISSING_SEQUENCE.");
    await userEvent.click(screen.getByRole("button", { name: "Export readiness" }));
    await screen.findByText("Readiness export readiness_export_1 is EXPORTED.");
    await userEvent.click(screen.getByRole("button", { name: "Export cutover package" }));
    await screen.findByText("Cutover package export is EXPORTED.");
    const exportsPanel = await screen.findByLabelText("Load Plan export artifacts");
    expect(exportsPanel).toHaveTextContent("artifact_readiness_export");
    expect(exportsPanel).toHaveTextContent("artifact_cutover_package");
    expect(exportsPanel).toHaveTextContent("evidence_cutover_package");
    await userEvent.click(within(exportsPanel).getAllByRole("button", { name: "Download" })[0]);
    await screen.findByText("Download started: artifact_readiness_export.zip.");
    await userEvent.click(screen.getByRole("button", { name: "Archive readiness export" }));
    await screen.findByText("Readiness export archive evidence_hub_archive.zip created.");
    expect(screen.getByLabelText("Load Plan readiness archive package")).toHaveTextContent("evidence_archive_1");

    await userEvent.click(screen.getByRole("button", { name: /8Handoff/ }));
    await screen.findByLabelText("Cutover handoff eligibility");
    expect(await screen.findByText("CUTOVER_READINESS_NOT_READY")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Decide Go/No-Go" }));
    await screen.findByText("Go/No-Go decision is GO.");
    expect(screen.getByLabelText("Cutover go no-go decision")).toHaveTextContent("evidence_go_no_go");
    await screen.findByText("Handoff is eligible.");
    await userEvent.click(screen.getByRole("button", { name: "Commit cutover handoff" }));
    await screen.findByText("Cutover handoff handoff_1 committed.");
    expect(screen.getByLabelText("Cutover handoff commit")).toHaveTextContent("READY FOR CUTOVER");
    expect(screen.getByLabelText("Cutover handoff commit")).toHaveTextContent("evidence_cutover_handoff");

    expect(checklistRequests).toEqual([{ method: "POST" }]);
    expect(csvutilRequests).toEqual([
      {
        body: {
          parameter_set: {
            date_format: "YYYY-MM-DD HH24:MI:SS",
            delimiter: "COMMA",
            encoding: "UTF-8",
            mode: "INSERT"
          }
        },
        method: "POST"
      }
    ]);
    expect(itemRequests).toEqual([{ evidence_id: "SYN_EVIDENCE_001", method: "CSVUTIL", status: "DONE" }]);
    expect(readinessRequests).toEqual([{ method: "POST" }]);
    expect(zipAnalysisRequests).toEqual([{ package_id: "package_1" }]);
    expect(reviewQueueRequests).toEqual([{ method: "POST" }]);
    expect(reviewDecisionRequests).toEqual([{ decision_note: "Synthetic UI review.", decision_status: "CONFIRMED" }]);
    expect(packageReadinessRequests).toEqual([{ package_id: "package_1" }]);
    expect(readinessExportRequests).toEqual([{ method: "POST" }]);
    expect(archiveRequests).toEqual([
      {
        evidence_type: "load_plan_readiness_export",
        sensitivity_level: "client_safe",
        source_module: "load_plan",
        status: "CREATED"
      }
    ]);
    expect(cutoverPackageRequests).toEqual([{ method: "POST" }]);
    expect(sequenceSnapshotRequests).toEqual([{ package_id: "package_1" }]);
    expect(goNoGoRequests).toEqual([{ decision_note: "Synthetic UI go/no-go review." }]);
    expect(handoffCommitRequests).toEqual([{ package_id: "package_1" }]);
    expect(artifactDownloadRequests).toEqual([
      "/api/v1/evidence-hub/artifacts/artifact_csvutil_ctl/download",
      "/api/v1/evidence-hub/artifacts/artifact_readiness_export/download"
    ]);
    expect(createObjectURL).toHaveBeenCalledTimes(2);
    expect(anchorClick).toHaveBeenCalledTimes(2);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:load-plan-artifact");
    expect(itemDone).toBe(true);

    await userEvent.click(screen.getByRole("link", { name: /Project Cockpit/ }));
    await userEvent.click(screen.getByRole("link", { name: /Load Plan/ }));
    await screen.findByRole("heading", { name: "Load Plan" });
    expect((await screen.findAllByText("rates_csv_zip")).length).toBeGreaterThan(0);
  }, 60000);
});
