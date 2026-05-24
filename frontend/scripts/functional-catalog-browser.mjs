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
    await page.getByLabel("Catalog macro objects").getByRole("button", { name: /RATE_RECORD/ }).click();
    await page
      .getByLabel("Selected catalog macro object")
      .locator(".detail-stack > div")
      .first()
      .getByText("RATE_RECORD")
      .waitFor();
    await page.getByLabel("Selected macro object tables").getByText("RATE_GEO_COST", { exact: true }).waitFor();
    await page.getByLabel("Selected macro object load plan").getByText("RATE_OFFERING", { exact: true }).waitFor();

    await page.getByLabel("Table name").fill("SHIPMENT");
    await page.getByLabel("Usage").selectOption("cutover");
    await page.getByRole("button", { name: "Validate table" }).click();
    await page.getByText("Table validation: ERROR").waitFor();
    await page.getByText(/transactional/i).waitFor();

    await page.getByLabel("Column table").fill("RATE_GEO_COST");
    await page.getByLabel("Column name").fill("RATE_GEO_COST_GROUP_GID");
    await page.getByRole("button", { name: "Validate column" }).click();
    await page.getByText("Column validation: INFO").waitFor();
    await page.getByText(/Column exists/i).waitFor();

    await page.getByLabel("Reference value").fill("OTM2.BRL");
    await page.getByRole("button", { name: "Validate reference" }).click();
    await page.getByText("Reference validation: ERROR").waitFor();
    await page.getByText(/outside|not found|does not exist|not allowed/i).waitFor();

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
          journey: "catalog-macro-load-plan-table-column-reference-validation",
          baseUrl,
          apiBaseUrl,
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
