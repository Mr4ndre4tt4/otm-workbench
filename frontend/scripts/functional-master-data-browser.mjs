/* global console, fetch, process */

import { execFileSync } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const baseUrl = process.env.OTM_WORKBENCH_BASE_URL ?? "http://127.0.0.1:5173";
const apiBaseUrl = process.env.OTM_WORKBENCH_API_BASE_URL ?? "http://127.0.0.1:8000";
const email = process.env.OTM_WORKBENCH_QA_EMAIL ?? "demo@example.test";
const password = process.env.OTM_WORKBENCH_QA_PASSWORD ?? "DemoPass123!";

function createSyntheticRegionsWorkbook() {
  const dir = mkdtempSync(join(tmpdir(), "otm-master-data-qa-"));
  const filePath = join(dir, "regions_basic_browser_upload.xlsx");
  const script = [
    "from openpyxl import Workbook",
    "import sys",
    "wb = Workbook()",
    "regions = wb.active",
    "regions.title = 'REGIONS'",
    "regions.append(['Region GID', 'Region XID', 'Region Name'])",
    "regions.append(['SYN.REGION_BROWSER', 'REGION_BROWSER', 'Synthetic Browser Region'])",
    "details = wb.create_sheet('REGION_DETAILS')",
    "details.append(['Region GID', 'Location GID'])",
    "details.append(['SYN.REGION_BROWSER', 'SYN.LOCATION_BROWSER'])",
    "wb.save(sys.argv[1])"
  ].join("\n");
  execFileSync("python", ["-c", script, filePath], { stdio: "pipe" });
  return filePath;
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
    throw new Error(`${method} ${path} failed with HTTP ${response.status}: ${await response.text()}`);
  }
  return response.json();
}

async function assertHidden(locator, message) {
  if (await locator.isVisible()) {
    throw new Error(message);
  }
}

async function assertDisabled(locator, message) {
  if (await locator.isEnabled()) {
    throw new Error(message);
  }
}

async function assertUnchecked(locator, message) {
  const checked = await locator.evaluate((element) => element.checked);
  if (checked) {
    throw new Error(message);
  }
}

async function waitForSuccessOrThrow(page, text) {
  const success = page.getByText(text);
  const error = page.locator(".form-error");
  const winner = await Promise.race([
    success.waitFor({ timeout: 30000 }).then(() => "success"),
    error.waitFor({ timeout: 30000 }).then(() => "error")
  ]);
  if (winner === "error") {
    throw new Error(`Visible UI error while waiting for "${text}": ${await error.textContent()}`);
  }
}

async function waitForVisibleOrThrow(page, locator, description, context = {}) {
  const error = page.locator(".form-error");
  let winner;
  try {
    winner = await Promise.race([
      locator.waitFor({ timeout: 30000 }).then(() => "target"),
      error.waitFor({ timeout: 30000 }).then(() => "error")
    ]);
  } catch (waitError) {
    throw new Error(
      [
        `Timed out while waiting for ${description}.`,
        `URL: ${page.url()}`,
        context.failedResponses?.length ? `HTTP failures:\n${context.failedResponses.join("\n")}` : "",
        context.consoleErrors?.length ? `Console errors:\n${context.consoleErrors.join("\n")}` : "",
        `Visible text:\n${(await page.locator("body").innerText({ timeout: 5000 })).slice(0, 1200)}`,
        waitError instanceof Error ? waitError.message : String(waitError)
      ]
        .filter(Boolean)
        .join("\n")
    );
  }
  if (winner === "error") {
    throw new Error(`Visible UI error while waiting for ${description}: ${await error.textContent()}`);
  }
}

async function run() {
  const playwright = await loadPlaywright();
  if (!playwright) return;
  const runId = Date.now().toString(36).toUpperCase();
  const authorTemplateCode = `LOC_BROWSER_${runId}`;

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

  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1360, height: 980 } });
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

    await waitForVisibleOrThrow(page, page.getByRole("heading", { name: "Project Cockpit" }), "Project Cockpit after sign in", {
      consoleErrors,
      failedResponses
    });
    await page.locator('a[href="/master-data"]').click();
    await waitForVisibleOrThrow(page, page.getByRole("heading", { name: "Data Factory", exact: true }), "Data Factory after navigation", {
      consoleErrors,
      failedResponses
    });
    await page.getByLabel("Data Factory workflow").waitFor();

    await page.locator(".master-data-workflow-step").filter({ hasText: "Author" }).click();
    await page.getByLabel("Template code").fill(authorTemplateCode);
    await page.getByLabel("Template name").fill(`Locations Browser QA ${runId}`);
    const tablePicker = page.getByLabel("Catalog tables for LOCATION");
    await tablePicker.getByRole("checkbox", { name: "LOCATION_ADDRESS" }).check();
    await page.getByLabel("Catalog columns for LOCATION").getByRole("checkbox", { name: "CITY" }).check();
    const addressPicker = page.getByLabel("Catalog columns for LOCATION_ADDRESS");
    await addressPicker.getByRole("checkbox", { name: "LOCATION_GID" }).check();
    await page.getByRole("checkbox", { name: "Require LOCATION parent for LOCATION_ADDRESS" }).check();
    await tablePicker.getByRole("checkbox", { name: "LOCATION_ADDRESS" }).uncheck();
    await assertHidden(
      page.getByLabel("Catalog columns for LOCATION_ADDRESS"),
      "LOCATION_ADDRESS columns remained visible after removing the child table."
    );
    await tablePicker.getByRole("checkbox", { name: "LOCATION_ADDRESS" }).check();
    const relationshipRule = page.getByRole("checkbox", { name: "Require LOCATION parent for LOCATION_ADDRESS" });
    await assertDisabled(relationshipRule, "Relationship rule remained enabled before the child key was re-selected.");
    await assertUnchecked(relationshipRule, "Relationship rule remained checked after the child table was removed and re-added.");
    const resetAddressPicker = page.getByLabel("Catalog columns for LOCATION_ADDRESS");
    await resetAddressPicker.getByRole("checkbox", { name: "LOCATION_GID" }).check();
    await resetAddressPicker.getByRole("checkbox", { name: "ADDRESS_LINE" }).check();
    await page.getByLabel("Friendly label for LOCATION_ADDRESS.ADDRESS_LINE").fill("Street line for browser QA");
    await page.getByLabel("Source type for LOCATION.CITY").selectOption("DEFAULT_VALUE");
    await page.getByLabel("Default value for LOCATION.CITY").fill("UNKNOWN_CITY");
    await page.getByRole("checkbox", { name: "Require LOCATION parent for LOCATION_ADDRESS" }).check();
    await page.getByRole("button", { name: "Create draft" }).click();
    await waitForSuccessOrThrow(page, `Draft ${authorTemplateCode} created.`);
    await page.getByRole("button", { name: "Validate definition" }).click();
    await waitForSuccessOrThrow(page, "Definition validation is VALID.");
    await page.getByRole("button", { name: "Publish template" }).click();
    await waitForSuccessOrThrow(page, `Template ${authorTemplateCode} published.`);

    await page.locator(".master-data-workflow-step").filter({ hasText: "Templates" }).click();
    await page
      .getByLabel("Master Data templates")
      .locator(".module-row")
      .filter({ hasText: "REGIONS_BASIC" })
      .click();
    await page.getByLabel("Selected Master Data template").getByText("REGIONS_BASIC", { exact: true }).waitFor();

    await page.locator(".master-data-workflow-step").filter({ hasText: "Workbook" }).click();
    await page.getByRole("button", { name: "Validate template" }).click();
    await page.getByText("Template validation is VALID.").waitFor();
    await page.getByRole("button", { name: "Build workbook" }).click();
    await page.getByText("Workbook regions_basic_v1.xlsx generated.").waitFor();

    await page.locator(".master-data-workflow-step").filter({ hasText: "Upload" }).click();
    await page.getByLabel("Workbook file").setInputFiles(createSyntheticRegionsWorkbook());
    await page.getByRole("button", { name: "Upload workbook" }).click();
    await page.getByText(/^Workbook uploaded as batch .+\.$/).waitFor();

    await page.locator(".master-data-workflow-step").filter({ hasText: "Validate" }).click();
    await page.getByRole("button", { name: "Validate relationships" }).click();
    await page.getByText(/^Relationship validation is (VALID|RELATIONSHIP_VALIDATED)\.$/).waitFor();

    await page.locator(".master-data-workflow-step").filter({ hasText: "Map" }).click();
    await page.getByRole("button", { name: "Map records" }).click();
    await page.getByText("Batch mapping is MAPPED.").waitFor();

    await page.locator(".master-data-workflow-step").filter({ hasText: "Output" }).click();
    const outputPanel = page.getByLabel("Output and export workflow");
    await outputPanel.getByRole("button", { name: "Build output" }).click();
    await page.getByText("Output build is OUTPUT_BUILT.").waitFor();
    await page.getByLabel("Master Data output record preview").getByText("REGION").first().waitFor();
    await outputPanel.getByRole("button", { name: "Build CSV" }).click();
    await page.getByText("CSV build is CSV_BUILT.").waitFor();
    await page.getByLabel("Master Data CSV file preview").getByText("001_REGION.csv").waitFor();
    await outputPanel.getByRole("button", { name: "Export package" }).click();
    await page.getByText("CSV package export is EXPORTED.").waitFor();
    await page.getByLabel("Export package summary").waitFor();
    await outputPanel.getByRole("button", { name: "Register for Load Plan" }).click();
    await page.getByText(/^Load Plan package .+ registered\.$/).waitFor();
    await page.getByLabel("Load Plan package registration").getByText("master_data_csv_zip").waitFor();

    await page.locator('a[href="/home"]').click();
    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    await page.locator('a[href="/master-data"]').click();
    await page.getByRole("heading", { name: "Data Factory", exact: true }).waitFor();
    await page.getByLabel("Master Data templates").getByText("REGIONS_BASIC", { exact: true }).waitFor();
    await page.locator(".master-data-workflow-step").filter({ hasText: "Output" }).click();
    await page.getByLabel("Durable Master Data batches").getByText("REGIONS_BASIC", { exact: true }).first().waitFor();
    await page
      .getByLabel("Master Data export artifacts")
      .getByText(/master_data_batch_.+\.zip/)
      .first()
      .waitFor();

    if (consoleErrors.length || failedResponses.length) {
      throw new Error(
        [
          "Master Data browser functional QA detected runtime failures.",
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
          journey: "master-data-author-template-workbook-upload-output-export-load-plan-registration-route-recovery",
          authorTemplateCode,
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
