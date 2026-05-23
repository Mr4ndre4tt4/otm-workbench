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
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
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

    await page.locator('a[href="/assets"]').click();
    await page.getByRole("heading", { name: "Assets Library" }).waitFor();
    await page.getByLabel("Assets Library workflow").waitFor();
    await page.getByLabel("Asset type filter").selectOption("SPEC");
    await page.getByLabel("Asset category filter").selectOption("INTEGRATION");
    await page.getByLabel("Asset status filter").selectOption("DRAFT");
    await page.getByLabel("Asset tag filter").fill("MVP0");
    await page.getByLabel("Asset scope filter").selectOption("MODULE");
    await page.getByLabel("Asset module filter").fill("rates");
    await page.getByLabel("Asset macro object filter").fill("RATE_GEO");
    await page.getByLabel("Asset OTM table filter").fill("RATE_GEO_COST");
    await page.getByRole("button", { name: "Apply asset filters" }).click();

    await page.locator(".load-plan-workflow-step").filter({ hasText: "Create" }).click();
    await page.getByLabel("Asset name").fill("Synthetic Rate Table Notes");
    await page.getByLabel("Asset description").fill("Client-safe rate table support asset.");
    await page.getByLabel("Asset type").selectOption("SPEC");
    await page.getByLabel("Asset category").selectOption("INTEGRATION");
    await page.getByLabel("Asset visibility").selectOption("PROJECT");
    await page.getByLabel("Asset scope").selectOption("MODULE");
    await page.getByLabel("Asset sensitivity").selectOption("INTERNAL");
    await page.getByLabel("Asset module id").fill("rates");
    await page.getByLabel("Asset macro object").fill("RATE_GEO");
    await page.getByLabel("Asset OTM table").fill("RATE_GEO_COST");
    await page.getByLabel("Asset tags").fill("SYNTHETIC,RATE");
    await page.getByRole("button", { name: "Create asset" }).click();
    await page.getByText("Asset Synthetic Rate Table Notes created.").waitFor();
    await page.getByLabel("Selected asset", { exact: true }).getByText("Synthetic Rate Table Notes").waitFor();

    await page.locator(".load-plan-workflow-step").filter({ hasText: "Create" }).click();
    await page.getByLabel("Asset name").fill("Synthetic Rate Table Notes Updated");
    await page.getByLabel("Asset description").fill("Updated client-safe rate table support asset.");
    await page.getByLabel("Asset tags").fill("SYNTHETIC,RATE,UPDATED");
    await page.getByRole("button", { name: "Update asset" }).click();
    await page.getByText("Asset Synthetic Rate Table Notes Updated updated.").waitFor();
    await page.getByLabel("Selected asset", { exact: true }).getByText("Synthetic Rate Table Notes Updated").waitFor();

    await page.locator(".load-plan-workflow-step").filter({ hasText: "Version" }).click();
    await page.getByLabel("Asset version file").setInputFiles({
      name: "synthetic_mapping_spec.md",
      mimeType: "text/markdown",
      buffer: Buffer.from("# synthetic mapping spec\n")
    });
    await page.getByRole("button", { name: "Upload version" }).click();
    await page.getByText("Asset version synthetic_mapping_spec.md uploaded.").waitFor();
    await page.getByLabel("Selected asset versions").getByText("synthetic_mapping_spec.md").waitFor();

    await page.locator(".load-plan-workflow-step").filter({ hasText: "Link" }).click();
    await page.getByLabel("Asset link type").selectOption("OTM_TABLE");
    await page.getByLabel("Asset link target id").fill("NOT_A_REAL_OTM_TABLE");
    await page.getByLabel("Asset link target label").fill("Invalid OTM table");
    await page.getByRole("button", { name: "Create link" }).click();
    await page.getByText("ASSET_LINK_INVALID_TABLE: OTM table not found in Data Dictionary.").waitFor();
    await page.getByLabel("Asset link target id").fill("RATE_GEO");
    await page.getByLabel("Asset guided link target").selectOption("RATE_GEO_COST");
    await page.getByRole("button", { name: "Create link" }).click();
    await page.getByText("Asset link RATE_GEO_COST created.").waitFor();
    await page.getByLabel("Selected asset links").getByText("RATE_GEO_COST table").waitFor();

    await page.locator(".load-plan-workflow-step").filter({ hasText: "Link" }).click();
    await page.getByLabel("Asset link type").selectOption("MACRO_OBJECT");
    await page.getByLabel("Asset link target id").fill("NOT_A_MACRO_OBJECT");
    await page.getByLabel("Asset link target label").fill("Invalid macro object");
    await page.getByRole("button", { name: "Create link" }).click();
    await page.getByText("ASSET_LINK_INVALID_MACRO_OBJECT: OTM macro object not found in Catalog Core.").waitFor();
    await page.getByLabel("Asset guided link target").selectOption("RATE_RECORD");
    await page.getByRole("button", { name: "Create link" }).click();
    await page.getByText("Asset link RATE_RECORD created.").waitFor();
    await page.getByLabel("Selected asset links").getByText("Rate Record macro object").waitFor();

    await page.locator(".load-plan-workflow-step").filter({ hasText: "Lifecycle" }).click();
    await page.getByRole("button", { name: "Download current version" }).click();
    await page.getByText("Download started: synthetic_mapping_spec.md.").waitFor();

    await page.getByRole("button", { name: "Archive asset" }).click();
    await page.getByText("Asset Synthetic Rate Table Notes Updated archived.").waitFor();
    await page.getByLabel("Selected asset", { exact: true }).getByText("ARCHIVED").waitFor();
    await page.locator(".load-plan-workflow-step").filter({ hasText: "Version" }).click();
    if (await page.getByRole("button", { name: "Upload version" }).isEnabled()) {
      throw new Error("Upload version remains enabled after asset archive.");
    }
    await page.locator(".load-plan-workflow-step").filter({ hasText: "Link" }).click();
    if (await page.getByRole("button", { name: "Create link" }).isEnabled()) {
      throw new Error("Create link remains enabled after asset archive.");
    }

    await page.locator('a[href="/home"]').click();
    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    await page.locator('a[href="/assets"]').click();
    await page.getByRole("heading", { name: "Assets Library" }).waitFor();
    await page.locator(".load-plan-workflow-step").filter({ hasText: "Library" }).click();
    await page.getByRole("button", { name: /Synthetic Rate Table Notes Updated/ }).first().waitFor();

    const unexpectedConsoleErrors = consoleErrors.filter(
      (message) => !message.includes("Failed to load resource: the server responded with a status of 400")
    );
    const unexpectedFailedResponses = failedResponses.filter(
      (failure) => !(failure.startsWith("400 ") && failure.includes("/api/v1/modules/assets/assets/") && failure.endsWith("/links"))
    );
    if (unexpectedConsoleErrors.length || unexpectedFailedResponses.length) {
      throw new Error(
        [
          "Assets browser functional QA detected runtime failures.",
          unexpectedConsoleErrors.length ? `Console errors:\n${unexpectedConsoleErrors.join("\n")}` : "",
          unexpectedFailedResponses.length ? `HTTP failures:\n${unexpectedFailedResponses.join("\n")}` : ""
        ]
          .filter(Boolean)
          .join("\n")
      );
    }

    console.log(
      JSON.stringify(
        {
          status: "passed",
          journey: "assets-filtered-metadata-create-edit-upload-otm-table-link-download-archive-guards-return",
          baseUrl,
          apiBaseUrl,
          project_id: context.project.id,
          profile_id: context.profile.id,
          environment_id: context.environment.id,
          downloaded_file: "synthetic_mapping_spec.md"
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
