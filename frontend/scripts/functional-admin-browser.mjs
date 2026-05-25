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

async function createDemoJobAndReadId(page) {
  await page.getByRole("button", { name: "Create demo job" }).click();
  const creationMessage = page.getByText(/^Created job .+\.$/);
  await creationMessage.waitFor();
  const messageText = (await creationMessage.textContent()) ?? "";
  const match = /^Created job (.+)\.$/.exec(messageText);
  if (!match) {
    throw new Error(`Could not read created job id from message: ${messageText}`);
  }
  const jobId = match[1];
  await page.getByLabel("Platform jobs").getByText(jobId, { exact: true }).first().waitFor();
  return jobId;
}

async function createSetupEntitiesFromUi(page) {
  const suffix = Date.now().toString(36);
  const names = {
    workspace: `Synthetic UI Workspace ${suffix}`,
    project: `Synthetic UI Project ${suffix}`,
    profile: `Synthetic UI Profile ${suffix}`,
    environment: `Synthetic UI DEV ${suffix}`
  };
  const setupPanel = page.getByLabel("Setup authoring");

  await page.getByLabel("Workspace name").fill(names.workspace);
  await page.getByRole("button", { name: "Create workspace" }).click();
  await page.getByText(`Created workspace ${names.workspace}.`).waitFor();
  await setupPanel.getByText(names.workspace, { exact: true }).first().waitFor();

  await page.getByLabel("Project workspace").selectOption({ label: names.workspace });
  await page.getByLabel("Project name").fill(names.project);
  await page.getByRole("button", { name: "Create project" }).click();
  await page.getByText(`Created project ${names.project}.`).waitFor();
  await setupPanel.getByText(names.project, { exact: true }).first().waitFor();

  await page.getByLabel("Profile project").selectOption({ label: names.project });
  await page.getByLabel("Profile name").fill(names.profile);
  await page.getByRole("button", { name: "Create profile" }).click();
  await page.getByText(`Created profile ${names.profile}.`).waitFor();
  await setupPanel.getByText(names.profile, { exact: true }).first().waitFor();

  await page.getByLabel("Environment project").selectOption({ label: names.project });
  await page.getByLabel("Environment type").selectOption("DEV");
  await page.getByLabel("Environment name").fill(names.environment);
  await page.getByRole("button", { name: "Create environment" }).click();
  await page.getByText(`Created environment ${names.environment}.`).waitFor();
  await setupPanel.getByText(names.environment, { exact: true }).first().waitFor();

  await page.getByLabel("Workspace name").fill(`Temporary workspace draft ${suffix}`);
  await page.getByLabel("Project workspace").selectOption({ label: names.workspace });
  await page.getByLabel("Project name").fill(`Temporary project draft ${suffix}`);
  await page.getByLabel("Profile project").selectOption({ label: names.project });
  await page.getByLabel("Profile name").fill(`Temporary profile draft ${suffix}`);
  await page.getByLabel("Environment project").selectOption({ label: names.project });
  await page.getByLabel("Environment type").selectOption("UAT");
  await page.getByLabel("Environment name").fill(`Temporary UAT draft ${suffix}`);
  await page.getByRole("button", { name: "Reset setup drafts" }).click();
  await page.getByLabel("Workspace name").evaluate((element) => {
    if (element.value !== "") throw new Error(`Workspace draft was not reset: ${element.value}`);
  });
  await page.getByLabel("Project name").evaluate((element) => {
    if (element.value !== "") throw new Error(`Project draft was not reset: ${element.value}`);
  });
  await page.getByLabel("Profile name").evaluate((element) => {
    if (element.value !== "") throw new Error(`Profile draft was not reset: ${element.value}`);
  });
  await page.getByLabel("Environment type").evaluate((element) => {
    if (element.value !== "DEV") throw new Error(`Environment type was not reset to DEV: ${element.value}`);
  });
  await page.getByLabel("Environment name").evaluate((element) => {
    if (element.value !== "") throw new Error(`Environment draft was not reset: ${element.value}`);
  });
  if (await page.getByText(`Created environment ${names.environment}.`).isVisible().catch(() => false)) {
    throw new Error("Setup success feedback stayed visible after reset.");
  }

  return names;
}

async function run() {
  const playwright = await loadPlaywright();
  if (!playwright) return;

  const login = await apiRequest("/api/v1/platform/session/login", {
    method: "POST",
    body: { email, password }
  });
  const token = login.access_token;
  await apiRequest("/api/v1/platform/feature-flags", {
    method: "POST",
    token,
    body: { name: "dev_tools", enabled: false, scope: "global" }
  });
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

    await page.locator('a[href="/admin"]').click();
    await page.getByRole("heading", { name: "Admin Console" }).waitFor();
    await page.getByText(email).waitFor();
    const authoredSetup = await createSetupEntitiesFromUi(page);
    await page.getByLabel("Project setup status").waitFor();
    await page.getByLabel("Effective capabilities").getByText("*", { exact: true }).waitFor();
    await page.getByLabel("Feature flags").getByText("dev_tools", { exact: true }).waitFor();
    await page.getByLabel("Feature flags").getByText("DISABLED", { exact: true }).waitFor();
    await page.getByRole("button", { name: "Enable feature flag dev_tools" }).click();
    await page.getByText("dev_tools enabled.").waitFor();
    await page.getByLabel("Feature flags").getByText("ENABLED", { exact: true }).waitFor();
    await page.getByLabel("Platform jobs").waitFor();
    await page.getByLabel("Audit trail").waitFor();

    const cancelledJobId = await createDemoJobAndReadId(page);
    await page.getByLabel("Selected job events").getByText("JOB_CREATED", { exact: true }).first().waitFor();
    await page.getByRole("button", { name: `Cancel job ${cancelledJobId}` }).click();
    await page.getByText("Job cancelled.").first().waitFor();
    await page.getByLabel("Selected job events").getByText("JOB_CANCELLED", { exact: true }).first().waitFor();
    await page.getByLabel("Platform jobs").getByText("CANCELLED", { exact: true }).first().waitFor();

    const jobId = await createDemoJobAndReadId(page);
    await page.getByRole("button", { name: `Run job ${jobId}` }).click();
    await page.getByText("Demo job completed.").first().waitFor();
    await page.getByLabel("Selected job events").getByText("JOB_SUCCEEDED", { exact: true }).first().waitFor();
    await page.getByLabel("Platform jobs").getByText("SUCCEEDED", { exact: true }).first().waitFor();
    await page.getByLabel("Audit trail").getByText("job.create").first().waitFor();
    await page.getByRole("button", { name: `View events ${cancelledJobId}` }).click();
    const successFeedback = page.locator(".form-success");
    if ((await successFeedback.count()) > 0) {
      const feedbackText = (await successFeedback.first().textContent()) ?? "";
      if (feedbackText.includes("Demo job completed.")) {
        throw new Error("Job completion feedback stayed visible after selecting another job.");
      }
    }
    await page.getByLabel("Selected job events").getByText("JOB_CANCELLED", { exact: true }).first().waitFor();

    await page.locator('a[href="/home"]').click();
    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    await page.locator('a[href="/admin"]').click();
    await page.getByRole("heading", { name: "Admin Console" }).waitFor();
    await page.getByLabel("Platform jobs").getByText(jobId, { exact: true }).first().waitFor();
    await page.getByLabel("Platform jobs").getByText("SUCCEEDED", { exact: true }).first().waitFor();

    if (consoleErrors.length || failedResponses.length) {
      throw new Error(
        [
          "Admin browser functional QA detected runtime failures.",
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
          journey: "admin-setup-capabilities-jobs-audit-create-run-switch-return",
          baseUrl,
          apiBaseUrl,
          project_id: context.project.id,
          profile_id: context.profile.id,
          environment_id: context.environment.id,
          authored_setup: authoredSetup,
          feature_flag: "dev_tools",
          cancelled_job_id: cancelledJobId,
          job_id: jobId
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
