import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "../platform/auth";

function renderFunctionalApp(initialPath = "/master-data/quality") {
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
    module_summary: { counts_by_status: { ACTIVE: 1 }, items: [], total: 1 },
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

function masterDataTemplate() {
  return {
    catalog_macro_object_code: "LOCATION",
    created_at: "2026-05-23T00:00:00",
    data_category: "MASTER_DATA",
    description: "Client-safe synthetic Location template.",
    id: "template_locations",
    name: "Locations Basic",
    sheets: [
      {
        code: "LOCATIONS",
        fields: [{ label: "Location ID", name: "location_gid", required: true, target_column: "LOCATION_GID" }],
        name: "Locations",
        target_table: "LOCATION"
      }
    ],
    status: "ACTIVE",
    target_tables: ["LOCATION"],
    updated_at: null,
    version: 1,
    code: "LOCATIONS_BASIC"
  };
}

function coordinatePreview() {
  return {
    results: [
      {
        address: { city: "Sao Paulo" },
        country_code3_gid: "BRA",
        diff_lat: null,
        diff_lon: null,
        issue: {},
        lat_new: -23.55,
        lat_orig: null,
        location_gid: "SYN.LOC_QA_001",
        location_name: "Synthetic Preview DC",
        lon_new: -46.63,
        lon_orig: null,
        new_valid_uf: true,
        orig_valid_uf: false,
        postal_code: "01000-000",
        province_code: "SP",
        source: "fake:inline",
        status: "NULL_FILLED"
      }
    ],
    summary: {
      corrected_count: 0,
      divergent_count: 0,
      failed_count: 0,
      ok_count: 0,
      processed_count: 1,
      review_count: 0,
      total_count: 1
    }
  };
}

describe("Functional Coordinate Quality journey", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
  });

  it("previews coordinates, creates a quality batch, exports a package, and returns with backend state", async () => {
    const previewRequests: unknown[] = [];
    const batchRequests: unknown[] = [];
    const exportRequests: unknown[] = [];
    let qualityBatchCreated = false;

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
      if (url.endsWith("/api/v1/catalog/macro-objects")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates")) {
        return Promise.resolve(jsonResponse({ items: [masterDataTemplate()], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates/LOCATIONS_BASIC")) {
        return Promise.resolve(jsonResponse(masterDataTemplate()));
      }
      if (url.endsWith("/api/v1/modules/master-data/batches")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/coordinate-quality/batches")) {
        if (init?.method === "POST") {
          expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
          const body = JSON.parse(String(init?.body));
          batchRequests.push({ record_count: body.records.length, source_type: body.source_type });
          qualityBatchCreated = true;
          return Promise.resolve(
            jsonResponse({
              batch_id: "coordinate_batch_1",
              issues: [],
              provider_mode: "fake",
              status: "PROCESSED",
              summary: coordinatePreview().summary
            })
          );
        }
        return Promise.resolve(
          jsonResponse({
            items: qualityBatchCreated
              ? [{ batch_id: "coordinate_batch_1", issues: [], provider_mode: "fake", status: "PROCESSED", summary: coordinatePreview().summary }]
              : [],
            total: qualityBatchCreated ? 1 : 0
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/coordinate-quality/validate")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        const body = JSON.parse(String(init?.body));
        previewRequests.push({ candidate_count: Object.keys(body.fake_candidates).length, record_count: body.records.length });
        return Promise.resolve(jsonResponse(coordinatePreview()));
      }
      if (url.endsWith("/api/v1/modules/master-data/coordinate-quality/batches/coordinate_batch_1/results")) {
        return Promise.resolve(jsonResponse({ items: coordinatePreview().results, total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/coordinate-quality/batches/coordinate_batch_1/export")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        exportRequests.push({ method: init?.method });
        return Promise.resolve(
          jsonResponse({
            artifact_id: "artifact_coordinate_quality",
            batch_id: "coordinate_batch_1",
            evidence_id: "evidence_coordinate_quality",
            file_name: "coordinate_quality_batch_coordinate_batch_1.zip",
            manifest_id: "manifest_coordinate_quality",
            sha256: "abc123",
            size_bytes: 1024
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

    await screen.findByRole("heading", { name: "Quality Tools" });
    expect(screen.getByRole("link", { name: "Open Lat/Lon Validator" })).toHaveAttribute(
      "href",
      "/master-data/quality/lat-lon"
    );
    expect(screen.queryByLabelText("Data Factory workflow")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Coordinate Quality workflow")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("link", { name: "Open Lat/Lon Validator" }));
    await screen.findByRole("heading", { name: "Lat/Lon Validator" });
    expect(screen.getByRole("link", { name: "Back to Quality Tools" })).toHaveAttribute("href", "/master-data/quality");
    expect(screen.queryByLabelText("Data Factory workflow")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Preview coordinates" }));
    await screen.findByText("Coordinate Quality preview processed 1 location(s).");
    expect(screen.getByLabelText("Coordinate Quality results")).toHaveTextContent("NULL FILLED");

    await userEvent.click(screen.getByRole("button", { name: "Create quality batch" }));
    await screen.findByText("Coordinate Quality batch coordinate_batch_1 created.");
    await screen.findByRole("heading", { name: "coordinate_batch_1" });
    expect(screen.getByLabelText("Coordinate Quality batches")).toHaveTextContent("coordinate_batch_1");
    expect(screen.queryByLabelText("Data Factory workflow")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Export quality package" }));
    await screen.findByText("Coordinate Quality package coordinate_quality_batch_coordinate_batch_1.zip exported.");
    expect(screen.getByLabelText("Coordinate Quality export package")).toHaveTextContent("artifact_coordinate_quality");

    await userEvent.click(screen.getByRole("link", { name: /Project Cockpit/ }));
    await userEvent.click(screen.getByRole("link", { name: /Data Factory/ }));
    await userEvent.click(screen.getByRole("link", { name: /Open Quality Tools/ }));
    await screen.findByRole("heading", { name: "Quality Tools" });
    await userEvent.click(screen.getByRole("link", { name: "Open Lat/Lon Validator" }));
    await screen.findByRole("heading", { name: "Lat/Lon Validator" });
    expect(await screen.findByLabelText("Coordinate Quality batches")).toHaveTextContent("coordinate_batch_1");

    expect(previewRequests).toEqual([{ candidate_count: 2, record_count: 2 }]);
    expect(batchRequests).toEqual([{ record_count: 2, source_type: "api" }]);
    expect(exportRequests).toEqual([{ method: "POST" }]);
  }, 60000);

  it("recovers a Lat/Lon batch detail route directly from the backend", async () => {
    const detailRequests: string[] = [];
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
      if (url.endsWith("/api/v1/catalog/macro-objects")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/templates")) {
        return Promise.resolve(jsonResponse({ items: [masterDataTemplate()], total: 1 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/batches")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/coordinate-quality/batches")) {
        return Promise.resolve(jsonResponse({ items: [], total: 0 }));
      }
      if (url.endsWith("/api/v1/modules/master-data/coordinate-quality/batches/coordinate_batch_1")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        detailRequests.push(url);
        return Promise.resolve(
          jsonResponse({
            batch_id: "coordinate_batch_1",
            issues: [],
            provider_mode: "fake",
            status: "PROCESSED",
            summary: coordinatePreview().summary
          })
        );
      }
      if (url.endsWith("/api/v1/modules/master-data/coordinate-quality/batches/coordinate_batch_1/results")) {
        return Promise.resolve(jsonResponse({ items: coordinatePreview().results, total: 1 }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderFunctionalApp("/master-data/quality/lat-lon/batches/coordinate_batch_1");
    await userEvent.type(screen.getByLabelText("Email"), "admin@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "coordinate_batch_1" });
    expect(screen.getByRole("link", { name: "Back to Quality Tools" })).toHaveAttribute("href", "/master-data/quality");
    expect(await screen.findByLabelText("Coordinate Quality results")).toHaveTextContent("NULL FILLED");
    expect(screen.getByLabelText("Coordinate Quality batches")).toHaveTextContent("coordinate_batch_1");
    expect(screen.queryByLabelText("Data Factory workflow")).not.toBeInTheDocument();
    expect(detailRequests).toHaveLength(1);
  }, 60000);
});
