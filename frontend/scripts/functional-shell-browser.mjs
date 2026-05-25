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
    await page.getByLabel("Password").fill("bad-password");
    await page.getByRole("button", { name: "Sign in" }).click();
    const loginError = page.locator(".login-form .form-error");
    await loginError.waitFor();
    await page.getByLabel("Password").fill(password);
    await loginError.waitFor({ state: "hidden" });
    consoleErrors.length = 0;
    failedResponses.length = 0;
    await page.getByRole("button", { name: "Sign in" }).click();

    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    const contextControls = page.locator(".context-switcher");
    await contextControls.locator("select").nth(0).selectOption(context.project.id);
    await contextControls.locator("select").nth(1).selectOption(context.profile.id);
    await contextControls.locator("select").nth(2).selectOption(context.environment.id);
    await contextControls.locator("input").fill("otm1");
    await page.getByRole("button", { name: "Apply context" }).click();

    await page.getByText("Project context ready").waitFor();
    await page.getByText("Context updated.").waitFor();
    await page.getByText("OTM1").waitFor();
    await contextControls.locator("input").fill("otm2");
    await page.getByText("Context updated.").waitFor({ state: "hidden" });
    await contextControls.locator("input").fill("otm1");
    await page.getByRole("button", { name: "Apply context" }).click();
    await page.getByText("Context updated.").waitFor();
    await page.getByText("OTM1").waitFor();

    await page.locator('a[href="/rates"]').click();
    await page.getByRole("heading", { name: "Rates Studio" }).waitFor();
    await page.locator('a[href="/home"]').click();
    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();

    await page.getByRole("button", { name: "Use compact density" }).click();
    await page.locator('.app-shell[data-density="compact"]').waitFor();
    await page.getByRole("button", { name: "Collapse sidebar" }).click();
    await page.locator('.app-shell[data-density="compact"][data-sidebar="collapsed"]').waitFor();

    if (consoleErrors.length || failedResponses.length) {
      throw new Error(
        [
          "Browser functional QA detected runtime failures.",
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
          journey: "shell-context-preferences-navigation",
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
