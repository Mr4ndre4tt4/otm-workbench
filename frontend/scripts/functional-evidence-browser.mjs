/* global console, fetch, process */

import { mkdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const baseUrl = process.env.OTM_WORKBENCH_BASE_URL ?? "http://127.0.0.1:5173";
const apiBaseUrl = process.env.OTM_WORKBENCH_API_BASE_URL ?? "http://127.0.0.1:8000";
const email = process.env.OTM_WORKBENCH_QA_EMAIL ?? "demo@example.test";
const password = process.env.OTM_WORKBENCH_QA_PASSWORD ?? "DemoPass123!";

async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch (error) {
    console.error(
      [
        "BLOCKED: Playwright is not installed in frontend/node_modules.",
        "Install or make it available before running browser functional QA.",
        "Expected package: playwright",
        `Original error: ${error instanceof Error ? error.message : String(error)}`
      ].join("\n")
    );
    process.exitCode = 2;
    return null;
  }
}

async function apiRequest(path, { method = "GET", token, body } = {}) {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!response.ok) {
    throw new Error(`${method} ${path} failed with HTTP ${response.status}: ${await response.text()}`);
  }
  return response.json();
}

function createSyntheticArtifactFile(runId) {
  const dir = resolve(process.cwd(), "..", "var", "artifacts", "evidence-browser-qa");
  mkdirSync(dir, { recursive: true });
  const filePath = join(dir, `synthetic_evidence_${runId}.zip`);
  writeFileSync(filePath, "synthetic evidence browser artifact\n", "utf-8");
  return filePath;
}

async function seedEvidence(token) {
  const runId = Date.now().toString(36);
  const evidenceType = `synthetic_evidence_browser_${runId}`;
  const artifactFile = createSyntheticArtifactFile(runId);
  const artifactFileName = `synthetic_evidence_${runId}.zip`;
  const artifact = await apiRequest("/api/v1/platform/artifacts", {
    method: "POST",
    token,
    body: {
      source_module: "rates",
      artifact_type: "synthetic_evidence_browser_zip",
      file_path: artifactFile,
      file_name: artifactFileName,
      content_type: "application/zip",
      sensitivity_level: "client_safe"
    }
  });
  const manifest = await apiRequest("/api/v1/platform/manifests", {
    method: "POST",
    token,
    body: {
      source_module: "rates",
      status: "CREATED",
      manifest_json: JSON.stringify(
        {
          schema_version: "synthetic-evidence-browser/v1",
          manifest_type: "synthetic_evidence_browser"
        },
        null,
        2
      )
    }
  });
  const evidence = await apiRequest("/api/v1/platform/evidence", {
    method: "POST",
    token,
    body: {
      source_module: "rates",
      evidence_type: evidenceType,
      summary_json: JSON.stringify({ status: "ok", synthetic: true }, null, 2),
      artifact_id: artifact.id,
      manifest_id: manifest.id
    }
  });
  return {
    artifact: { ...artifact, file_name: artifactFileName },
    evidence,
    evidenceType,
    manifest
  };
}

async function assertControlValue(locator, expected, description) {
  const value = await locator.inputValue();
  if (value !== expected) {
    throw new Error(`${description} expected value "${expected}" but received "${value}".`);
  }
}

async function run() {
  const playwright = await loadPlaywright();
  if (!playwright) return;

  const login = await apiRequest("/api/v1/platform/session/login", {
    method: "POST",
    body: { email, password }
  });
  const token = login.access_token;
  await apiRequest("/api/v1/platform/user-preferences", {
    method: "PUT",
    token,
    body: {
      theme_mode: "light",
      follow_system_theme: false,
      density: "comfortable",
      sidebar_mode: "expanded"
    }
  });
  const seeded = await seedEvidence(token);

  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage({ acceptDownloads: true, viewport: { width: 1360, height: 980 } });
  const consoleErrors = [];
  const failedResponses = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });
  page.on("response", (response) => {
    if (response.status() >= 400) {
      failedResponses.push(`${response.status()} ${response.url()}`);
    }
  });

  try {
    await page.goto(baseUrl, { waitUntil: "domcontentloaded" });
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Sign in" }).click();

    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    await page.locator('a[href="/evidence"]').click();
    await page.getByRole("heading", { name: "Evidence Hub" }).waitFor();
    await page.getByLabel("Evidence Hub workflow").waitFor();
    const evidenceFilters = page.getByLabel("Evidence filters");

    await evidenceFilters.getByLabel("Source module").fill("rates");
    await evidenceFilters.getByLabel("Evidence type").fill(seeded.evidenceType);
    await evidenceFilters.getByLabel("Status").fill("CREATED");
    await evidenceFilters.getByLabel("Sensitivity").fill("client_safe");
    await page.getByRole("button", { name: "Apply filters" }).click();
    await page.getByText("Evidence filters applied.").waitFor();
    await page.getByLabel("Evidence entries").getByText(seeded.evidenceType, { exact: true }).waitFor();
    await page.getByLabel("Selected evidence").getByText(seeded.artifact.file_name, { exact: true }).first().waitFor();

    await page.getByRole("button", { name: "Reset filters" }).click();
    await page.getByText("Evidence filters reset.").waitFor();
    await assertControlValue(evidenceFilters.getByLabel("Source module"), "", "Source module after reset");
    await assertControlValue(evidenceFilters.getByLabel("Evidence type"), "", "Evidence type after reset");
    await assertControlValue(evidenceFilters.getByLabel("Status"), "", "Status after reset");
    await assertControlValue(evidenceFilters.getByLabel("Project"), "", "Project after reset");
    await assertControlValue(evidenceFilters.getByLabel("Sensitivity"), "", "Sensitivity after reset");
    await assertControlValue(evidenceFilters.getByLabel("Artifact"), "", "Artifact after reset");
    await assertControlValue(evidenceFilters.getByLabel("Manifest"), "", "Manifest after reset");

    await evidenceFilters.getByLabel("Source module").fill("rates");
    await evidenceFilters.getByLabel("Evidence type").fill(seeded.evidenceType);
    await evidenceFilters.getByLabel("Status").fill("CREATED");
    await evidenceFilters.getByLabel("Sensitivity").fill("client_safe");
    await page.getByRole("button", { name: "Apply filters" }).click();
    await page.getByText("Evidence filters applied.").waitFor();
    await page.getByLabel("Evidence entries").getByText(seeded.evidenceType, { exact: true }).waitFor();
    await page.getByLabel("Selected evidence").getByText(seeded.artifact.file_name, { exact: true }).first().waitFor();

    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", { name: "Download artifact" }).click();
    const download = await downloadPromise;
    if (!download.suggestedFilename().includes(seeded.artifact.file_name)) {
      throw new Error(`Unexpected download filename: ${download.suggestedFilename()}`);
    }
    await page.getByText(`Artifact ${seeded.artifact.file_name} downloaded through Evidence Hub.`).waitFor();

    await page.getByRole("button", { name: "Create archive" }).click();
    await page.getByText(/^Archive package .+ created\.$/).waitFor();
    await page.getByLabel("Latest archive package").waitFor();
    await page.getByLabel("Archive package history").getByText(/evidence_hub_archive_/).first().waitFor();

    await page.getByLabel("Evidence entries").getByRole("button", { name: new RegExp(seeded.evidenceType) }).click();
    await page.getByLabel("Selected evidence").getByText(seeded.artifact.file_name, { exact: true }).first().waitFor();
    if (await page.getByText(/^Archive package .+ created\.$/).isVisible().catch(() => false)) {
      throw new Error("Evidence Hub kept stale archive feedback after switching selected evidence.");
    }

    await page.locator('a[href="/home"]').click();
    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    await page.locator('a[href="/evidence"]').click();
    await page.getByRole("heading", { name: "Evidence Hub" }).waitFor();
    await page.getByLabel("Evidence entries").getByText(seeded.evidenceType, { exact: true }).waitFor();

    if (consoleErrors.length || failedResponses.length) {
      throw new Error(
        [
          "Evidence Hub browser functional QA detected runtime failures.",
          consoleErrors.length ? `Console errors:\n${consoleErrors.join("\n")}` : "",
          failedResponses.length ? `HTTP failures:\n${failedResponses.join("\n")}` : ""
        ]
          .filter(Boolean)
          .join("\n")
      );
    }

    console.log(
      JSON.stringify(
        {
          status: "passed",
          journey: "evidence-filter-detail-download-archive-return",
          evidenceType: seeded.evidenceType,
          baseUrl,
          apiBaseUrl
        },
        null,
        2
      )
    );
  } finally {
    await browser.close();
  }
}

run().catch((error) => {
  console.error(error instanceof Error ? error.stack : String(error));
  process.exitCode = 1;
});
