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

  const suffix = Date.now().toString(36).toUpperCase();
  const systemCode = `EXT_DELIVERY_API_UI_${suffix}`;
  const endpointCode = `CREATE_DELIVERY_UI_${suffix}`;
  const definitionCode = `PS_TO_EXTERNAL_DELIVERY_UI_${suffix}`;
  const definitionName = `Planned Shipment to External Delivery UI ${suffix}`;

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

    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    await page.locator('a[href="/integration-mapping"]').click();
    await page.getByRole("heading", { name: "Integration Mapping Studio" }).waitFor();

    await page.getByLabel("System code").fill(systemCode);
    await page.getByLabel("System name").fill(`External Delivery API UI ${suffix}`);
    await page.getByLabel("System type").selectOption("EXTERNAL_API");
    await page.getByLabel("System base URL").fill("https://api.example.test");
    await page.getByLabel("System description").fill("Synthetic external system metadata.");
    await page.getByRole("button", { name: "Create system" }).click();
    await page.getByText(`Created system ${systemCode}.`).waitFor();
    await page.getByLabel("Integration systems").getByText(systemCode, { exact: true }).waitFor();

    await page.getByLabel("Endpoint system").selectOption({ label: systemCode });
    await page.getByLabel("Endpoint code").fill(endpointCode);
    await page.getByLabel("Endpoint name").fill(`Create Delivery UI ${suffix}`);
    await page.getByLabel("Endpoint path").fill("/deliveries");
    await page.getByLabel("Endpoint method").selectOption("POST");
    await page.getByLabel("Endpoint payload format").selectOption("JSON");
    await page.getByLabel("Endpoint description").fill("Synthetic endpoint metadata.");
    await page.getByRole("button", { name: "Create endpoint" }).click();
    await page.getByText(`Created endpoint ${endpointCode}.`).waitFor();
    await page.getByLabel("Integration endpoints").getByText(endpointCode, { exact: true }).waitFor();

    await page.getByRole("button", { name: /^2 Definition$/ }).click();
    await page.getByLabel("Definition code").fill(definitionCode);
    await page.getByLabel("Definition name").fill(definitionName);
    await page.getByLabel("Source system").fill("OTM");
    await page.getByLabel("Target system").fill("EXTERNAL_DELIVERY");
    await page.getByLabel("Source format").selectOption("XML");
    await page.getByLabel("Target format").selectOption("JSON");
    await page.getByLabel("Definition description").fill("Synthetic browser mapping definition.");
    await page.getByRole("button", { name: "Create definition" }).click();
    await page.getByText(`Created definition ${definitionCode}.`).waitFor();
    await page.getByText(definitionCode, { exact: true }).first().waitFor();

    await page.locator(".integration-workflow-step").filter({ hasText: "Payloads & schemas" }).click();
    const payloadForm = page.locator(".integration-payload-form");
    await payloadForm.getByLabel("Payload role").selectOption("SOURCE_SAMPLE");
    await payloadForm.getByLabel("Payload format").selectOption("XML");
    await payloadForm.getByLabel("Payload file name").fill(`planned_shipment_manual_${suffix}.xml`);
    await payloadForm.getByLabel("Payload description").fill("Synthetic browser source payload.");
    await payloadForm
      .getByLabel("Payload content")
      .fill(
        "<Transmission><Shipment><ShipmentGid>DEMO.SHIPMENT_001</ShipmentGid><ShipmentStop><StopSequence>1</StopSequence></ShipmentStop></Shipment></Transmission>"
      );
    await page.getByRole("button", { name: "Create payload and schema" }).click();
    await page.getByText(`Payload planned_shipment_manual_${suffix}.xml and schema Transmission created.`).waitFor();

    await payloadForm.getByLabel("Payload role").selectOption("TARGET_SAMPLE");
    await payloadForm.getByLabel("Payload format").selectOption("JSON");
    await payloadForm.getByLabel("Payload file name").fill(`external_delivery_manual_${suffix}.json`);
    await payloadForm.getByLabel("Payload description").fill("Synthetic browser target payload.");
    await payloadForm.getByLabel("Payload content").fill('{"header":{"shipmentId":"DEMO"},"deliveries":[{"sequence":1}]}');
    await page.getByRole("button", { name: "Create payload and schema" }).click();
    await page.getByText(`Payload external_delivery_manual_${suffix}.json and schema $ created.`).waitFor();

    await page.getByLabel("Selected definition schema documents").getByText("Transmission", { exact: true }).waitFor();
    await page.getByLabel("Selected definition schema documents").getByText("$", { exact: true }).waitFor();

    await page.locator(".integration-workflow-step").filter({ hasText: "Mapping rules" }).click();
    await page.getByLabel("Mapping source node").selectOption("/Transmission/Shipment/ShipmentGid");
    await page.getByLabel("Mapping target node").selectOption("$.header.shipmentId");
    await page.getByLabel("Transform type").selectOption("DIRECT");
    await page.getByLabel("Mapping description").fill("Synthetic direct mapping from shipment id.");
    await page.getByRole("button", { name: "Create mapping" }).click();
    await page.getByText("Created mapping $.header.shipmentId.").waitFor();
    await page.getByLabel("Selected definition mappings").getByText("$.header.shipmentId", { exact: true }).waitFor();

    await page.getByLabel("Loop source schema").selectOption({ label: "Transmission" });
    await page.getByLabel("Loop target schema").selectOption({ label: "$" });
    await page.getByLabel("Loop name").fill("Synthetic delivery loop");
    await page.getByLabel("Loop source node").selectOption("/Transmission/Shipment/ShipmentStop");
    await page.getByLabel("Loop target node").selectOption("$.deliveries[]");
    await page.getByLabel("Loop description").fill("Synthetic delivery loop metadata.");
    await page.getByRole("button", { name: "Create loop" }).click();
    await page.getByText("Created loop Synthetic delivery loop.").waitFor();
    await page.getByLabel("Selected definition loops").getByText("Synthetic delivery loop", { exact: true }).waitFor();

    await page.getByLabel("Join source schema").selectOption({ label: "Transmission" });
    await page.getByLabel("Join name").fill("Synthetic shipment stop join");
    await page.getByLabel("Join left node").selectOption("/Transmission/Shipment/ShipmentGid");
    await page.getByLabel("Join right node").selectOption("/Transmission/Shipment/ShipmentStop/StopSequence");
    await page.getByLabel("Join operator").selectOption("EQ");
    await page.getByLabel("Join description").fill("Synthetic join metadata.");
    await page.getByRole("button", { name: "Create join" }).click();
    await page.getByText("Created join Synthetic shipment stop join.").waitFor();
    await page.getByLabel("Selected definition joins").getByText("Synthetic shipment stop join", { exact: true }).waitFor();

    await page.getByLabel("Lookup source schema").selectOption({ label: "Transmission" });
    await page.getByLabel("Lookup target schema").selectOption({ label: "$" });
    await page.getByLabel("Lookup name").fill("Synthetic carrier lookup");
    await page.getByLabel("Lookup input node").selectOption("/Transmission/Shipment/ShipmentGid");
    await page.getByLabel("Lookup output node").selectOption("$.header.shipmentId");
    await page.getByLabel("Lookup type").selectOption("MOCK");
    await page.getByLabel("Lookup description").fill("Synthetic lookup metadata.");
    await page.getByLabel("Lookup mock response JSON").fill('{"shipmentId":"DEMO-SHIPMENT"}');
    await page.getByRole("button", { name: "Create lookup" }).click();
    await page.getByText("Created lookup Synthetic carrier lookup.").waitFor();
    await page.getByLabel("Selected definition lookups").getByText("Synthetic carrier lookup", { exact: true }).waitFor();

    await page.getByRole("button", { name: "Reset mapping rule drafts" }).click();
    const mappingForm = page.locator(".integration-mapping-form");
    await mappingForm.getByLabel("Source schema").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected mapping source schema after reset: ${element.value}`);
    });
    await mappingForm.getByLabel("Target schema").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected mapping target schema after reset: ${element.value}`);
    });
    await mappingForm.getByLabel("Source path").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected mapping source path after reset: ${element.value}`);
    });
    await page.locator(".integration-loop-form").getByLabel("Loop source schema").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected loop source schema after reset: ${element.value}`);
    });
    await page.locator(".integration-join-form").getByLabel("Join source schema").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected join source schema after reset: ${element.value}`);
    });
    await page.locator(".integration-lookup-form").getByLabel("Lookup mock response JSON").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected lookup mock JSON after reset: ${element.value}`);
    });
    if (await page.getByText("Created lookup Synthetic carrier lookup.").isVisible().catch(() => false)) {
      throw new Error("Lookup success feedback stayed visible after mapping rule reset.");
    }

    await page.getByRole("button", { name: "Validate definition" }).click();
    await page.getByText("Validation passed with 0 issue(s).").waitFor();
    await page.getByRole("button", { name: "Preview definition" }).click();
    await page.getByText(/^Preview artifact .+ generated by job .+\.$/).waitFor();
    await page.getByRole("button", { name: "Generate spec" }).click();
    await page.getByText(/^Spec artifact .+ generated by job .+\.$/).waitFor();
    const generatedArtifactsPanel = page.getByLabel("Integration mapping generated artifacts");
    await generatedArtifactsPanel.getByText("integration_mapping_spec.md", { exact: true }).waitFor();
    const downloadPromise = page.waitForEvent("download");
    await generatedArtifactsPanel
      .locator(".artifact-list-item")
      .filter({ hasText: "integration_mapping_spec.md" })
      .getByRole("button", { name: "Download" })
      .click();
    const download = await downloadPromise;
    if (download.suggestedFilename() !== "integration_mapping_spec.md") {
      throw new Error(`Unexpected Integration Mapping artifact filename: ${download.suggestedFilename()}`);
    }
    await page.getByText("Download started: integration_mapping_spec.md.").waitFor();

    await page.locator('a[href="/home"]').click();
    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    await page.locator('a[href="/integration-mapping"]').click();
    await page.getByRole("heading", { name: "Integration Mapping Studio" }).waitFor();
    await page.getByText(definitionCode, { exact: true }).first().waitFor();

    if (consoleErrors.length || failedResponses.length) {
      throw new Error(
        [
          "Integration Mapping browser functional QA detected runtime failures.",
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
          journey: "integration-mapping-definition-samples-mapping-preview-spec-return",
          baseUrl,
          apiBaseUrl,
          system_code: systemCode,
          endpoint_code: endpointCode,
          definition_code: definitionCode
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
