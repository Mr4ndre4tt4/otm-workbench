/* global console, fetch, process */

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

async function run() {
  const playwright = await loadPlaywright();
  if (!playwright) return;
  const runId = Date.now().toString(36).toUpperCase();
  const alternateTemplateCode = `TL_OR_BROWSER_ALT_${runId}`;

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

  const browser = await playwright.chromium.launch({ headless: true });
  const browserContext = await browser.newContext({ acceptDownloads: true, viewport: { width: 1280, height: 900 } });
  const page = await browserContext.newPage();
  const consoleErrors = [];
  const failedResponses = [];
  page.on("console", (message) => {
    if (message.type() === "error" && !message.text().includes("409 (Conflict)")) {
      consoleErrors.push(message.text());
    }
  });
  page.on("response", (response) => {
    if (response.status() >= 400 && !response.url().endsWith("/submit-otm")) {
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

    await page.locator('a[href="/order-release-generator"]').click();
    await page.getByRole("heading", { name: "Order Release Generator" }).waitFor();
    await page.getByLabel("Order Release templates").getByText("TL_ORDER_RELEASE_MVP0").waitFor();
    await page.getByLabel("Template code", { exact: true }).fill(alternateTemplateCode);
    await page.getByLabel("Template name", { exact: true }).fill(`Browser alternate OR ${runId}`);
    await page.getByLabel("Required columns", { exact: true }).fill("release_gid, source_location_gid, destination_location_gid, item_gid");
    await page.getByLabel("Optional columns", { exact: true }).fill("transport_mode, weight_uom");
    await page.getByLabel("Default values", { exact: true }).fill("transport_mode=LTL\nweight_uom=LB");
    await page.getByRole("button", { name: "Create template" }).click();
    await page.getByText(`Order Release template ${alternateTemplateCode} created.`).waitFor();
    await page.getByLabel("Order Release templates").getByText("TL_ORDER_RELEASE_MVP0").click();

    await page.getByRole("button", { name: /2Batch/ }).click();
    await page.getByRole("button", { name: "Reset rows" }).click();
    await page.getByText("Order Release rows reset from the selected template.").waitFor();
    await page.getByLabel("Order Release row editor").getByText("Row 1").waitFor();
    if (await page.getByLabel("Order Release row editor").getByText("Row 2").isVisible().catch(() => false)) {
      throw new Error("Reset rows did not collapse the editor back to a single template row.");
    }
    const requiredFields = [
      ["Row 1 release_gid", "OTM1.OR_SYN_BROWSER_001"],
      ["Row 1 source_location_gid", "OTM1.SOURCE_A"],
      ["Row 1 destination_location_gid", "OTM1.DEST_A"],
      ["Row 1 early_pickup_date", "2026-05-20 08:00:00"],
      ["Row 1 late_delivery_date", "2026-05-21 17:00:00"],
      ["Row 1 item_gid", "OTM1.ITEM_A"],
      ["Row 1 packaged_item_gid", "OTM1.PACK_A"],
      ["Row 1 weight", "100"],
      ["Row 1 weight_uom", "KG"]
    ];
    for (const [label, value] of requiredFields) {
      await page.getByLabel(label, { exact: true }).fill(value);
    }
    await page.getByRole("button", { name: "Create batch" }).click();
    await page.getByText(/Order Release batch .* created\./).waitFor();
    const batchPanel = page.getByLabel("Active Order Release batch");
    await batchPanel.getByText("VALID").waitFor();
    const batchId = (await batchPanel.locator(".table-list-main").first().textContent())?.trim();
    if (!batchId) {
      throw new Error("Could not read created Order Release batch id from UI.");
    }

    await page.getByRole("button", { name: /3Preview/ }).click();
    await page.getByRole("button", { name: "Preview XML" }).click();
    await page.getByText("Order Release XML preview generated.").waitFor();
    await page.getByLabel("Order Release XML preview").getByText("Transmission", { exact: true }).waitFor();

    await page.getByRole("button", { name: /4Artifact/ }).click();
    await page.getByRole("button", { name: "Generate XML artifact" }).click();
    await page.getByText(/Order Release XML artifact .* generated\./).waitFor();
    await page.getByLabel("Order Release XML artifact").getByText(/db\.xml/).waitFor();
    await page.getByRole("button", { name: "Download" }).click();
    await page.getByText(/Order Release artifact .*db\.xml downloaded\./).waitFor();
    const downloadedFile = "db.xml";

    await page.getByRole("button", { name: /5Submit/ }).click();
    await page.getByRole("button", { name: "Verify OTM submit guard" }).click();
    await page.getByText("Direct OTM submission is disabled in MVP0.").waitFor();
    await page.getByLabel("OTM submit guard").getByText("order_release_generator.submit_otm").waitFor();
    await page.getByRole("button", { name: /1Templates/ }).click();
    await page.getByLabel("Order Release templates").getByText(alternateTemplateCode).click();
    await page.getByRole("button", { name: /2Batch/ }).click();
    if (await page.getByLabel("Active Order Release batch", { exact: true }).isVisible().catch(() => false)) {
      throw new Error("Switching Order Release templates left the previous batch active.");
    }
    await page.getByLabel("Order Release row editor").getByText("transport_mode").waitFor();
    if (await page.getByText("Direct OTM submission is disabled in MVP0.").isVisible().catch(() => false)) {
      throw new Error("Switching Order Release templates left stale submit guard feedback visible.");
    }
    await page.getByRole("button", { name: /3Preview/ }).click();
    if (await page.getByLabel("Order Release XML preview", { exact: true }).isVisible().catch(() => false)) {
      throw new Error("Switching Order Release templates left stale XML preview visible.");
    }
    await page.getByRole("button", { name: /4Artifact/ }).click();
    if (await page.getByLabel("Order Release XML artifact", { exact: true }).isVisible().catch(() => false)) {
      throw new Error("Switching Order Release templates left stale XML artifacts visible.");
    }
    await page.getByRole("button", { name: /5Submit/ }).click();
    if (await page.getByLabel("OTM submit guard", { exact: true }).isVisible().catch(() => false)) {
      throw new Error("Switching Order Release templates left stale submit guard details visible.");
    }

    await page.locator('a[href="/home"]').click();
    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    await page.locator('a[href="/order-release-generator"]').click();
    await page.getByRole("heading", { name: "Order Release Generator" }).waitFor();
    await page.getByLabel("Recent Order Release batches").getByText(batchId).waitFor();

    if (consoleErrors.length || failedResponses.length) {
      throw new Error(
        [
          "Order Release Generator browser functional QA detected runtime failures.",
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
          journey: "order-release-template-batch-preview-artifact-submit-guard-return",
          alternate_template_code: alternateTemplateCode,
          baseUrl,
          apiBaseUrl,
          project_id: context.project.id,
          profile_id: context.profile.id,
          environment_id: context.environment.id,
          batch_id: batchId,
          downloaded_file: downloadedFile
        },
        null,
        2
      )
    );
  } finally {
    await browserContext.close();
    await browser.close();
  }
}

run().catch((error) => {
  console.error(error instanceof Error ? error.stack : String(error));
  process.exitCode = 1;
});
