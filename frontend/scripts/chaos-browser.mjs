/* global Buffer, console, fetch, process */

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

async function seedAssetsChaosData(token) {
  const suffix = Date.now().toString(36).toUpperCase();
  const primary = await apiRequest("/api/v1/modules/assets/assets", {
    method: "POST",
    token,
    body: {
      name: `Chaos Asset Primary ${suffix}`,
      description: "Client-safe chaos QA primary asset.",
      asset_type: "SPEC",
      category: "INTEGRATION",
      visibility: "PROJECT",
      scope_type: "MODULE",
      sensitivity: "INTERNAL",
      module_id: "rates",
      macro_object_code: "RATE_RECORD",
      otm_table_name: "RATE_GEO_COST",
      tags: ["CHAOS", "PRIMARY"]
    }
  });
  const alternate = await apiRequest("/api/v1/modules/assets/assets", {
    method: "POST",
    token,
    body: {
      name: `Chaos Asset Alternate ${suffix}`,
      description: "Client-safe chaos QA alternate asset.",
      asset_type: "TEMPLATE",
      category: "OTM_SETUP",
      visibility: "PROJECT",
      scope_type: "MODULE",
      sensitivity: "INTERNAL",
      module_id: "master_data",
      macro_object_code: "LOCATION",
      otm_table_name: "LOCATION",
      tags: ["CHAOS", "ALTERNATE"]
    }
  });

  return { alternate, primary, suffix };
}

async function createOrderReleaseTemplate(token, payload) {
  return apiRequest("/api/v1/modules/order-release-generator/templates", {
    method: "POST",
    token,
    body: payload
  });
}

async function seedOrderReleaseChaosData(token) {
  const suffix = Date.now().toString(36).toUpperCase();
  const primary = await createOrderReleaseTemplate(token, {
    code: `CHAOS_OR_PRIMARY_${suffix}`,
    name: `Chaos Order Release Primary ${suffix}`,
    description: "Client-safe chaos QA primary Order Release template.",
    required_columns: [
      "release_gid",
      "source_location_gid",
      "destination_location_gid",
      "early_pickup_date",
      "late_delivery_date",
      "item_gid",
      "packaged_item_gid",
      "weight",
      "weight_uom"
    ],
    optional_columns: ["remarks"],
    defaults: {
      release_gid: `OTM1.OR_CHAOS_PRIMARY_${suffix}`,
      source_location_gid: "OTM1.SOURCE_PRIMARY",
      destination_location_gid: "OTM1.DEST_PRIMARY",
      early_pickup_date: "2026-05-20 08:00:00",
      late_delivery_date: "2026-05-21 17:00:00",
      item_gid: "OTM1.ITEM_PRIMARY",
      packaged_item_gid: "OTM1.PACK_PRIMARY",
      weight: "100",
      weight_uom: "KG",
      remarks: "Primary chaos row"
    }
  });
  const alternate = await createOrderReleaseTemplate(token, {
    code: `CHAOS_OR_ALT_${suffix}`,
    name: `Chaos Order Release Alternate ${suffix}`,
    description: "Client-safe chaos QA alternate Order Release template.",
    required_columns: ["release_gid", "source_location_gid", "item_gid"],
    optional_columns: ["transport_mode"],
    defaults: {
      release_gid: `OTM1.OR_CHAOS_ALT_${suffix}`,
      source_location_gid: "OTM1.SOURCE_ALT",
      item_gid: "OTM1.ITEM_ALT",
      transport_mode: "LTL"
    }
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

async function selectAsset(page, name) {
  await page.locator(".load-plan-workflow-step").filter({ hasText: "Library" }).click();
  await page.getByLabel("Assets").getByRole("button", { name: new RegExp(name) }).first().click();
  await page.getByLabel("Selected asset", { exact: true }).getByText(name).waitFor();
}

async function selectOrderReleaseTemplate(page, code) {
  await page.getByRole("button", { name: /1Templates/ }).click();
  await page.getByLabel("Order Release templates").getByRole("button").filter({ hasText: code }).click();
  await page.getByLabel("Selected Order Release template").getByText(code).waitFor();
}

async function assertControlValue(locator, expected, description) {
  const value = await locator.inputValue();
  if (value !== expected) {
    throw new Error(`${description} expected value "${expected}" but received "${value}".`);
  }
}

async function assertSelectValue(locator, expected, description) {
  const value = await locator.inputValue();
  if (value !== expected) {
    throw new Error(`${description} expected selected value "${expected}" but received "${value}".`);
  }
}

async function runIntegrationMappingChaosJourney(page, seeded) {
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
}

async function runAssetsChaosJourney(page, seeded) {
  await page.locator('a[href="/assets"]').click();
  await page.getByRole("heading", { name: "Assets Library" }).waitFor();
  await page.getByLabel("Assets Library workflow").waitFor();

  await selectAsset(page, seeded.primary.name);
  await page.locator(".load-plan-workflow-step").filter({ hasText: "Create" }).click();
  await page.getByLabel("Asset name").fill("Dirty Asset Name That Must Not Leak");
  await page.getByLabel("Asset description").fill("Dirty asset description that must not leak.");
  await page.getByLabel("Asset module id").fill("dirty_module");
  await page.getByLabel("Asset macro object").fill("DIRTY_MACRO");
  await page.getByLabel("Asset OTM table").fill("DIRTY_TABLE");
  await page.getByLabel("Asset tags").fill("DIRTY,TAGS");

  await page.locator(".load-plan-workflow-step").filter({ hasText: "Version" }).click();
  await page.getByLabel("Asset version file").setInputFiles({
    name: "dirty_asset_version.md",
    mimeType: "text/markdown",
    buffer: Buffer.from("# dirty version that must not leak\n")
  });
  if (await page.getByRole("button", { name: "Upload version" }).isDisabled()) {
    throw new Error("Upload version should be enabled after selecting a draft file on the primary asset.");
  }

  await page.locator(".load-plan-workflow-step").filter({ hasText: "Link" }).click();
  await page.getByLabel("Asset link type").selectOption("OTM_TABLE");
  await page.getByLabel("Asset link target id").fill("DIRTY_TABLE");
  await page.getByLabel("Asset link target label").fill("Dirty target label");

  await selectAsset(page, seeded.alternate.name);
  await page.locator(".load-plan-workflow-step").filter({ hasText: "Create" }).click();
  await assertControlValue(page.getByLabel("Asset name"), seeded.alternate.name, "Asset draft name after selection switch");
  await assertControlValue(
    page.getByLabel("Asset description"),
    seeded.alternate.description,
    "Asset draft description after selection switch"
  );
  await assertControlValue(page.getByLabel("Asset module id"), "master_data", "Asset module draft after selection switch");
  await assertControlValue(page.getByLabel("Asset macro object"), "LOCATION", "Asset macro object after selection switch");
  await assertControlValue(page.getByLabel("Asset OTM table"), "LOCATION", "Asset OTM table after selection switch");
  await assertControlValue(page.getByLabel("Asset tags"), "CHAOS,ALTERNATE", "Asset tags after selection switch");

  await page.locator(".load-plan-workflow-step").filter({ hasText: "Version" }).click();
  if (await page.getByRole("button", { name: "Upload version" }).isEnabled()) {
    throw new Error("Upload version stayed enabled after switching assets; stale file selection leaked.");
  }

  await page.locator(".load-plan-workflow-step").filter({ hasText: "Link" }).click();
  await assertSelectValue(page.getByLabel("Asset link type"), "MODULE", "Asset link type after selection switch");
  await assertControlValue(page.getByLabel("Asset link target id"), "integration_mapping", "Asset link target id after selection switch");
  await assertControlValue(
    page.getByLabel("Asset link target label"),
    "Integration Mapping Studio",
    "Asset link target label after selection switch"
  );

  await page.locator('a[href="/home"]').click();
  await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
  await page.locator('a[href="/assets"]').click();
  await page.getByRole("heading", { name: "Assets Library" }).waitFor();
  await page.getByLabel("Selected asset", { exact: true }).getByText(seeded.alternate.name).waitFor();
}

async function runOrderReleaseChaosJourney(page, seeded) {
  await page.locator('a[href="/order-release-generator"]').click();
  await page.getByRole("heading", { name: "Order Release Generator" }).waitFor();

  await selectOrderReleaseTemplate(page, seeded.primary.code);
  await page.getByRole("button", { name: /2Batch/ }).click();
  await assertControlValue(
    page.getByLabel("Row 1 release_gid", { exact: true }),
    seeded.primary.defaults.release_gid,
    "Primary Order Release default release_gid"
  );
  await page.getByLabel("Row 1 release_gid", { exact: true }).fill("OTM1.DIRTY_RELEASE_THAT_MUST_NOT_LEAK");
  await page.getByLabel("Row 1 source_location_gid", { exact: true }).fill("OTM1.DIRTY_SOURCE");
  await page.getByLabel("Row 1 destination_location_gid", { exact: true }).fill("OTM1.DIRTY_DEST");
  await page.getByLabel("Row 1 early_pickup_date", { exact: true }).fill("2026-05-20 08:00:00");
  await page.getByLabel("Row 1 late_delivery_date", { exact: true }).fill("2026-05-21 17:00:00");
  await page.getByLabel("Row 1 item_gid", { exact: true }).fill("OTM1.DIRTY_ITEM");
  await page.getByLabel("Row 1 packaged_item_gid", { exact: true }).fill("OTM1.DIRTY_PACK");
  await page.getByLabel("Row 1 weight", { exact: true }).fill("125");
  await page.getByLabel("Row 1 weight_uom", { exact: true }).fill("KG");
  await page.getByLabel("Batch file name").fill("dirty_order_release_rows.json");
  await page.getByRole("button", { name: "Add row" }).click();
  await page.getByLabel("Order Release row editor").getByText("Row 2").waitFor();
  await page.getByRole("button", { name: "Remove row" }).last().click();
  await page.getByRole("button", { name: "Create batch" }).click();
  await page.getByText(/Order Release batch .* created\./).waitFor();
  await page.getByLabel("Active Order Release batch").getByText("VALID").waitFor();

  await page.getByRole("button", { name: /3Preview/ }).click();
  await page.getByRole("button", { name: "Preview XML" }).click();
  await page.getByText("Order Release XML preview generated.").waitFor();
  await page.getByLabel("Order Release XML preview").getByText("Transmission", { exact: true }).waitFor();

  await page.getByRole("button", { name: /5Submit/ }).click();
  await page.getByRole("button", { name: "Verify OTM submit guard" }).click();
  await page.getByText("Direct OTM submission is disabled in MVP0.").waitFor();
  await page.getByLabel("OTM submit guard").getByText("order_release_generator.submit_otm").waitFor();

  await selectOrderReleaseTemplate(page, seeded.alternate.code);
  await page.getByRole("button", { name: /2Batch/ }).click();
  await assertControlValue(
    page.getByLabel("Row 1 release_gid", { exact: true }),
    seeded.alternate.defaults.release_gid,
    "Alternate Order Release release_gid after template switch"
  );
  await assertControlValue(
    page.getByLabel("Row 1 source_location_gid", { exact: true }),
    seeded.alternate.defaults.source_location_gid,
    "Alternate Order Release source after template switch"
  );
  await assertControlValue(
    page.getByLabel("Row 1 item_gid", { exact: true }),
    seeded.alternate.defaults.item_gid,
    "Alternate Order Release item after template switch"
  );
  await assertControlValue(
    page.getByLabel("Row 1 transport_mode", { exact: true }),
    "LTL",
    "Alternate Order Release transport mode after template switch"
  );
  if ((await page.getByLabel("Order Release row editor").getByText("Row 2").count()) > 0) {
    throw new Error("Order Release template switch kept a stale extra row.");
  }
  if ((await page.getByLabel("Order Release row editor").getByText("destination_location_gid").count()) > 0) {
    throw new Error("Order Release template switch kept a field that belongs only to the previous template.");
  }
  if (await page.getByLabel("Active Order Release batch", { exact: true }).isVisible().catch(() => false)) {
    throw new Error("Order Release template switch kept the previous active batch.");
  }

  await page.getByRole("button", { name: /3Preview/ }).click();
  if (await page.getByLabel("Order Release XML preview", { exact: true }).isVisible().catch(() => false)) {
    throw new Error("Order Release template switch left stale XML preview visible.");
  }
  if (await page.getByText("Direct OTM submission is disabled in MVP0.").isVisible().catch(() => false)) {
    throw new Error("Order Release template switch left stale submit guard feedback visible.");
  }
  await page.getByRole("button", { name: /5Submit/ }).click();
  if (await page.getByLabel("OTM submit guard", { exact: true }).isVisible().catch(() => false)) {
    throw new Error("Order Release template switch left stale submit guard details visible.");
  }

  await page.locator('a[href="/home"]').click();
  await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
  await page.locator('a[href="/order-release-generator"]').click();
  await page.getByRole("heading", { name: "Order Release Generator" }).waitFor();
  await page.getByLabel("Order Release templates").getByText(seeded.alternate.code).waitFor();
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
  const integrationMappingSeed = await seedIntegrationMappingChaosData(token);
  const assetsSeed = await seedAssetsChaosData(token);
  const orderReleaseSeed = await seedOrderReleaseChaosData(token);

  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 840 } });
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
    await signIn(page);
    await runIntegrationMappingChaosJourney(page, integrationMappingSeed);
    await runAssetsChaosJourney(page, assetsSeed);
    await runOrderReleaseChaosJourney(page, orderReleaseSeed);

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
          journeys: [
            "integration-mapping-out-of-order-definition-switch",
            "assets-dirty-draft-file-link-selection-switch",
            "order-release-template-switch-dirty-row-preview-submit-guard"
          ],
          baseUrl,
          apiBaseUrl,
          primary_definition_code: integrationMappingSeed.primary.code,
          alternate_definition_code: integrationMappingSeed.alternate.code,
          primary_asset_name: assetsSeed.primary.name,
          alternate_asset_name: assetsSeed.alternate.name,
          primary_order_release_template_code: orderReleaseSeed.primary.code,
          alternate_order_release_template_code: orderReleaseSeed.alternate.code
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
