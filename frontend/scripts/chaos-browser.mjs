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
        "Install or make it available before running browser chaos QA.",
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

async function createDefinition(token, code, name) {
  return apiRequest("/api/v1/modules/integration-mapping/definitions", {
    method: "POST",
    token,
    body: {
      code,
      name,
      description: "Synthetic chaos QA definition.",
      source_system: "OTM",
      target_system: "EXTERNAL_DELIVERY",
      source_format: "XML",
      target_format: "JSON"
    }
  });
}

async function createPayloadAndSchema(token, definitionId, payload) {
  const artifact = await apiRequest(`/api/v1/modules/integration-mapping/definitions/${definitionId}/payload-artifacts`, {
    method: "POST",
    token,
    body: payload
  });
  return apiRequest(`/api/v1/modules/integration-mapping/payload-artifacts/${artifact.id}/schema-documents`, {
    method: "POST",
    token,
    body: {}
  });
}

async function seedIntegrationMappingChaosData(token) {
  const suffix = Date.now().toString(36).toUpperCase();
  const primary = await createDefinition(
    token,
    `CHAOS_IM_PRIMARY_${suffix}`,
    `Chaos Integration Primary ${suffix}`
  );
  const alternate = await createDefinition(
    token,
    `CHAOS_IM_ALT_${suffix}`,
    `Chaos Integration Alternate ${suffix}`
  );

  await createPayloadAndSchema(token, primary.id, {
    payload_role: "SOURCE_SAMPLE",
    payload_format: "XML",
    file_name: `chaos_planned_shipment_${suffix}.xml`,
    description: "Synthetic chaos source payload.",
    content:
      "<Transmission><Shipment><ShipmentGid>DEMO.SHIPMENT_001</ShipmentGid><ShipmentStop><StopSequence>1</StopSequence></ShipmentStop></Shipment></Transmission>"
  });
  await createPayloadAndSchema(token, primary.id, {
    payload_role: "TARGET_SAMPLE",
    payload_format: "JSON",
    file_name: `chaos_external_delivery_${suffix}.json`,
    description: "Synthetic chaos target payload.",
    content: '{"header":{"shipmentId":"DEMO"},"deliveries":[{"sequence":1}]}'
  });

  return { alternate, primary, suffix };
}

async function signIn(page) {
  await page.goto(baseUrl, { waitUntil: "domcontentloaded" });
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
}

async function selectDefinition(page, code) {
  await page.locator(".integration-workflow-step").filter({ hasText: "Definitions list" }).click();
  await page.getByLabel("Integration mapping definitions").getByRole("button").filter({ hasText: code }).click();
  await page.getByLabel("Selected integration mapping definition").getByText(code).waitFor();
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
  const seeded = await seedIntegrationMappingChaosData(token);

  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 840 } });
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
    await signIn(page);
    await page.locator('a[href="/integration-mapping"]').click();
    await page.getByRole("heading", { name: "Integration Mapping Studio" }).waitFor();

    await selectDefinition(page, seeded.primary.code);
    await page.locator(".integration-workflow-step").filter({ hasText: "Mapping rules" }).click();
    const mappingForm = page.locator(".integration-mapping-form").first();
    await mappingForm.waitFor();
    await mappingForm.getByLabel("Source schema").selectOption({ label: "Transmission" });
    await mappingForm.getByLabel("Target schema").selectOption({ label: "$" });
    await page.getByRole("button", { name: "Load backend suggestions" }).click();
    await page
      .getByRole("button", {
        name: "Apply suggestion /Transmission/Shipment/ShipmentGid to $.header.shipmentId"
      })
      .waitFor();

    await page.getByLabel("Source path").fill("/dirty/source/path");
    await page.getByLabel("Target path").fill("$.dirtyTarget");
    await page.getByLabel("Mapping description").fill("Dirty draft that must not leak.");

    await selectDefinition(page, seeded.alternate.code);
    await page.locator(".integration-workflow-step").filter({ hasText: "Mapping rules" }).click();
    await mappingForm.waitFor();
    const sourcePath = await page.getByLabel("Source path").inputValue();
    const targetPath = await page.getByLabel("Target path").inputValue();
    const description = await page.getByLabel("Mapping description").inputValue();
    if (sourcePath || targetPath || description) {
      throw new Error(
        [
          "Integration Mapping dirty draft leaked after definition switch.",
          `source_path=${sourcePath}`,
          `target_path=${targetPath}`,
          `description=${description}`
        ].join("\n")
      );
    }

    const loadSuggestions = page.getByRole("button", { name: "Load backend suggestions" });
    if (await loadSuggestions.isEnabled()) {
      throw new Error("Load backend suggestions should stay disabled when the selected definition has no schemas selected.");
    }
    await page.getByText("No mapping suggestions for the selected schemas.").waitFor();

    await page.locator('a[href="/home"]').click();
    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    await page.locator('a[href="/integration-mapping"]').click();
    await page.getByRole("heading", { name: "Integration Mapping Studio" }).waitFor();
    await page.getByLabel("Selected integration mapping definition").getByText(seeded.alternate.code).waitFor();

    if (consoleErrors.length || failedResponses.length) {
      throw new Error(
        [
          "Browser chaos QA detected runtime failures.",
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
          journey: "integration-mapping-out-of-order-definition-switch",
          baseUrl,
          apiBaseUrl,
          primary_definition_code: seeded.primary.code,
          alternate_definition_code: seeded.alternate.code
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
  console.error(error);
  process.exitCode = 1;
});
