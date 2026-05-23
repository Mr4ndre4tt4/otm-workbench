import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "../platform/auth";

function renderFunctionalApp(initialPath = "/evidence") {
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

function evidenceItem(id = "evidence_1") {
  return {
    artifact: {
      artifact_type: "rates_csv_zip",
      content_type: "application/zip",
      created_at: "2026-05-22T00:00:00",
      file_name: "synthetic_rates_export.zip",
      id: "artifact_1",
      sensitivity_level: "client_safe",
      sha256: "a".repeat(64),
      size_bytes: 42,
      source_module: "rates"
    },
    client_safe: true,
    created_at: "2026-05-22T00:00:00",
    evidence_type: "rates_csv_export",
    id,
    manifest: {
      created_at: "2026-05-22T00:00:00",
      id: "manifest_1",
      manifest_type: "rates_csv_export",
      schema_version: "rates-csv-export-manifest/v1",
      source_module: "rates",
      status: "CREATED"
    },
    project_id: "SYN_PROJECT",
    sensitivity_level: "client_safe",
    source_module: "rates",
    status: "CREATED",
    summary: { artifact_ref_count: 1, status: "ok" }
  };
}

function archiveEvidenceItem() {
  return {
    artifact: {
      artifact_type: "evidence_hub_archive_zip",
      content_type: "application/zip",
      created_at: "2026-05-22T00:00:00",
      file_name: "evidence_hub_archive.zip",
      id: "artifact_archive",
      sensitivity_level: "internal",
      sha256: "b".repeat(64),
      size_bytes: 128,
      source_module: "evidence_hub"
    },
    client_safe: true,
    created_at: "2026-05-22T00:00:00",
    evidence_type: "evidence_hub_archive",
    id: "evidence_archive",
    manifest: {
      created_at: "2026-05-22T00:00:00",
      id: "manifest_archive",
      manifest_type: "evidence_hub_archive",
      schema_version: "evidence-hub-archive-manifest/v1",
      source_module: "evidence_hub",
      status: "CREATED"
    },
    project_id: null,
    sensitivity_level: "client_safe",
    source_module: "evidence_hub",
    status: "CREATED",
    summary: { artifact_ref_count: 1, evidence_count: 1, manifest_ref_count: 1 }
  };
}

describe("Functional Evidence Hub journey", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("filters evidence, inspects detail, downloads artifact, creates archive, and returns with backend state", async () => {
    const evidenceRequests: string[] = [];
    const detailRequests: string[] = [];
    const downloadRequests: string[] = [];
    const archiveRequests: unknown[] = [];
    const createObjectUrl = vi.fn(() => "blob:synthetic-evidence");
    const revokeObjectUrl = vi.fn();
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: createObjectUrl
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: revokeObjectUrl
    });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);

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
              { id: "evidence", label: "Evidence Hub", path: "/evidence", status: "ACTIVE" }
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
      if (
        url.includes("/api/v1/evidence-hub/evidence?") &&
        url.includes("source_module=evidence_hub") &&
        url.includes("evidence_type=evidence_hub_archive")
      ) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        evidenceRequests.push(url);
        return Promise.resolve(jsonResponse({ items: [archiveEvidenceItem()], total: 1 }));
      }
      if (url.includes("/api/v1/evidence-hub/evidence?")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        evidenceRequests.push(url);
        return Promise.resolve(jsonResponse({ items: [evidenceItem()], total: 1 }));
      }
      if (url.endsWith("/api/v1/evidence-hub/evidence")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        evidenceRequests.push(url);
        return Promise.resolve(jsonResponse({ items: [evidenceItem()], total: 1 }));
      }
      if (url.endsWith("/api/v1/evidence-hub/evidence/evidence_1")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        detailRequests.push(url);
        return Promise.resolve(jsonResponse(evidenceItem()));
      }
      if (url.endsWith("/api/v1/evidence-hub/evidence/evidence_archive")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        detailRequests.push(url);
        return Promise.resolve(jsonResponse(evidenceItem("evidence_archive")));
      }
      if (url.endsWith("/api/v1/evidence-hub/artifacts/artifact_1/download")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        downloadRequests.push(url);
        return Promise.resolve(
          new Response(new Blob(["synthetic archive"], { type: "application/zip" }), {
            headers: {
              "Content-Disposition": 'attachment; filename="synthetic_rates_export.zip"',
              "Content-Type": "application/zip"
            },
            status: 200
          })
        );
      }
      if (url.endsWith("/api/v1/evidence-hub/archive-packages")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        archiveRequests.push(JSON.parse(String(init?.body)));
        return Promise.resolve(
          jsonResponse({
            archive_id: "artifact_archive",
            artifact_id: "artifact_archive",
            evidence_id: "evidence_archive",
            file_name: "evidence_hub_archive.zip",
            manifest_id: "manifest_archive",
            sha256: "b".repeat(64),
            size_bytes: 128,
            summary: { artifact_ref_count: 1, evidence_count: 1, manifest_ref_count: 1 }
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

    await screen.findByRole("heading", { name: "Evidence Hub" });
    expect(screen.getByLabelText("Evidence Hub workflow")).toHaveTextContent("Find");
    expect(screen.getByLabelText("Evidence entries")).toHaveTextContent("rates_csv_export");
    await screen.findByText("synthetic_rates_export.zip");
    expect(screen.getByLabelText("Selected evidence")).toHaveTextContent("synthetic_rates_export.zip");
    const resetEvidenceFilters = within(screen.getByLabelText("Evidence filters"));
    await userEvent.clear(resetEvidenceFilters.getByLabelText("Source module"));
    await userEvent.type(resetEvidenceFilters.getByLabelText("Source module"), "rates");
    await userEvent.clear(resetEvidenceFilters.getByLabelText("Evidence type"));
    await userEvent.type(resetEvidenceFilters.getByLabelText("Evidence type"), "rates_csv_export");
    await userEvent.clear(resetEvidenceFilters.getByLabelText("Status"));
    await userEvent.type(resetEvidenceFilters.getByLabelText("Status"), "CREATED");
    await userEvent.clear(resetEvidenceFilters.getByLabelText("Sensitivity"));
    await userEvent.type(resetEvidenceFilters.getByLabelText("Sensitivity"), "client_safe");
    await userEvent.click(screen.getByRole("button", { name: "Apply filters" }));
    await screen.findByText("Evidence filters applied.");
    await waitFor(() => {
      expect(evidenceRequests.some((request) => request.includes("source_module=rates"))).toBe(true);
    });
    expect(evidenceRequests.some((request) => request.includes("evidence_type=rates_csv_export"))).toBe(true);
    expect(evidenceRequests.some((request) => request.includes("sensitivity_level=client_safe"))).toBe(true);

    await userEvent.click(screen.getByRole("button", { name: "Reset filters" }));
    await screen.findByText("Evidence filters reset.");
    await waitFor(() => {
      const resetEvidenceFilters = within(screen.getByLabelText("Evidence filters"));
      expect(resetEvidenceFilters.getByLabelText("Source module")).toHaveValue("");
      expect(resetEvidenceFilters.getByLabelText("Evidence type")).toHaveValue("");
      expect(resetEvidenceFilters.getByLabelText("Status")).toHaveValue("");
      expect(resetEvidenceFilters.getByLabelText("Project")).toHaveValue("");
      expect(resetEvidenceFilters.getByLabelText("Sensitivity")).toHaveValue("");
      expect(resetEvidenceFilters.getByLabelText("Artifact")).toHaveValue("");
      expect(resetEvidenceFilters.getByLabelText("Manifest")).toHaveValue("");
    });
    await waitFor(() => {
      expect(evidenceRequests.at(-1)?.endsWith("/api/v1/evidence-hub/evidence")).toBe(true);
    });

    const reappliedEvidenceFilters = within(screen.getByLabelText("Evidence filters"));
    await userEvent.clear(reappliedEvidenceFilters.getByLabelText("Source module"));
    await userEvent.type(reappliedEvidenceFilters.getByLabelText("Source module"), "rates");
    await userEvent.clear(reappliedEvidenceFilters.getByLabelText("Evidence type"));
    await userEvent.type(reappliedEvidenceFilters.getByLabelText("Evidence type"), "rates_csv_export");
    await userEvent.clear(reappliedEvidenceFilters.getByLabelText("Status"));
    await userEvent.type(reappliedEvidenceFilters.getByLabelText("Status"), "CREATED");
    await userEvent.clear(reappliedEvidenceFilters.getByLabelText("Sensitivity"));
    await userEvent.type(reappliedEvidenceFilters.getByLabelText("Sensitivity"), "client_safe");
    await userEvent.click(screen.getByRole("button", { name: "Apply filters" }));
    await screen.findByText("Evidence filters applied.");

    await userEvent.click(screen.getByRole("button", { name: "Download artifact" }));
    await screen.findByText("Artifact synthetic_rates_export.zip downloaded through Evidence Hub.");
    expect(downloadRequests).toHaveLength(1);
    expect(createObjectUrl).toHaveBeenCalledTimes(1);
    expect(revokeObjectUrl).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByRole("button", { name: "Create archive" }));
    await screen.findByText("Archive package evidence_hub_archive.zip created.");
    expect(archiveRequests).toEqual([
      {
        evidence_type: "rates_csv_export",
        sensitivity_level: "client_safe",
        source_module: "rates",
        status: "CREATED"
      }
    ]);
    expect(screen.getByLabelText("Latest archive package")).toHaveTextContent("artifact_archive");
    expect(screen.getByLabelText("Archive package history")).toHaveTextContent("evidence_hub_archive.zip");
    expect(screen.getByLabelText("Archive package history")).toHaveTextContent("1 evidence");

    await userEvent.click(screen.getByRole("link", { name: /Project Cockpit/ }));
    await userEvent.click(screen.getByRole("link", { name: /Evidence Hub/ }));
    await screen.findByRole("heading", { name: "Evidence Hub" });
    expect(within(screen.getByLabelText("Evidence entries")).getByText("rates_csv_export")).toBeInTheDocument();
    expect(detailRequests.length).toBeGreaterThan(0);
  }, 60000);
});
