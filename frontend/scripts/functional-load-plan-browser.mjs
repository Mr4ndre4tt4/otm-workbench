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

  await apiRequest("/api/v1/platform/active-context", {
    method: "POST",
    token,
    body: {
      project_id: project.id,
      profile_id: profile.id,
      environment_id: environment.id,
      domain_name: "otm1",
      can_view_all_domains: false
    }
  });

  return { project, profile, environment };
}

async function seedLoadPlanPackage(token, suffix) {
  const xid = `LP_QA_${suffix}`;
  const batch = await apiRequest("/api/v1/modules/rates/batches", {
    method: "POST",
    token,
    body: {
      scenario_code: "ACCESSORIAL_ONLY",
      name: `Synthetic Load Plan browser batch ${suffix}`,
      domain_name: "OTM1"
    }
  });
  await apiRequest(`/api/v1/modules/rates/batches/${batch.id}/tables`, {
    method: "POST",
    token,
    body: {
      tables: [
        {
          table_name: "ACCESSORIAL_COST",
          rows: [
            {
              ACCESSORIAL_COST_GID: `OTM1.${xid}`,
              ACCESSORIAL_COST_XID: xid
            }
          ]
        }
      ]
    }
  });
  await apiRequest(`/api/v1/modules/rates/batches/${batch.id}/csv-preview`, { method: "POST", token });
  await apiRequest(`/api/v1/modules/rates/batches/${batch.id}/export-csv`, { method: "POST", token });
  await apiRequest(`/api/v1/modules/rates/batches/${batch.id}/approve`, {
    method: "POST",
    token,
    body: { approval_note: "Reviewed for synthetic Load Plan browser QA." }
  });
  const loadPlanPackage = await apiRequest(`/api/v1/modules/load-plan/packages/from-rates/${batch.id}`, {
    method: "POST",
    token
  });
  const evidence = await apiRequest("/api/v1/platform/evidence", {
    method: "POST",
    token,
    body: {
      source_module: "load_plan",
      evidence_type: "cutover_table_readiness",
      summary_json: JSON.stringify({
        source_entity_type: "browser_qa",
        package_id: loadPlanPackage.id,
        table_name: "ACCESSORIAL_COST"
      })
    }
  });
  return { batch, evidence, package: loadPlanPackage };
}

function syntheticSuffix() {
  return Date.now().toString(36).toUpperCase();
}

async function waitForCsvutilBuildResult(page) {
  try {
    await page.getByText(/^CSVUTIL build .* is BUILT\.$/).waitFor({ timeout: 10000 });
    return;
  } catch (error) {
    const visibleText = await page.locator("body").innerText().catch(() => "");
    const csvutilLines = visibleText
      .split("\n")
      .filter((line) => /CSVUTIL|eligible|evidence|required|failed|error|build/i.test(line))
      .join("\n");
    throw new Error(
      [
        "CSVUTIL build success message did not appear.",
        csvutilLines ? `Visible diagnostic lines:\n${csvutilLines}` : "",
        error instanceof Error ? `Original wait error: ${error.message}` : ""
      ]
        .filter(Boolean)
        .join("\n")
    );
  }
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
  const seeded = await seedLoadPlanPackage(token, suffix);

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
    await page.locator('a[href="/load-plan"]').click();
    await page.getByRole("heading", { name: "Load Plan" }).waitFor();
    await page.getByLabel("Load Plan workflow").waitFor();
    await page.getByLabel("Load plan packages").getByText("rates_csv_zip").first().waitFor();

    await page.locator(".load-plan-workflow-step").filter({ hasText: "Checklist" }).click();
    await page.getByRole("button", { name: "Create checklist" }).click();
    await page.getByText("Checklist MVP0_STANDARD_CUTOVER created for selected package.").waitFor();
    const checklistPanel = page.getByLabel("Cutover checklist review queue");
    await checklistPanel.getByText("ACCESSORIAL_COST").waitFor();

    await page.getByLabel("Evidence id").fill(seeded.evidence.id);
    await checklistPanel.getByRole("button", { name: "Mark CSVUTIL ready" }).first().click();
    await page.getByText("Checklist item updated.").waitFor();

    await page.locator(".load-plan-workflow-step").filter({ hasText: "Readiness" }).click();
    await page.getByRole("button", { name: "Generate readiness" }).click();
    await page.getByText(/^Checklist readiness is (READY|BLOCKED|NEEDS_REVIEW)\.$/).waitFor();
    await page.getByLabel("Cutover readiness summary").waitFor();

    await page.locator(".load-plan-workflow-step").filter({ hasText: "CSVUTIL" }).click();
    await page.getByRole("button", { name: "Build CSVUTIL" }).click();
    await waitForCsvutilBuildResult(page);
    const csvutilPanel = page.getByLabel("CSVUTIL build artifacts");
    await csvutilPanel.getByText("CTL artifact").waitFor();
    await csvutilPanel.getByText("CL artifact").waitFor();
    await csvutilPanel.getByText("Manifest").waitFor();
    await csvutilPanel.getByText("Evidence").waitFor();

    await page.locator(".load-plan-workflow-step").filter({ hasText: "Handoff" }).click();
    await page.getByLabel("Cutover handoff eligibility", { exact: true }).waitFor();
    await page.getByText(/READINESS_EXPORT_MISSING|CUTOVER_READINESS_MISSING/).first().waitFor();

    await page.locator('a[href="/home"]').click();
    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    await page.locator('a[href="/load-plan"]').click();
    await page.getByRole("heading", { name: "Load Plan" }).waitFor();
    await page.getByLabel("Load plan packages").getByText("rates_csv_zip").first().waitFor();

    if (consoleErrors.length || failedResponses.length) {
      throw new Error(
        [
          "Load Plan browser functional QA detected runtime failures.",
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
          journey: "load-plan-cutover-checklist-readiness-csvutil-return",
          baseUrl,
          apiBaseUrl,
          project_id: context.project.id,
          profile_id: context.profile.id,
          environment_id: context.environment.id,
          package_id: seeded.package.id,
          batch_id: seeded.batch.id,
          evidence_id: seeded.evidence.id
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
