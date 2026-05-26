/* global console, fetch, process */

import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const baseUrl = process.env.OTM_WORKBENCH_BASE_URL ?? "http://127.0.0.1:5173";
const apiBaseUrl = process.env.OTM_WORKBENCH_API_BASE_URL ?? "http://127.0.0.1:8000";
const email = process.env.OTM_WORKBENCH_QA_EMAIL ?? "demo@example.test";
const password = process.env.OTM_WORKBENCH_QA_PASSWORD ?? "DemoPass123!";
const screenshotDir = path.resolve(process.cwd(), "..", "output", "gui-qa", "catalog");

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
    const responseText = await response.text();
    if (response.status === 401 && path === "/api/v1/platform/session/login") {
      throw new Error(
        [
          `${method} ${path} failed with HTTP 401: ${responseText}`,
          "Browser QA login user is not available in the local backend.",
          "Run from the repository root after the backend schema is created:",
          "  python -m otm_workbench.cli bootstrap-qa-user",
          "Then rerun the browser QA script."
        ].join("\n")
      );
    }
    throw new Error(`${method} ${path} failed with HTTP ${response.status}: ${responseText}`);
  }
  return response.json();
}

async function seedSyntheticContext(token) {
  const projects = await apiRequest("/api/v1/platform/projects", { token });
  let project = projects.items?.[0];
  if (!project) {
    const workspace = await apiRequest("/api/v1/platform/workspaces", {
      method: "POST",
      token,
      body: { name: "Synthetic QA Workspace" }
    });
    project = await apiRequest("/api/v1/platform/projects", {
      method: "POST",
      token,
      body: { workspace_id: workspace.id, name: "Synthetic QA Project" }
    });
  }

  const profiles = await apiRequest(`/api/v1/platform/profiles?project_id=${project.id}`, { token });
  const profile =
    profiles.items?.[0] ??
    (await apiRequest("/api/v1/platform/profiles", {
      method: "POST",
      token,
      body: { project_id: project.id, name: "Synthetic QA Profile" }
    }));

  const environments = await apiRequest(`/api/v1/platform/environments?project_id=${project.id}`, { token });
  const environment =
    environments.items?.[0] ??
    (await apiRequest("/api/v1/platform/environments", {
      method: "POST",
      token,
      body: { project_id: project.id, name: "DEV", environment_type: "DEV" }
    }));

  return { project, profile, environment };
}

async function seedSyntheticReferenceOptions(token) {
  await apiRequest("/api/v1/reference/import-batches", {
    method: "POST",
    token,
    body: {
      source_type: "json",
      source_description: "synthetic catalog browser reference option seed",
      records: [
        {
          object_type: "RATE_SERVICE",
          gid: "PUBLIC.RS_STANDARD",
          xid: "RS_STANDARD",
          domain_name: "PUBLIC",
          display_name: "Standard service"
        },
        {
          object_type: "RATE_SERVICE",
          gid: "OTM1.RS_EXPRESS",
          xid: "RS_EXPRESS",
          domain_name: "OTM1",
          display_name: "Express service"
        },
        {
          object_type: "RATE_SERVICE",
          gid: "OTM2.RS_OTHER",
          xid: "RS_OTHER",
          domain_name: "OTM2",
          display_name: "Other service"
        }
      ]
    }
  });
}

async function seedSyntheticSchemaPack(token) {
  const existingRoots = await apiRequest("/api/v1/catalog/schema-roots?schema_guidance_role=ENVELOPE_ONLY", { token });
  if (existingRoots.items?.length) {
    const firstRootPaths = await apiRequest(`/api/v1/catalog/schema-roots/${existingRoots.items[0].id}/paths`, { token });
    if (firstRootPaths.items?.length) return;
  }

  const schemaFolder = path.resolve(process.cwd(), "..", "output", "gui-qa", "catalog", "synthetic-schema-pack");
  await mkdir(schemaFolder, { recursive: true });
  await writeFile(
    path.join(schemaFolder, "Transmission.xsd"),
    `<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
  targetNamespace="http://xmlns.oracle.com/apps/otm/transmission">
  <xs:element name="Transmission" type="TransmissionType"/>
  <xs:complexType name="TransmissionType">
    <xs:sequence>
      <xs:element name="TransmissionHeader" type="xs:string"/>
      <xs:element name="TransmissionBody" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
`,
    "utf-8"
  );
  await writeFile(
    path.join(schemaFolder, "Shipment.xsd"),
    `<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
  targetNamespace="http://xmlns.oracle.com/apps/otm/shipment">
  <xs:element name="PlannedShipment" type="PlannedShipmentType"/>
  <xs:complexType name="PlannedShipmentType">
    <xs:sequence>
      <xs:element name="ShipmentGid" type="xs:string"/>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
`,
    "utf-8"
  );

  const pack = await apiRequest("/api/v1/catalog/schema-packs", {
    method: "POST",
    token,
    body: {
      code: `OTM_QA_SCHEMA_${Date.now()}`,
      name: "Synthetic Catalog QA schema pack",
      otm_version: "26A",
      source_type: "LOCAL_FOLDER",
      source_path: schemaFolder,
      content_hash: `synthetic-catalog-${Date.now()}`
    }
  });
  await apiRequest(`/api/v1/catalog/schema-packs/${pack.id}/index`, { method: "POST", token });
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
  const context = await seedSyntheticContext(token);
  await seedSyntheticReferenceOptions(token);
  await seedSyntheticSchemaPack(token);
  const macroObjects = await apiRequest("/api/v1/catalog/macro-objects", { token });
  const alternateMacroCode = macroObjects.items?.find((item) => !["RATE_RECORD", "RATE_OFFERING"].includes(item.code))?.code;
  if (!alternateMacroCode) {
    throw new Error("Catalog browser functional QA requires a second macro object for macro-switch recovery.");
  }

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
    await page.goto(baseUrl, { waitUntil: "domcontentloaded" });
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Sign in" }).click();

    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    const contextControls = page.locator(".context-switcher");
    await contextControls.locator("select").nth(0).selectOption(context.project.id);
    await contextControls.locator("select").nth(1).selectOption(context.profile.id);
    await contextControls.locator("select").nth(2).selectOption(context.environment.id);
    await contextControls.locator("input").fill("otm1");
    await page.getByRole("button", { name: "Apply context" }).click();
    await page.getByText("Project context ready").waitFor();

    await page.locator('a[href="/catalog"]').click();
    await page.getByRole("heading", { name: "OTM Catalog Core" }).waitFor();
    await capture(page, "01-catalog-hub.png");
    await page.getByLabel("Catalog macro objects").getByRole("button", { name: /RATE_RECORD/ }).click();
    await page.getByRole("heading", { name: "RATE_RECORD Catalog detail" }).waitFor();
    await page
      .getByLabel("Selected catalog macro object")
      .locator(".detail-stack > div")
      .first()
      .getByText("RATE_RECORD")
      .waitFor();
    await page.getByLabel("Selected macro object tables").getByText("RATE_GEO_COST", { exact: true }).waitFor();
    await page.getByLabel("Selected macro object load plan").getByText("RATE_OFFERING", { exact: true }).waitFor();
    await capture(page, "02-rate-record-detail.png");
    await page.getByRole("link", { name: "Back to Catalog" }).click();
    await page.getByRole("heading", { name: "OTM Catalog Core" }).waitFor();

    await page.goto(`${baseUrl}/catalog/macro-objects/RATE_RECORD`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "RATE_RECORD Catalog detail" }).waitFor();
    await page.getByRole("link", { name: "Back to Catalog" }).waitFor();
    await page.getByLabel("Selected macro object tables").getByText("RATE_GEO_COST", { exact: true }).waitFor();
    await capture(page, "03-rate-record-route-detail.png");
    await page.getByRole("link", { name: "Back to Catalog" }).click();
    await page.getByRole("heading", { name: "OTM Catalog Core" }).waitFor();

    await page.goto(`${baseUrl}/catalog/tables`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Catalog Table Explorer" }).waitFor();
    await page.getByLabel("Table search").fill("rate_geo");
    await page.getByLabel("Catalog table search results").getByText("RATE_GEO_COST", { exact: true }).waitFor();
    await capture(page, "07-table-explorer.png");
    await page.getByLabel("Catalog table search results").getByText("RATE_GEO_COST", { exact: true }).click();
    await page.getByRole("heading", { name: "RATE_GEO_COST Table detail" }).waitFor();
    await page.getByRole("link", { name: "Back to Tables" }).waitFor();
    await page.getByLabel("Catalog table columns").getByText("RATE_GEO_COST_GROUP_GID", { exact: true }).waitFor();
    await capture(page, "08-table-detail.png");
    await page.getByRole("link", { name: "Back to Catalog" }).click();
    await page.getByRole("heading", { name: "OTM Catalog Core" }).waitFor();

    await page.goto(`${baseUrl}/catalog/reference-options`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Catalog Reference Options" }).waitFor();
    await page.getByLabel("Object type").fill("RATE_SERVICE");
    await page.getByLabel("Catalog reference options").getByText("PUBLIC.RS_STANDARD", { exact: true }).waitFor();
    await page.getByLabel("Catalog reference options").getByText("OTM1.RS_EXPRESS", { exact: true }).waitFor();
    await capture(page, "09-reference-options.png");
    await page.getByLabel("Reference value").fill("OTM2.BRL");
    await page.getByRole("button", { name: "Validate reference" }).click();
    await page.getByText("Reference validation: ERROR").waitFor();
    await page.getByText(/outside|not found|does not exist|not allowed/i).waitFor();
    await capture(page, "10-reference-options-validation-error.png");
    await page.getByRole("link", { name: "Back to Catalog" }).click();
    await page.getByRole("heading", { name: "OTM Catalog Core" }).waitFor();

    await page.goto(`${baseUrl}/catalog/schema-guidance`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Catalog Schema Guidance" }).waitFor();
    await page.getByText("Ready guidance").waitFor();
    await page.getByLabel("Schema guidance readiness").getByText("SHIPMENT", { exact: true }).waitFor();
    await capture(page, "11-schema-guidance.png");
    const schemaInspectButtons = page.getByLabel("Schema root inspector").getByRole("button");
    if ((await schemaInspectButtons.count()) === 0) {
      throw new Error("Catalog schema guidance requires at least one backend-owned schema root.");
    }
    await schemaInspectButtons.first().click();
    await page.getByLabel("Selected schema root paths").locator(".table-list-item").first().waitFor();
    await capture(page, "12-schema-guidance-paths.png");
    await page.getByRole("link", { name: "Back to Catalog" }).click();
    await page.getByRole("heading", { name: "OTM Catalog Core" }).waitFor();

    await page.getByLabel("Table name").fill("SHIPMENT");
    await page.getByLabel("Usage").selectOption("cutover");
    await page.getByRole("button", { name: "Validate table" }).click();
    await page.getByText("Table validation: ERROR").waitFor();
    await page.getByText(/Transactional table is blocked by default/i).waitFor();
    await capture(page, "04-table-validation-error.png");

    await page.getByLabel("Column table").fill("RATE_GEO_COST");
    await page.getByLabel("Column name").fill("RATE_GEO_COST_GROUP_GID");
    await page.getByRole("button", { name: "Validate column" }).click();
    await page.getByText("Column validation: INFO").waitFor();
    await page.getByText(/Column exists/i).waitFor();

    await page.getByLabel("Reference value").fill("OTM2.BRL");
    await page.getByRole("button", { name: "Validate reference" }).click();
    await page.getByText("Reference validation: ERROR").waitFor();
    await page.getByText(/outside|not found|does not exist|not allowed/i).waitFor();
    await capture(page, "05-reference-validation-error.png");

    await page.getByLabel("Catalog macro objects").getByRole("button", { name: new RegExp(alternateMacroCode) }).click();
    await page.getByRole("heading", { name: `${alternateMacroCode} Catalog detail` }).waitFor();
    await page
      .getByLabel("Selected catalog macro object")
      .locator(".detail-stack > div")
      .first()
      .getByText(alternateMacroCode, { exact: true })
      .waitFor();
    if (await page.getByText("Reference validation: ERROR").isVisible().catch(() => false)) {
      throw new Error("Reference validation result stayed visible after selecting another macro object.");
    }
    await capture(page, "06-macro-switch-recovery.png");
    await page.getByRole("link", { name: "Back to Catalog" }).click();
    await page.getByRole("heading", { name: "OTM Catalog Core" }).waitFor();

    await page.getByRole("button", { name: "Reset catalog validation" }).click();
    await page.getByLabel("Table name").evaluate((element) => {
      if (element.value !== "RATE_GEO_COST") throw new Error(`Unexpected table reset value: ${element.value}`);
    });
    await page.getByLabel("Usage").evaluate((element) => {
      if (element.value !== "cutover") throw new Error(`Unexpected usage reset value: ${element.value}`);
    });
    await page.getByLabel("Column table").evaluate((element) => {
      if (element.value !== "RATE_GEO_COST") throw new Error(`Unexpected column table reset value: ${element.value}`);
    });
    await page.getByLabel("Reference value").evaluate((element) => {
      if (element.value !== "OTM1.BRL") throw new Error(`Unexpected reference reset value: ${element.value}`);
    });
    if (await page.getByText("Reference validation: ERROR").isVisible().catch(() => false)) {
      throw new Error("Reference validation result stayed visible after reset.");
    }

    await page.locator('a[href="/home"]').click();
    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    await page.locator('a[href="/catalog"]').click();
    await page.getByRole("heading", { name: "OTM Catalog Core" }).waitFor();
    await page.getByLabel("Catalog macro objects").getByText("RATE_RECORD").waitFor();

    if (consoleErrors.length || failedResponses.length) {
      throw new Error(
        [
          "Catalog browser functional QA detected runtime failures.",
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
          journey: "catalog-macro-load-plan-table-column-reference-validation-switch-recovery",
          baseUrl,
          apiBaseUrl,
          alternate_macro_code: alternateMacroCode,
          project_id: context.project.id,
          profile_id: context.profile.id,
          environment_id: context.environment.id
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
