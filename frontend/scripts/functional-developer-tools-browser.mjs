/* global console, fetch, process */

import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const baseUrl = process.env.OTM_WORKBENCH_BASE_URL ?? "http://127.0.0.1:5173";
const apiBaseUrl = process.env.OTM_WORKBENCH_API_BASE_URL ?? "http://127.0.0.1:8000";
const email = process.env.OTM_WORKBENCH_QA_EMAIL ?? "demo@example.test";
const password = process.env.OTM_WORKBENCH_QA_PASSWORD ?? "DemoPass123!";
const screenshotDir = path.resolve(process.cwd(), "..", "output", "gui-qa", "developer-tools");

async function capture(page, name) {
  await mkdir(screenshotDir, { recursive: true });
  await page.screenshot({ fullPage: true, path: path.join(screenshotDir, name) });
}

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

async function apiRequest(requestPath, { method = "GET", token, body } = {}) {
  const response = await fetch(`${apiBaseUrl}${requestPath}`, {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!response.ok) {
    const responseText = await response.text();
    if (response.status === 401 && requestPath === "/api/v1/platform/session/login") {
      throw new Error(
        [
          `${method} ${requestPath} failed with HTTP 401: ${responseText}`,
          "Browser QA login user is not available in the local backend.",
          "Run from the repository root after the backend schema is created:",
          "  python -m otm_workbench.cli bootstrap-qa-user",
          "Then rerun the browser QA script."
        ].join("\n")
      );
    }
    throw new Error(`${method} ${requestPath} failed with HTTP ${response.status}: ${responseText}`);
  }
  return response.json();
}

async function seedSchemaPack(token) {
  const seedId = Date.now();
  const code = `OTM26A_QA_${seedId}`;
  const schemaFolder = path.join(screenshotDir, `schema-pack-seed-${seedId}`);
  await mkdir(schemaFolder, { recursive: true });
  await writeFile(
    path.join(schemaFolder, "Order.xsd"),
    `<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
  targetNamespace="http://xmlns.oracle.com/apps/otm/order">
  <xs:element name="Release" type="ReleaseType"/>
  <xs:complexType name="ReleaseType">
    <xs:sequence>
      <xs:element name="TransactionCode" type="xs:string" minOccurs="1" maxOccurs="1"/>
      <xs:element name="ReleaseLine" minOccurs="0" maxOccurs="unbounded">
        <xs:complexType>
          <xs:sequence>
            <xs:element name="LineNumber" type="xs:string"/>
          </xs:sequence>
        </xs:complexType>
      </xs:element>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
`,
    "utf8"
  );
  const pack = await apiRequest("/api/v1/catalog/schema-packs", {
    method: "POST",
    token,
    body: {
      code,
      name: "Synthetic OTM 26A QA",
      otm_version: "26A",
      source_type: "LOCAL_FOLDER",
      source_path: schemaFolder,
      content_hash: `synthetic-schema-pack-${seedId}`
    }
  });
  await apiRequest(`/api/v1/catalog/schema-packs/${pack.id}/index`, {
    method: "POST",
    token
  });
  return { ...pack, code, otm_version: "26A" };
}

async function run() {
  const playwright = await loadPlaywright();
  if (!playwright) return;

  const login = await apiRequest("/api/v1/platform/session/login", {
    method: "POST",
    body: { email, password }
  });
  const token = login.access_token;
  await apiRequest("/api/v1/platform/feature-flags", {
    method: "POST",
    token,
    body: { name: "dev_tools", enabled: true, scope: "global" }
  });
  const workspace = await apiRequest("/api/v1/platform/workspaces", {
    method: "POST",
    token,
    body: { name: `Developer Tools QA ${Date.now()}` }
  });
  const project = await apiRequest("/api/v1/platform/projects", {
    method: "POST",
    token,
    body: { workspace_id: workspace.id, name: `Synthetic Dev Tools ${Date.now()}` }
  });
  const profile = await apiRequest("/api/v1/platform/profiles", {
    method: "POST",
    token,
    body: { project_id: project.id, name: "Default" }
  });
  const environment = await apiRequest("/api/v1/platform/environments", {
    method: "POST",
    token,
    body: { project_id: project.id, name: "DEV", environment_type: "DEV" }
  });
  await apiRequest("/api/v1/platform/active-context", {
    method: "POST",
    token,
    body: {
      project_id: project.id,
      profile_id: profile.id,
      environment_id: environment.id,
      domain_name: "otm1",
      can_view_all_domains: false
    }
  });
  await apiRequest("/api/v1/platform/jobs", {
    method: "POST",
    token,
    body: {
      job_type: "DEMO_ECHO",
      source_module: "dev_tools",
      project_id: project.id,
      profile_id: profile.id,
      environment_id: environment.id,
      domain_name: "OTM1",
      input: { source: "developer-tools-browser-qa" },
      execute_now: true
    }
  });
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
  const schemaPack = await seedSchemaPack(token);

  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
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
    await page.goto(`${baseUrl}/dev-tools`, { waitUntil: "domcontentloaded" });
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.getByRole("heading", { name: "Technical Diagnostics Hub" }).waitFor();
    await page.getByRole("link", { name: "Open Data Dictionary Explorer" }).waitFor();
    await page.getByRole("link", { name: "Open FK Catalog Explorer" }).waitFor();
    await page.getByRole("link", { name: "Open Schema Pack Diagnostics" }).waitFor();
    await page.getByRole("link", { name: "Open Environment Readiness" }).waitFor();
    await page.getByText("Oracle Lab").waitFor();
    await page.getByText("DEMO_ECHO").waitFor();
    await page.getByText("Summary returns backend-safe metadata only; raw diagnostic payloads remain hidden.").waitFor();
    if (await page.getByText("Primary list or work queue").isVisible().catch(() => false)) {
      throw new Error("Developer Tools still renders the generic module placeholder.");
    }
    await capture(page, "01-developer-tools-guarded-hub.png");

    await page.getByRole("link", { name: "Open Data Dictionary Explorer" }).click();
    await page.getByRole("heading", { name: "Data Dictionary Explorer" }).waitFor();
    await page.getByRole("link", { name: "Back to Developer Tools" }).waitFor();

    await page.goto(`${baseUrl}/dev-tools/data-dictionary?query=rate_geo`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Data Dictionary Explorer" }).waitFor();
    await page.getByText("RATE_GEO_COST", { exact: true }).waitFor();
    await page.getByText("RATES_SETUP").first().waitFor();
    await page.getByText("Source contract: /api/v1/catalog/tables").waitFor();
    await page.getByRole("link", { name: "Back to Developer Tools" }).waitFor();
    await capture(page, "02-data-dictionary-explorer.png");

    await page.getByRole("link", { name: "Open table" }).nth(4).click();
    await page.getByRole("heading", { name: "RATE_GEO_COST" }).waitFor();
    await page.getByText("ALLOW_ZERO_RBI_VALUE", { exact: true }).waitFor();
    await page.getByText("Source contract: /api/v1/catalog/tables/{table_name}").waitFor();
    await page.getByRole("link", { name: "Back to Data Dictionary" }).waitFor();
    await capture(page, "03-data-dictionary-table-detail.png");

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${baseUrl}/dev-tools/data-dictionary/tables/RATE_GEO_COST`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "RATE_GEO_COST" }).waitFor();
    await page.getByText("ALLOW_ZERO_RBI_VALUE", { exact: true }).waitFor();
    await page.getByRole("link", { name: "Back to Data Dictionary" }).waitFor();
    await capture(page, "04-data-dictionary-table-detail-mobile.png");

    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`${baseUrl}/dev-tools/fk-catalog?source_table=RATE_GEO_COST`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "FK Catalog Explorer" }).waitFor();
    await page.getByText("RATE_GEO_COST_GROUP_GID", { exact: true }).first().waitFor();
    await page.getByText("RATE_GEO_COST_GROUP", { exact: true }).first().waitFor();
    await page.getByText("Source contract: /api/v1/catalog/tables/RATE_GEO_COST").waitFor();
    await page.getByRole("link", { name: "Open parent table RATE_GEO_COST_GROUP" }).waitFor();
    await page.getByRole("link", { name: "Back to Developer Tools" }).waitFor();
    await capture(page, "05-fk-catalog-explorer.png");

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${baseUrl}/dev-tools/fk-catalog?source_table=RATE_GEO_COST`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "FK Catalog Explorer" }).waitFor();
    await page.getByText("RATE_GEO_COST_GROUP_GID", { exact: true }).first().waitFor();
    await page.getByRole("link", { name: "Open parent table RATE_GEO_COST_GROUP" }).waitFor();
    await capture(page, "06-fk-catalog-explorer-mobile.png");

    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`${baseUrl}/dev-tools/schema-packs?otm_version=${schemaPack.otm_version}&code=${schemaPack.code}`, {
      waitUntil: "domcontentloaded"
    });
    await page.getByRole("heading", { name: "Schema Pack Diagnostics" }).waitFor();
    await page.getByText("Synthetic OTM 26A QA", { exact: true }).first().waitFor();
    await page.getByText("Order Release", { exact: true }).first().waitFor();
    await page.getByText("Source contract: /api/v1/catalog/schema-packs").waitFor();
    await page.getByRole("link", { name: "Back to Developer Tools" }).waitFor();
    await capture(page, "07-schema-pack-diagnostics.png");

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${baseUrl}/dev-tools/schema-packs?otm_version=${schemaPack.otm_version}&code=${schemaPack.code}`, {
      waitUntil: "domcontentloaded"
    });
    await page.getByRole("heading", { name: "Schema Pack Diagnostics" }).waitFor();
    await page.getByText("Synthetic OTM 26A QA", { exact: true }).first().waitFor();
    await page.getByText("Order Release", { exact: true }).first().waitFor();
    await capture(page, "08-schema-pack-diagnostics-mobile.png");

    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`${baseUrl}/dev-tools/environment-readiness`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Environment Readiness" }).waitFor();
    await page.getByText("DEV", { exact: true }).waitFor();
    await page.getByText("Active environment", { exact: true }).waitFor();
    await page.getByText("Domain scope", { exact: true }).waitFor();
    await page.getByText("Source contract: /api/v1/platform/active-context").waitFor();
    await page.getByRole("link", { name: "Back to Developer Tools" }).waitFor();
    await capture(page, "09-environment-readiness.png");

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${baseUrl}/dev-tools/environment-readiness`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Environment Readiness" }).waitFor();
    await page.getByText("DEV", { exact: true }).waitFor();
    await page.getByText("Active environment", { exact: true }).waitFor();
    await page.getByRole("link", { name: "Back to Developer Tools" }).waitFor();
    await capture(page, "10-environment-readiness-mobile.png");

    if (consoleErrors.length || failedResponses.length) {
      throw new Error(
        [
          "Developer Tools browser functional QA detected runtime failures.",
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
          journey: "developer-tools-hub-data-dictionary-fk-catalog-schema-packs-and-environment-readiness",
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
