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

async function apiDownloadText(path, { token } = {}) {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    }
  });
  if (!response.ok) {
    const responseText = await response.text();
    throw new Error(`GET ${path} failed with HTTP ${response.status}: ${responseText}`);
  }
  return response.text();
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
  const alternateDefinitionCode = `ALT_EXTERNAL_DELIVERY_UI_${suffix}`;
  const scenarioDefinitionCode = `PS_TO_EXTERNAL_DELIVERY_NDD_UI_${suffix}`;

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
    const isExpectedBlockedPreview =
      response.status() === 409 && response.url().includes("/api/v1/modules/integration-mapping/definitions/") && response.url().endsWith("/preview");
    if (response.status() >= 400 && !isExpectedBlockedPreview) {
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

    await page.getByLabel("Definition code").fill(alternateDefinitionCode);
    await page.getByLabel("Definition name").fill(`Alternate External Delivery UI ${suffix}`);
    await page.getByLabel("Source system").fill("OTM");
    await page.getByLabel("Target system").fill("EXTERNAL_DELIVERY_ALT");
    await page.getByLabel("Source format").selectOption("XML");
    await page.getByLabel("Target format").selectOption("JSON");
    await page.getByLabel("Definition description").fill("Synthetic alternate browser mapping definition.");
    await page.getByRole("button", { name: "Create definition" }).click();
    await page.getByText(`Created definition ${alternateDefinitionCode}.`).waitFor();

    await page.getByLabel("Definition code").fill(scenarioDefinitionCode);
    await page.getByLabel("Definition name").fill(`Required Target Scenario UI ${suffix}`);
    await page.getByLabel("Source system").fill("OTM");
    await page.getByLabel("Target system").fill("EXTERNAL_DELIVERY_NDD");
    await page.getByLabel("Source format").selectOption("XML");
    await page.getByLabel("Target format").selectOption("JSON");
    await page.getByLabel("Definition description").fill("Synthetic required target scenario definition.");
    await page.getByRole("button", { name: "Create definition" }).click();
    await page.getByText(`Created definition ${scenarioDefinitionCode}.`).waitFor();

    await page.locator(".integration-workflow-step").filter({ hasText: "Definitions list" }).click();
    await page.getByLabel("Integration mapping definitions").getByRole("button", { name: new RegExp(definitionCode) }).click();
    await page.getByLabel("Selected integration mapping definition").getByText(definitionCode, { exact: true }).waitFor();

    await page.locator(".integration-workflow-step").filter({ hasText: "Payloads & schemas" }).click();
    const payloadForm = page.locator(".integration-payload-form");
    await payloadForm.getByLabel("Payload role").selectOption("SOURCE_SAMPLE");
    await payloadForm.getByLabel("Payload format").selectOption("XML");
    await payloadForm.getByLabel("Payload file name").fill(`planned_shipment_manual_${suffix}.xml`);
    await payloadForm.getByLabel("Payload description").fill("Synthetic browser source payload.");
    await payloadForm
      .getByLabel("Payload content")
      .fill(
        [
          "<Transmission><Shipment><ShipmentGid>DEMO.SHIPMENT_001</ShipmentGid>",
          "<StartDt><PlannedTime>20260525103000</PlannedTime></StartDt>",
          "<ShipmentStop><StopSequence>1</StopSequence><StopSequenceCopy>1</StopSequenceCopy><ShipmentStopDetail><ShipUnitGid><Gid><Xid>SU-001</Xid></Gid></ShipUnitGid></ShipmentStopDetail></ShipmentStop>",
          "<ShipUnit><ShipUnitGid><Gid><Xid>SU-001</Xid></Gid></ShipUnitGid><ShipUnitContent><ReleaseGid><Gid><Xid>REL-001</Xid></Gid></ReleaseGid></ShipUnitContent></ShipUnit>",
          "<Release><ReleaseGid><Gid><Xid>REL-001</Xid></Gid></ReleaseGid><ReleaseRefnum><ReleaseRefnumQualifierGid><Gid><Xid>RFN_CHAVE_ACESSO</Xid></Gid></ReleaseRefnumQualifierGid><ReleaseRefnumValue>KEY-001</ReleaseRefnumValue></ReleaseRefnum></Release>",
          "</Shipment></Transmission>"
        ].join("")
      );
    await page.getByRole("button", { name: "Create payload and schema" }).click();
    await page.getByText(`Payload planned_shipment_manual_${suffix}.xml and schema Transmission created.`).waitFor();

    await payloadForm.getByLabel("Payload role").selectOption("TARGET_SAMPLE");
    await payloadForm.getByLabel("Payload format").selectOption("JSON");
    await payloadForm.getByLabel("Payload file name").fill(`external_delivery_manual_${suffix}.json`);
    await payloadForm.getByLabel("Payload description").fill("Synthetic browser target payload.");
    await payloadForm
      .getByLabel("Payload content")
      .fill('{"status":"","issuedAt":"","header":{"shipmentId":"DEMO","accessKey":"","filteredAccessKey":"","releaseCount":0},"deliveries":[{"sequence":1,"accessKey":"","carrierName":""}]}');
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
    await page.getByLabel("Join left node").selectOption("/Transmission/Shipment/ShipmentStop/StopSequence");
    await page.getByLabel("Join right node").selectOption("/Transmission/Shipment/ShipmentStop/StopSequenceCopy");
    await page.getByLabel("Join operator").selectOption("EQ");
    await page.getByLabel("Join description").fill("Synthetic join metadata.");
    await page.locator(".integration-join-form").getByRole("button", { name: "Create join", exact: true }).click();
    await page.getByText("Created join Synthetic shipment stop join.").waitFor();
    await page.getByLabel("Selected definition joins").getByText("Synthetic shipment stop join", { exact: true }).waitFor();

    await page.getByLabel("Join binding source schema").selectOption({ label: "Transmission" });
    await page.getByLabel("Join binding name").fill("Stop to release binding");
    const joinBindingSelects = page.locator(".integration-join-binding-form select");
    await joinBindingSelects.nth(1).selectOption("/Transmission/Shipment/ShipmentStop");
    await joinBindingSelects.nth(2).selectOption("/Transmission/Shipment/Release");
    await joinBindingSelects.nth(3).selectOption("/Transmission/Shipment/ShipmentStop");
    await page.getByLabel("Hop 1 left value path").fill("ShipmentStopDetail/ShipUnitGid/Gid/Xid");
    await joinBindingSelects.nth(4).selectOption("/Transmission/Shipment/ShipUnit");
    await page.getByLabel("Hop 1 right value path").fill("ShipUnitGid/Gid/Xid");
    await page.getByLabel("Hop 1 result alias").fill("stop_ship_unit");
    await joinBindingSelects.nth(5).selectOption("/Transmission/Shipment/ShipUnit");
    await page.getByLabel("Hop 2 left value path").fill("ShipUnitContent/ReleaseGid/Gid/Xid");
    await joinBindingSelects.nth(6).selectOption("/Transmission/Shipment/Release");
    await page.getByLabel("Hop 2 right value path").fill("ReleaseGid/Gid/Xid");
    await page.getByLabel("Hop 2 result alias").fill("ship_unit_release");
    await page.getByLabel("Join binding description").fill("Synthetic two-hop binding metadata.");
    await page.getByRole("button", { name: "Create join binding" }).click();
    await page.getByText("Created join binding Stop to release binding.").waitFor();
    await page.getByLabel("Selected definition join bindings").getByText("Stop to release binding", { exact: true }).waitFor();

    await page.getByLabel("Alias source context").selectOption("ship_unit_release");
    await page.getByLabel("Mapping source node").selectOption("/Transmission/Shipment/Release/ReleaseRefnum/ReleaseRefnumValue");
    await page.getByLabel("Mapping target node").selectOption("$.header.accessKey");
    await page.getByLabel("Mapping description").fill("Synthetic alias-backed access key mapping.");
    await page.getByRole("button", { name: "Create mapping" }).click();
    await page.getByText("Created mapping $.header.accessKey.").waitFor();
    await page.getByLabel("Selected definition mappings").getByText("$.header.accessKey", { exact: true }).waitFor();

    await page.getByLabel("Alias source context").selectOption("ship_unit_release");
    await page.getByLabel("Mapping source node").selectOption("/Transmission/Shipment/Release/ReleaseRefnum/ReleaseRefnumValue");
    await page.getByLabel("Mapping target node").selectOption("$.deliveries[].accessKey");
    await page.getByLabel("Mapping description").fill("Synthetic delivery alias-backed access key mapping.");
    await page.getByRole("button", { name: "Create mapping" }).click();
    await page.getByText("Created mapping $.deliveries[].accessKey.").waitFor();
    await page.getByLabel("Selected definition mappings").getByText("$.deliveries[].accessKey", { exact: true }).waitFor();

    await page.getByLabel("Mapping source node").selectOption("/Transmission/Shipment/ShipmentStop/StopSequence");
    await page.getByLabel("Mapping target node").selectOption("$.deliveries[].sequence");
    await page.getByLabel("Transform type").selectOption("DIRECT");
    await page.getByLabel("Mapping description").fill("Synthetic delivery stop sequence mapping.");
    await page.getByRole("button", { name: "Create mapping" }).click();
    await page.getByText("Created mapping $.deliveries[].sequence.").waitFor();
    await page.getByLabel("Selected definition mappings").getByText("$.deliveries[].sequence", { exact: true }).waitFor();

    await page.getByLabel("Mapping source node").selectOption("/Transmission/Shipment/ShipmentGid");
    await page.getByLabel("Mapping target node").selectOption("$.status");
    await page.getByLabel("Transform type").selectOption("CONSTANT");
    await page.getByLabel("Constant value").fill("ACCEPTED");
    await page.getByLabel("Mapping description").fill("Synthetic constant status mapping.");
    await page.getByRole("button", { name: "Create mapping" }).click();
    await page.getByText("Created mapping $.status.").waitFor();
    await page.getByLabel("Selected definition mappings").getByText("$.status", { exact: true }).waitFor();

    await page.getByLabel("Mapping source node").selectOption("/Transmission/Shipment/StartDt/PlannedTime");
    await page.getByLabel("Mapping target node").selectOption("$.issuedAt");
    await page.getByLabel("Transform type").selectOption("DATE_FORMAT");
    await page.getByLabel("Date source format").fill("OTM_GLOGDATE");
    await page.getByLabel("Date target format").fill("ISO8601");
    await page.getByLabel("Date timezone offset").fill("-03:00");
    await page.getByLabel("Mapping description").fill("Synthetic planned time ISO mapping.");
    await page.getByRole("button", { name: "Create mapping" }).click();
    await page.getByText("Created mapping $.issuedAt.").waitFor();
    await page.getByLabel("Selected definition mappings").getByText("$.issuedAt", { exact: true }).waitFor();

    await page.getByLabel("Mapping source node").selectOption("/Transmission/Shipment/Release/ReleaseRefnum/ReleaseRefnumValue");
    await page.getByLabel("Mapping target node").selectOption("$.header.filteredAccessKey");
    await page.getByLabel("Transform type").selectOption("FILTER_BY_QUALIFIER");
    await page.getByLabel("Filter collection path").fill("/Transmission/Shipment/Release/ReleaseRefnum");
    await page.getByLabel("Filter qualifier path").fill("ReleaseRefnumQualifierGid/Gid/Xid");
    await page.getByLabel("Filter qualifier value").fill("RFN_CHAVE_ACESSO");
    await page.getByLabel("Filter value path").fill("ReleaseRefnumValue");
    await page.getByLabel("Mapping description").fill("Synthetic filtered access key mapping.");
    await page.getByRole("button", { name: "Create mapping" }).click();
    await page.getByText("Created mapping $.header.filteredAccessKey.").waitFor();
    await page.getByLabel("Selected definition mappings").getByText("$.header.filteredAccessKey", { exact: true }).waitFor();

    await page.getByLabel("Mapping source node").selectOption("/Transmission/Shipment/Release/ReleaseGid/Gid/Xid");
    await page.getByLabel("Mapping target node").selectOption("$.header.releaseCount");
    await page.getByLabel("Transform type").selectOption("COUNT_DISTINCT");
    await page.getByLabel("Count collection path").fill("/Transmission/Shipment/Release");
    await page.getByLabel("Count value path").fill("ReleaseGid/Gid/Xid");
    await page.getByLabel("Mapping description").fill("Synthetic release count mapping.");
    await page.getByRole("button", { name: "Create mapping" }).click();
    await page.getByText("Created mapping $.header.releaseCount.").waitFor();
    await page.getByLabel("Selected definition mappings").getByText("$.header.releaseCount", { exact: true }).waitFor();

    await page.getByLabel("Lookup source schema").selectOption({ label: "Transmission" });
    await page.getByLabel("Lookup target schema").selectOption({ label: "$" });
    await page.getByLabel("Lookup name").fill("Synthetic carrier lookup");
    await page.getByLabel("Lookup input node").selectOption("/Transmission/Shipment/ShipmentStop/StopSequence");
    await page.getByLabel("Lookup output node").selectOption("$.deliveries[].carrierName");
    await page.getByLabel("Lookup type").selectOption("MOCK");
    await page.getByLabel("Lookup description").fill("Synthetic lookup metadata.");
    await page.getByLabel("Lookup mock response JSON").fill('{"carrierName":"Synthetic Carrier"}');
    await page.getByRole("button", { name: "Create lookup" }).click();
    await page.getByText("Created lookup Synthetic carrier lookup.").waitFor();
    await page.getByLabel("Selected definition lookups").getByText("Synthetic carrier lookup", { exact: true }).waitFor();

    await page.getByLabel("Response schema").selectOption({ label: "$" });
    await page.getByLabel("Response handler name").fill("Accepted delivery response");
    await page.getByLabel("Response path node").selectOption("$.status");
    await page.getByLabel("Success condition").selectOption("EQUALS");
    await page.getByLabel("Expected value").fill("ACCEPTED");
    await page.getByLabel("Outcome").selectOption("SUCCESS");
    await page.getByLabel("Response handler description").fill("Synthetic response handler metadata.");
    await page.getByRole("button", { name: "Create response handler" }).click();
    await page.getByText("Created response handler Accepted delivery response.").waitFor();
    await page.getByLabel("Selected definition response handlers").getByText("Accepted delivery response", { exact: true }).waitFor();
    await page.getByLabel("Integration mapping grouped executable review").getByText("EQUALS ACCEPTED", { exact: true }).waitFor();

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
    await mappingForm.getByLabel("Alias source context").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected mapping source alias after reset: ${element.value}`);
    });
    await mappingForm.getByLabel("Constant value").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected constant value after reset: ${element.value}`);
    });
    await mappingForm.getByLabel("Date source format").evaluate((element) => {
      if (element.value !== "OTM_GLOGDATE") throw new Error(`Unexpected date source format after reset: ${element.value}`);
    });
    await mappingForm.getByLabel("Date target format").evaluate((element) => {
      if (element.value !== "ISO8601") throw new Error(`Unexpected date target format after reset: ${element.value}`);
    });
    await mappingForm.getByLabel("Date timezone offset").evaluate((element) => {
      if (element.value !== "-03:00") throw new Error(`Unexpected date timezone offset after reset: ${element.value}`);
    });
    await mappingForm.getByLabel("Filter collection path").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected filter collection path after reset: ${element.value}`);
    });
    await mappingForm.getByLabel("Filter qualifier path").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected filter qualifier path after reset: ${element.value}`);
    });
    await mappingForm.getByLabel("Filter qualifier value").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected filter qualifier value after reset: ${element.value}`);
    });
    await mappingForm.getByLabel("Filter value path").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected filter value path after reset: ${element.value}`);
    });
    await mappingForm.getByLabel("Count collection path").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected count collection path after reset: ${element.value}`);
    });
    await mappingForm.getByLabel("Count value path").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected count value path after reset: ${element.value}`);
    });
    await page.locator(".integration-loop-form").getByLabel("Loop source schema").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected loop source schema after reset: ${element.value}`);
    });
    await page.locator(".integration-join-form").getByLabel("Join source schema").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected join source schema after reset: ${element.value}`);
    });
    await page.locator(".integration-join-binding-form").getByLabel("Join binding source schema").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected join binding source schema after reset: ${element.value}`);
    });
    await page.locator(".integration-join-binding-form").getByLabel("Hop 1 left value path").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected join binding hop 1 left value after reset: ${element.value}`);
    });
    await page.locator(".integration-join-binding-form").getByLabel("Hop 2 result alias").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected join binding hop 2 alias after reset: ${element.value}`);
    });
    await page.locator(".integration-lookup-form").getByLabel("Lookup mock response JSON").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected lookup mock JSON after reset: ${element.value}`);
    });
    await page.locator(".integration-response-handler-form").getByLabel("Response schema").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected response schema after reset: ${element.value}`);
    });
    await page.locator(".integration-response-handler-form").getByLabel("Response handler name").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected response handler name after reset: ${element.value}`);
    });
    await page.locator(".integration-response-handler-form").getByRole("textbox", { name: "Response path" }).evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected response path after reset: ${element.value}`);
    });
    await page.locator(".integration-response-handler-form").getByLabel("Success condition").evaluate((element) => {
      if (element.value !== "EXISTS") throw new Error(`Unexpected response condition after reset: ${element.value}`);
    });
    await page.locator(".integration-response-handler-form").getByLabel("Outcome").evaluate((element) => {
      if (element.value !== "SUCCESS") throw new Error(`Unexpected response outcome after reset: ${element.value}`);
    });
    if (await page.getByText("Created response handler Accepted delivery response.").isVisible().catch(() => false)) {
      throw new Error("Response handler success feedback stayed visible after mapping rule reset.");
    }

    await page.getByRole("button", { name: "Validate definition" }).click();
    await page.getByText("Validation passed with 0 issue(s).").waitFor();
    await page.getByLabel("Integration mapping readiness").getByText("Specification readiness", { exact: true }).waitFor();
    await page.getByLabel("Integration mapping readiness").getByText("Preview executable", { exact: true }).waitFor();
    await page.getByLabel("Integration mapping readiness").getByText("No specification blockers reported", { exact: true }).waitFor();
    await page.getByRole("button", { name: "Preview definition" }).click();
    await page.getByText(/^Preview artifact .+ generated by job .+\.$/).waitFor();
    const definitions = await apiRequest("/api/v1/modules/integration-mapping/definitions", { token });
    const createdDefinition = definitions.items.find((item) => item.code === definitionCode);
    if (!createdDefinition) {
      throw new Error(`Could not find created Integration Mapping definition ${definitionCode}.`);
    }
    const previewArtifacts = await apiRequest(
      `/api/v1/modules/integration-mapping/definitions/${createdDefinition.id}/artifacts`,
      { token }
    );
    const previewArtifact = previewArtifacts.items.find((item) => item.artifact_type === "integration_preview");
    if (!previewArtifact?.download_url) {
      throw new Error("Integration Mapping preview artifact was not available for download.");
    }
    const previewPayload = JSON.parse(await apiDownloadText(previewArtifact.download_url, { token }));
    const preview = previewPayload.preview;
    if (preview.mode !== "synthetic_executable_json") {
      throw new Error(`Expected executable Integration Mapping preview, received ${preview.mode}.`);
    }
    if (preview.target_json?.header?.shipmentId !== "DEMO.SHIPMENT_001") {
      throw new Error(`Unexpected preview header shipment id: ${preview.target_json?.header?.shipmentId}`);
    }
    if (preview.target_json?.header?.accessKey !== "KEY-001") {
      throw new Error(`Unexpected preview header access key: ${preview.target_json?.header?.accessKey}`);
    }
    if (preview.target_json?.status !== "ACCEPTED") {
      throw new Error(`Unexpected preview status: ${preview.target_json?.status}`);
    }
    if (preview.target_json?.issuedAt !== "2026-05-25T10:30:00-03:00") {
      throw new Error(`Unexpected preview issuedAt: ${preview.target_json?.issuedAt}`);
    }
    if (preview.target_json?.header?.filteredAccessKey !== "KEY-001") {
      throw new Error(`Unexpected preview filtered access key: ${preview.target_json?.header?.filteredAccessKey}`);
    }
    if (preview.target_json?.header?.releaseCount !== 1) {
      throw new Error(`Unexpected preview release count: ${preview.target_json?.header?.releaseCount}`);
    }
    const firstDelivery = preview.target_json?.deliveries?.[0];
    if (firstDelivery?.sequence !== "1" || firstDelivery?.accessKey !== "KEY-001") {
      throw new Error(`Unexpected preview delivery payload: ${JSON.stringify(firstDelivery)}`);
    }
    if (firstDelivery?.carrierName !== "Synthetic Carrier") {
      throw new Error(`Unexpected preview delivery lookup value: ${JSON.stringify(firstDelivery)}`);
    }
    const hasLoopAliasProvenance = preview.field_provenance?.some(
      (item) => item.source_alias === "ship_unit_release" && item.target_item_path === "$.deliveries[0].accessKey"
    );
    if (!hasLoopAliasProvenance) {
      throw new Error("Preview artifact did not include delivery alias field provenance.");
    }
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

    await page.locator(".integration-workflow-step").filter({ hasText: "Definitions list" }).click();
    await page.getByLabel("Integration mapping definitions").getByRole("button", { name: new RegExp(alternateDefinitionCode) }).click();
    await page.getByLabel("Selected integration mapping definition").getByText(alternateDefinitionCode, { exact: true }).waitFor();
    if (await page.getByText("Download started: integration_mapping_spec.md.").isVisible().catch(() => false)) {
      throw new Error("Integration Mapping kept stale artifact download feedback after switching definitions.");
    }
    if (await page.getByLabel("Integration mapping readiness").isVisible().catch(() => false)) {
      throw new Error("Integration Mapping kept stale readiness after switching definitions.");
    }
    await page.getByLabel("Integration mapping generated artifacts").getByText("No generated artifacts for this definition.").waitFor();
    await page.locator(".integration-workflow-step").filter({ hasText: "Mapping rules" }).click();
    await page.locator(".integration-mapping-form").getByLabel("Source schema").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected mapping source schema after definition switch: ${element.value}`);
    });
    await page.locator(".integration-mapping-form").getByLabel("Target schema").evaluate((element) => {
      if (element.value !== "") throw new Error(`Unexpected mapping target schema after definition switch: ${element.value}`);
    });

    await page.locator(".integration-workflow-step").filter({ hasText: "Payloads & schemas" }).click();
    await payloadForm.getByLabel("Payload role").selectOption("SOURCE_SAMPLE");
    await payloadForm.getByLabel("Payload format").selectOption("XML");
    await payloadForm.getByLabel("Payload file name").fill(`planned_shipment_negative_${suffix}.xml`);
    await payloadForm.getByLabel("Payload description").fill("Synthetic negative browser source payload.");
    await payloadForm
      .getByLabel("Payload content")
      .fill(
        [
          "<Transmission><Shipment><ShipmentGid>DEMO.SHIPMENT_NEGATIVE</ShipmentGid>",
          "<ShipmentStop><StopSequence>1</StopSequence><ShipmentStopDetail><ShipUnitGid><Gid><Xid>SU-NEG</Xid></Gid></ShipUnitGid></ShipmentStopDetail></ShipmentStop>",
          "<ShipUnit><ShipUnitGid><Gid><Xid>SU-NEG</Xid></Gid></ShipUnitGid><ShipUnitContent><ReleaseGid><Gid><Xid>REL-NEG</Xid></Gid></ReleaseGid></ShipUnitContent></ShipUnit>",
          "<Release><ReleaseGid><Gid><Xid>REL-NEG</Xid></Gid></ReleaseGid><ReleaseRefnum><ReleaseRefnumQualifierGid><Gid><Xid>RFN_CHAVE_ACESSO</Xid></Gid></ReleaseRefnumQualifierGid><ReleaseRefnumValue>KEY-NEG</ReleaseRefnumValue></ReleaseRefnum></Release>",
          "</Shipment></Transmission>"
        ].join("")
      );
    await page.getByRole("button", { name: "Create payload and schema" }).click();
    await page.getByText(`Payload planned_shipment_negative_${suffix}.xml and schema Transmission created.`).waitFor();

    await payloadForm.getByLabel("Payload role").selectOption("TARGET_SAMPLE");
    await payloadForm.getByLabel("Payload format").selectOption("JSON");
    await payloadForm.getByLabel("Payload file name").fill(`external_delivery_negative_${suffix}.json`);
    await payloadForm.getByLabel("Payload description").fill("Synthetic negative browser target payload.");
    await payloadForm.getByLabel("Payload content").fill('{"header":{"shipmentId":"","accessKey":""}}');
    await page.getByRole("button", { name: "Create payload and schema" }).click();
    await page.getByText(`Payload external_delivery_negative_${suffix}.json and schema $ created.`).waitFor();

    await page.locator(".integration-workflow-step").filter({ hasText: "Mapping rules" }).click();
    await page.getByLabel("Join binding source schema").selectOption({ label: "Transmission" });
    await page.getByLabel("Join binding name").fill("Negative stop to release binding");
    await joinBindingSelects.nth(1).selectOption("/Transmission/Shipment/ShipmentStop");
    await joinBindingSelects.nth(2).selectOption("/Transmission/Shipment/Release");
    await joinBindingSelects.nth(3).selectOption("/Transmission/Shipment/ShipmentStop");
    await page.getByLabel("Hop 1 left value path").fill("ShipmentStopDetail/ShipUnitGid/Gid/Xid");
    await joinBindingSelects.nth(4).selectOption("/Transmission/Shipment/ShipUnit");
    await page.getByLabel("Hop 1 right value path").fill("ShipUnitGid/Gid/Xid");
    await page.getByLabel("Hop 1 result alias").fill("stop_ship_unit");
    await joinBindingSelects.nth(5).selectOption("/Transmission/Shipment/ShipUnit");
    await page.getByLabel("Hop 2 left value path").fill("ShipUnitContent/ReleaseGid/Gid/Xid");
    await joinBindingSelects.nth(6).selectOption("/Transmission/Shipment/Release");
    await page.getByLabel("Hop 2 right value path").fill("ReleaseGid/Gid/Xid");
    await page.getByLabel("Hop 2 result alias").fill("ship_unit_release");
    await page.getByLabel("Join binding description").fill("Synthetic negative two-hop binding metadata.");
    await page.getByRole("button", { name: "Create join binding" }).click();
    await page.getByText("Created join binding Negative stop to release binding.").waitFor();

    await page.getByLabel("Alias source context").selectOption("ship_unit_release");
    await page.getByLabel("Mapping source node").selectOption("/Transmission/Shipment/ShipmentGid");
    await page.getByLabel("Mapping target node").selectOption("$.header.accessKey");
    await page.getByLabel("Mapping description").fill("Invalid alias mapping intentionally outside release scope.");
    await page.getByRole("button", { name: "Create mapping" }).click();
    await page.getByText("Created mapping $.header.accessKey.").waitFor();
    await page.getByRole("button", { name: "Validate definition" }).click();
    await page.getByText("Validation failed with 1 issue(s).").waitFor();
    await page
      .getByLabel("Integration mapping readiness")
      .getByText("INTEGRATION_VALIDATION_MAPPING_ALIAS_SCOPE_INVALID", { exact: true })
      .waitFor();
    await page.getByRole("button", { name: "Preview definition" }).click();
    await page.getByText("Integration Mapping definition must pass validation before preview.").waitFor();
    if (await page.getByText(/^Preview artifact .+ generated by job .+\.$/).isVisible().catch(() => false)) {
      throw new Error("Blocked negative Integration Mapping preview displayed a stale success message.");
    }

    await page.getByRole("button", { name: "Remove mapping $.header.accessKey" }).click();
    await page.getByText("Removed mapping $.header.accessKey.").waitFor();
    await page.getByLabel("Alias source context").selectOption("ship_unit_release");
    await page.getByLabel("Mapping source node").selectOption("/Transmission/Shipment/Release/ReleaseRefnum/ReleaseRefnumValue");
    await page.getByLabel("Mapping target node").selectOption("$.header.accessKey");
    await page.getByLabel("Mapping description").fill("Corrected alias mapping inside release scope.");
    await page.getByRole("button", { name: "Create mapping" }).click();
    await page.getByText("Created mapping $.header.accessKey.").waitFor();
    await page.getByRole("button", { name: "Validate definition" }).click();
    await page.getByText("Validation passed with 0 issue(s).").waitFor();
    await page.getByRole("button", { name: "Preview definition" }).click();
    await page.getByText(/^Preview artifact .+ generated by job .+\.$/).waitFor();

    await page.locator(".integration-workflow-step").filter({ hasText: "Definitions list" }).click();
    await page.getByLabel("Integration mapping definitions").getByRole("button", { name: new RegExp(scenarioDefinitionCode) }).click();
    await page.getByLabel("Selected integration mapping definition").getByText(scenarioDefinitionCode, { exact: true }).waitFor();
    await page.locator(".integration-workflow-step").filter({ hasText: "Payloads & schemas" }).click();
    await payloadForm.getByLabel("Payload role").selectOption("SOURCE_SAMPLE");
    await payloadForm.getByLabel("Payload format").selectOption("XML");
    await payloadForm.getByLabel("Payload file name").fill(`planned_shipment_required_${suffix}.xml`);
    await payloadForm.getByLabel("Payload description").fill("Synthetic required target source payload.");
    await payloadForm
      .getByLabel("Payload content")
      .fill(
        [
          "<Transmission><Shipment><ShipmentGid>DEMO.SHIPMENT_REQUIRED</ShipmentGid>",
          "<StartDt><PlannedTime><GLogDate>20260525103000</GLogDate></PlannedTime></StartDt>",
          "<ShipmentStop><StopSequence>1</StopSequence></ShipmentStop>",
          "<Release><ReleaseRefnum><ReleaseRefnumValue>DOC-001</ReleaseRefnumValue></ReleaseRefnum></Release>",
          "</Shipment></Transmission>"
        ].join("")
      );
    await page.getByRole("button", { name: "Create payload and schema" }).click();
    await page.getByText(`Payload planned_shipment_required_${suffix}.xml and schema Transmission created.`).waitFor();

    await payloadForm.getByLabel("Payload role").selectOption("TARGET_SAMPLE");
    await payloadForm.getByLabel("Payload format").selectOption("JSON");
    await payloadForm.getByLabel("Payload file name").fill(`external_delivery_required_${suffix}.json`);
    await payloadForm.getByLabel("Payload description").fill("Synthetic required target payload.");
    await payloadForm
      .getByLabel("Payload content")
      .fill('{"NumeroViagem":"","DataEmissao":"","Entregas":[{"NumeroDocumento":"","ChaveAcesso":""}]}');
    await page.getByRole("button", { name: "Create payload and schema" }).click();
    await page.getByText(`Payload external_delivery_required_${suffix}.json and schema $ created.`).waitFor();

    await page.locator(".integration-workflow-step").filter({ hasText: "Mapping rules" }).click();
    await page.getByLabel("Mapping source node").selectOption("/Transmission/Shipment/ShipmentGid");
    await page.getByLabel("Mapping target node").selectOption("$.NumeroViagem");
    await page.getByLabel("Mapping description").fill("Required scenario trip number mapping.");
    await page.getByRole("button", { name: "Create mapping" }).click();
    await page.getByText("Created mapping $.NumeroViagem.").waitFor();
    await page.getByRole("button", { name: "Validate definition" }).click();
    await page.getByText("Validation failed with 4 issue(s).").waitFor();
    await page
      .getByLabel("Integration mapping required target checklist")
      .getByText("$.DataEmissao", { exact: true })
      .waitFor();
    await page
      .getByLabel("Integration mapping required target checklist")
      .getByText("$.Entregas[].ChaveAcesso", { exact: true })
      .waitFor();

    await page.getByLabel("Loop source schema").selectOption({ label: "Transmission" });
    await page.getByLabel("Loop target schema").selectOption({ label: "$" });
    await page.getByLabel("Loop name").fill("Required deliveries loop");
    await page.getByLabel("Loop source node").selectOption("/Transmission/Shipment/ShipmentStop");
    await page.getByLabel("Loop target node").selectOption("$.Entregas[]");
    await page.getByLabel("Loop description").fill("Required target deliveries loop.");
    await page.getByRole("button", { name: "Create loop" }).click();
    await page.getByText("Created loop Required deliveries loop.").waitFor();

    await page.getByLabel("Mapping source node").selectOption("/Transmission/Shipment/StartDt/PlannedTime/GLogDate");
    await page.getByLabel("Mapping target node").selectOption("$.DataEmissao");
    await page.getByLabel("Mapping description").fill("Required scenario issue date mapping.");
    await page.getByRole("button", { name: "Create mapping" }).click();
    await page.getByText("Created mapping $.DataEmissao.").waitFor();

    await page.getByLabel("Mapping source node").selectOption("/Transmission/Shipment/Release/ReleaseRefnum/ReleaseRefnumValue");
    await page.getByLabel("Mapping target node").selectOption("$.Entregas[].NumeroDocumento");
    await page.getByLabel("Mapping description").fill("Required scenario document number mapping.");
    await page.getByRole("button", { name: "Create mapping" }).click();
    await page.getByText("Created mapping $.Entregas[].NumeroDocumento.").waitFor();

    await page.getByLabel("Mapping source node").selectOption("/Transmission/Shipment/Release/ReleaseRefnum/ReleaseRefnumValue");
    await page.getByLabel("Mapping target node").selectOption("$.Entregas[].ChaveAcesso");
    await page.getByLabel("Mapping description").fill("Required scenario access key mapping.");
    await page.getByRole("button", { name: "Create mapping" }).click();
    await page.getByText("Created mapping $.Entregas[].ChaveAcesso.").waitFor();
    await page.getByRole("button", { name: "Validate definition" }).click();
    await page.getByText("Validation passed with 0 issue(s).").waitFor();
    const scenarioChecklist = page.getByLabel("Integration mapping required target checklist");
    await scenarioChecklist.getByText("PlannedShipment to External Delivery", { exact: true }).waitFor();
    if (await scenarioChecklist.getByText("MISSING", { exact: true }).isVisible().catch(() => false)) {
      throw new Error("Required target checklist still showed missing targets after correction.");
    }

    await page.locator('a[href="/home"]').click();
    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    await page.locator('a[href="/integration-mapping"]').click();
    await page.getByRole("heading", { name: "Integration Mapping Studio" }).waitFor();
    await page.getByText(scenarioDefinitionCode, { exact: true }).first().waitFor();

    const unexpectedConsoleErrors = consoleErrors.filter(
      (message) => !message.includes("Failed to load resource: the server responded with a status of 409")
    );
    if (unexpectedConsoleErrors.length || failedResponses.length) {
      throw new Error(
        [
          "Integration Mapping browser functional QA detected runtime failures.",
          unexpectedConsoleErrors.length ? `Console errors:\n${unexpectedConsoleErrors.join("\n")}` : "",
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
          definition_code: definitionCode,
          alternate_definition_code: alternateDefinitionCode,
          scenario_definition_code: scenarioDefinitionCode
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
