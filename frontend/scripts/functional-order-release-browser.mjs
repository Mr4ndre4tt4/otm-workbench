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

    await page.getByRole("button", { name: /2Batch/ }).click();
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

    await page.getByRole("button", { name: /5Submit/ }).click();
    await page.getByRole("button", { name: "Verify OTM submit guard" }).click();
    await page.getByText("Direct OTM submission is disabled in MVP0.").waitFor();
    await page.getByLabel("OTM submit guard").getByText("order_release_generator.submit_otm").waitFor();

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
          baseUrl,
          apiBaseUrl,
          project_id: context.project.id,
          profile_id: context.profile.id,
          environment_id: context.environment.id,
          batch_id: batchId
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
