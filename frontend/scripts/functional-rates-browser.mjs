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

function syntheticSuffix() {
  return Date.now().toString(36).toUpperCase();
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
  const suffix = syntheticSuffix();
  const batchName = `Synthetic browser rates batch ${suffix}`;
  const alternateBatchName = `Synthetic alternate rates batch ${suffix}`;
  const rowGid = `OTM1.ACC_COST_${suffix}`;

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

    await apiRequest("/api/v1/modules/rates/batches", {
      method: "POST",
      token,
      body: {
        scenario_code: "RATE_GEO_ONLY",
        name: alternateBatchName,
        domain_name: "OTM1",
        description: "",
        source_type: "api"
      }
    });

    await page.locator('a[href="/rates"]').click();
    await page.getByRole("heading", { name: "Rates Studio" }).waitFor();
    await page.getByRole("button", { name: "Create rate batch" }).click();
    await page.getByLabel("Scenario").selectOption("ACCESSORIAL_ONLY");
    await page.getByLabel("Batch name").fill(batchName);
    await page.getByLabel("Domain").fill("OTM1");
    await page.getByRole("button", { name: "Create batch" }).click();
    await page.getByText("Rate batch created.").waitFor();
    const selectedBatchPanel = page.getByLabel("Selected rate batch");
    await selectedBatchPanel.getByText(batchName).waitFor();

    await page.getByLabel("Table").selectOption("ACCESSORIAL_COST");
    await page.getByLabel("Row GID").fill(rowGid);
    await page.getByLabel("Row value").fill("OTM1.ACC_FUEL");
    await page.getByRole("button", { name: "Add table row" }).click();
    await page.getByText("Table row staged.").waitFor();
    await page.getByLabel("Selected batch tables").getByText("ACCESSORIAL_COST").waitFor();

    await page.getByRole("button", { name: "Preview CSV" }).click();
    await page.getByText("CSV preview ready.").waitFor();
    await page.getByLabel("CSV preview output").getByText("ACCESSORIAL_COST", { exact: true }).waitFor();
    await page.getByLabel("CSV preview output").getByText(rowGid).waitFor();

    await page.getByRole("button", { name: "Export CSV" }).last().click();
    await page.getByText(/CSV export created: .*\.zip\./).waitFor();
    await page.getByLabel("Rate batch export artifacts").getByText(".zip").waitFor();

    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", { name: "Download" }).last().click();
    const download = await downloadPromise;
    if (!download.suggestedFilename().endsWith(".zip")) {
      throw new Error(`Expected ZIP download, received ${download.suggestedFilename()}`);
    }
    await page.getByText(/Download started: .*\.zip\./).waitFor();

    await page.getByLabel("Rate batches").getByRole("button", { name: new RegExp(alternateBatchName) }).click();
    await selectedBatchPanel.getByText(alternateBatchName).waitFor();
    if (await page.getByText(/Download started: .*\.zip\./).isVisible().catch(() => false)) {
      throw new Error("Rates kept stale download feedback after switching batches.");
    }
    if (await page.getByLabel("CSV preview output").isVisible().catch(() => false)) {
      throw new Error("Rates kept stale CSV preview output after switching batches.");
    }
    if (!(await selectedBatchPanel.getByRole("button", { name: "Export CSV" }).last().isDisabled())) {
      throw new Error("Rates export remained enabled after switching to a batch without preview.");
    }

    await page.getByLabel("Rate batches").getByRole("button", { name: new RegExp(batchName) }).click();
    await selectedBatchPanel.getByText(batchName).waitFor();

    await page.getByRole("button", { name: "Approve", exact: true }).click();
    await page.getByRole("heading", { name: "Confirm rate batch approval" }).waitFor();
    await page.getByLabel("Approval note").fill("Reviewed for synthetic browser QA.");
    await page.getByRole("button", { name: "Confirm approval" }).click();
    await page.getByText("Approve completed.").waitFor();
    await page.getByLabel("Rate batch evidence").getByText("rates_batch_approval").waitFor();

    await page.locator('a[href="/home"]').click();
    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    await page.locator('a[href="/rates"]').click();
    await page.getByRole("heading", { name: "Rates Studio" }).waitFor();
    await selectedBatchPanel.getByText(batchName).waitFor();
    await page.getByLabel("Selected batch tables").getByText("ACCESSORIAL_COST").waitFor();

    if (consoleErrors.length || failedResponses.length) {
      throw new Error(
        [
          "Rates browser functional QA detected runtime failures.",
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
          journey: "rates-create-stage-preview-export-download-approve",
          baseUrl,
          apiBaseUrl,
          project_id: context.project.id,
          profile_id: context.profile.id,
          environment_id: context.environment.id,
          batch_name: batchName,
          alternate_batch_name: alternateBatchName,
          downloaded_file: download.suggestedFilename()
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
