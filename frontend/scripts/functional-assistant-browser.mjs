/* global console, fetch, process */

const baseUrl = process.env.OTM_WORKBENCH_BASE_URL ?? "http://127.0.0.1:5205";
const apiBaseUrl = process.env.OTM_WORKBENCH_API_BASE_URL ?? "http://127.0.0.1:8045";
const email = process.env.OTM_WORKBENCH_QA_EMAIL ?? "demo@example.test";
const password = process.env.OTM_WORKBENCH_QA_PASSWORD ?? "DemoPass123!";

const expectedNavigationIds = [
  "master_data",
  "home",
  "rates",
  "load_plan",
  "assets",
  "order_release_generator",
  "integration_mapping",
  "settings"
];

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

async function seedAssistantSource(token) {
  await apiRequest("/api/v1/assistant/sources", {
    method: "POST",
    token,
    body: {
      title: "Shipment template guide",
      source_type: "WORKBENCH_DOC",
      source_uri: "workbench-doc://shipment-template.md",
      body_text: "Shipment template source for Assistant browser QA.",
      module_id: "order_release_generator",
      domain_name: "PUBLIC",
      visibility: "PUBLIC"
    }
  });
  await apiRequest("/api/v1/assistant/index/rebuild", { method: "POST", token, body: {} });
}

async function seedSyntheticContext(token) {
  const projects = await apiRequest("/api/v1/platform/projects", { token });
  let project = projects.items?.[0];
  if (!project) {
    const workspace = await apiRequest("/api/v1/platform/workspaces", {
      method: "POST",
      token,
      body: { name: "Synthetic Assistant QA Workspace" }
    });
    project = await apiRequest("/api/v1/platform/projects", {
      method: "POST",
      token,
      body: { workspace_id: workspace.id, name: "Synthetic Assistant QA Project" }
    });
  }

  const profiles = await apiRequest(`/api/v1/platform/profiles?project_id=${project.id}`, { token });
  const profile =
    profiles.items?.[0] ??
    (await apiRequest("/api/v1/platform/profiles", {
      method: "POST",
      token,
      body: { project_id: project.id, name: "Synthetic Assistant QA Profile" }
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
  const navigation = await apiRequest("/api/v1/platform/navigation", { token });
  const navigationIds = navigation.items.map((item) => item.id);
  const staleNavigation = navigationIds.some((id) => !expectedNavigationIds.includes(id));
  const missingNavigation = expectedNavigationIds.filter((id) => !navigationIds.includes(id));
  if (staleNavigation || missingNavigation.length || navigationIds.includes("assistant")) {
    throw new Error(
      [
        "Live backend navigation does not match the current UI phase.",
        `Expected: ${expectedNavigationIds.join(", ")}`,
        `Actual: ${navigationIds.join(", ")}`
      ].join("\n")
    );
  }
  const context = await seedSyntheticContext(token);
  await seedAssistantSource(token);

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
    await page.getByText("OTM1", { exact: true }).first().waitFor();
    await page.getByRole("button", { name: "Open Workbench Assistant" }).click();
    await page.getByRole("heading", { name: "Workbench Assistant" }).waitFor();
    await page.getByText("Assistant backend connected").waitFor();
    await page.getByLabel("Assistant context").getByText("Current screen").waitFor();
    await page.getByLabel("Assistant context").getByText("Project Cockpit").waitFor();
    await page.getByRole("button", { name: "Help for this screen" }).waitFor();
    await page.getByRole("button", { name: "Find template" }).click();
    await page.getByLabel("Search Workbench sources").waitFor({ state: "visible" });
    await page.getByLabel("Search Workbench sources").evaluate((input) => {
      if (!(input instanceof HTMLInputElement) || input.value !== "Project Cockpit template") {
        throw new Error("Find template quick action did not prefill the source search field.");
      }
    });
    await page.getByRole("button", { name: "Search Oracle docs" }).click();
    await page.getByLabel("Oracle docs question").evaluate((textarea) => {
      if (
        !(textarea instanceof HTMLTextAreaElement) ||
        textarea.value !== "Oracle Transportation Management Project Cockpit documentation"
      ) {
        throw new Error("Search Oracle docs quick action did not prefill the Oracle question.");
      }
    });
    await page.getByLabel("Search Workbench sources").fill("shipment template");
    await page.getByRole("button", { name: "Search sources" }).click();
    await page.getByText("Shipment template guide").first().waitFor();
    await page.getByLabel("Oracle docs question").fill("client ACME REST API post shipment endpoint");
    await page.getByLabel("Private terms").fill("ACME");
    await page.getByRole("button", { name: "Prepare Oracle lookup" }).click();
    await page.getByText("client REST API post shipment endpoint").waitFor();
    await page.getByLabel("SQL table").fill("RATE_GEO_COST");
    await page.getByLabel("SQL columns").fill("RATE_GEO_COST_GROUP_GID, RATE_GEO_COST_SEQ");
    await page.getByLabel("SQL filter column").fill("RATE_GEO_COST_GROUP_GID");
    await page.getByLabel("SQL purpose").fill("Find rate cost by group");
    await page.getByRole("button", { name: "Draft SQL" }).click();
    await page.getByText("SQL draft preview").waitFor();
    await page
      .getByText(
        "select rgc.RATE_GEO_COST_GROUP_GID, rgc.RATE_GEO_COST_SEQ from RATE_GEO_COST rgc where rgc.RATE_GEO_COST_GROUP_GID = :rate_geo_cost_group_gid"
      )
      .waitFor();
    await page
      .getByLabel("SQL to review")
      .fill("select rgc.RATE_GEO_COST_GROUP_GID, rgc.UNKNOWN_COL from RATE_GEO_COST rgc");
    await page.getByRole("button", { name: "Review SQL" }).click();
    await page.getByText("SQL review preview").waitFor();
    await page.getByText("RATE_GEO_COST.UNKNOWN_COL was not found.").waitFor();
    await page.screenshot({ path: "../var/qa/workbench-assistant-shell.png", fullPage: true });

    if (consoleErrors.length || failedResponses.length) {
      throw new Error(
        [
          "Assistant browser QA detected runtime failures.",
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
          journey: "workbench-assistant-shell",
          baseUrl,
          apiBaseUrl,
          navigationIds,
          screenshot: "var/qa/workbench-assistant-shell.png"
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
