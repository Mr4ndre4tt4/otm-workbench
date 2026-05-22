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

describe("Functional Load Plan journey", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
  });

  it("creates a checklist, updates an item, generates readiness, and returns with backend state", async () => {
    let checklistCreated = false;
    let itemDone = false;
    let readinessGenerated = false;
    const checklistRequests: unknown[] = [];
    const itemRequests: unknown[] = [];
    const readinessRequests: unknown[] = [];

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
      if (url.endsWith("/api/v1/modules/load-plan/cutover-handoff/eligibility?package_id=package_1")) {
        return Promise.resolve(
          jsonResponse({
            archive_evidence_id: null,
            blockers: readinessGenerated
              ? [{ code: "READINESS_EXPORT_MISSING", message: "Export readiness first.", severity: "ERROR" }]
              : [{ code: "CUTOVER_READINESS_MISSING", message: "Generate cutover readiness first.", severity: "ERROR" }],
            checklist_id: checklistCreated ? "checklist_1" : null,
            checklist_readiness_evidence_id: readinessGenerated ? "evidence_readiness" : null,
            checklist_readiness_status: readinessGenerated ? "READY" : null,
            eligible: false,
            next_actions: readinessGenerated ? ["READINESS_EXPORT_MISSING"] : ["CUTOVER_READINESS_MISSING"],
            package_id: "package_1",
            readiness_export_evidence_id: null,
            readiness_export_id: null,
            readiness_id: null,
            readiness_status: null,
            status: "INELIGIBLE"
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
    await userEvent.click(within(checklistPanel).getByRole("button", { name: "Mark done" }));
    await screen.findByText("Checklist item updated.");

    await userEvent.click(screen.getByRole("button", { name: /3Readiness/ }));
    await userEvent.click(screen.getByRole("button", { name: "Generate readiness" }));
    await screen.findByText("Checklist readiness is READY.");
    expect(screen.getByLabelText("Cutover readiness summary")).toHaveTextContent("DONE");

    await userEvent.click(screen.getByRole("button", { name: /4Handoff/ }));
    await screen.findByLabelText("Cutover handoff eligibility");
    expect(await screen.findByText("READINESS_EXPORT_MISSING")).toBeInTheDocument();

    expect(checklistRequests).toEqual([{ method: "POST" }]);
    expect(itemRequests).toEqual([{ evidence_id: "SYN_EVIDENCE_001", method: "MANUAL", status: "DONE" }]);
    expect(readinessRequests).toEqual([{ method: "POST" }]);
    expect(itemDone).toBe(true);

    await userEvent.click(screen.getByRole("link", { name: /Project Cockpit/ }));
    await userEvent.click(screen.getByRole("link", { name: /Load Plan/ }));
    await screen.findByRole("heading", { name: "Load Plan" });
    expect((await screen.findAllByText("rates_csv_zip")).length).toBeGreaterThan(0);
  }, 60000);
});
