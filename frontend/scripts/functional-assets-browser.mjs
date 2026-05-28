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

async function assertControlValue(locator, expected, description) {
  const value = await locator.inputValue();
  if (value !== expected) {
    throw new Error(`${description} expected value "${expected}" but received "${value}".`);
  }
}

async function run() {
  const playwright = await loadPlaywright();
  if (!playwright) return;
  const fs = await import("node:fs/promises");
  const path = await import("node:path");
  const url = await import("node:url");

  const login = await apiRequest("/api/v1/platform/session/login", {
    method: "POST",
    body: { email, password }
  });
  const token = login.access_token;
  const navigation = await apiRequest("/api/v1/platform/navigation", { token });
  const navigationIds = (navigation.items ?? []).map((item) => item.id);
  const excludedNavigationIds = ["catalog", "evidence", "admin", "dev_tools", "coordinate_quality"];
  const staleNavigationIds = navigationIds.filter((id) => excludedNavigationIds.includes(id));
  if (staleNavigationIds.length) {
    throw new Error(`Stale navigation contract exposed excluded modules: ${staleNavigationIds.join(", ")}.`);
  }
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
  await apiRequest("/api/v1/platform/active-context", {
    method: "POST",
    token,
    body: {
      project_id: context.project.id,
      profile_id: context.profile.id,
      environment_id: context.environment.id,
      domain_name: "OTM1"
    }
  });
  const referenceAsset = await apiRequest("/api/v1/modules/assets/assets", {
    method: "POST",
    token,
    body: {
      name: `Synthetic Reference Template ${Date.now()}`,
      description: "Client-safe selected reference asset.",
      asset_type: "SPEC",
      category: "INTEGRATION",
      visibility: "PROJECT",
      scope_type: "MODULE",
      sensitivity: "INTERNAL",
      module_id: "master_data",
      macro_object_code: "LOCATION",
      otm_table_name: "LOCATION",
      tags: ["REFERENCE", "SYNTHETIC"]
    }
  });
  let evidenceIndex = await apiRequest("/api/v1/evidence-hub/evidence", { token });
  let evidenceTarget = evidenceIndex.items?.find((item) => item.artifact);
  if (!evidenceTarget?.artifact) {
    const artifactPath = url.fileURLToPath(new URL("../../var/artifacts/browser-qa/assets-link-target.md", import.meta.url));
    await fs.mkdir(path.dirname(artifactPath), { recursive: true });
    await fs.writeFile(artifactPath, "# synthetic assets browser QA target\n", "utf-8");
    const artifact = await apiRequest("/api/v1/platform/artifacts", {
      method: "POST",
      token,
      body: {
        source_module: "integration_mapping",
        artifact_type: "integration_markdown_spec",
        file_path: artifactPath,
        file_name: "assets-link-target.md",
        content_type: "text/markdown",
        sensitivity_level: "client_safe",
        project_id: context.project.id,
        profile_id: context.profile.id,
        environment_id: context.environment.id,
        domain_name: "OTM1",
        visibility: "PROJECT"
      }
    });
    const manifest = await apiRequest("/api/v1/platform/manifests", {
      method: "POST",
      token,
      body: {
        source_module: "integration_mapping",
        manifest_json: "{\"status\":\"synthetic-browser-qa\"}",
        status: "CREATED",
        project_id: context.project.id,
        profile_id: context.profile.id,
        environment_id: context.environment.id,
        domain_name: "OTM1",
        visibility: "PROJECT"
      }
    });
    await apiRequest("/api/v1/platform/evidence", {
      method: "POST",
      token,
      body: {
        source_module: "integration_mapping",
        evidence_type: "integration_mapping_spec",
        summary_json: "{\"status\":\"synthetic-browser-qa\"}",
        artifact_id: artifact.id,
        manifest_id: manifest.id
      }
    });
    evidenceIndex = await apiRequest(`/api/v1/evidence-hub/evidence?artifact_id=${artifact.id}`, { token });
    evidenceTarget = evidenceIndex.items?.find((item) => item.artifact);
  }
  if (!evidenceTarget?.artifact) {
    throw new Error("Assets browser functional QA requires at least one client-safe evidence item with an artifact.");
  }

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
    await page.getByText("Context updated.").waitFor();

    await page.locator('a[href="/assets"]').first().click();
    await page.getByRole("heading", { name: "Assets Library" }).waitFor();
    await page.getByRole("link", { name: "Open library" }).click();
    await page.getByLabel("Assets Library workflow").waitFor();
    const classificationCode = `PLAYBOOK_${Date.now()}`;
    await page.goto(`${baseUrl}/assets/classifications`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Asset classifications" }).waitFor();
    await page.getByText("asset_category").waitFor();
    const classificationsScreenshotPath = url.fileURLToPath(new URL("../../var/qa/assets-classifications-route.png", import.meta.url));
    await fs.mkdir(path.dirname(classificationsScreenshotPath), { recursive: true });
    await page.screenshot({ fullPage: true, path: classificationsScreenshotPath });
    await page.getByRole("link", { name: "Create classification" }).click();
    await page.getByRole("heading", { name: "Create asset classification" }).waitFor();
    await page.getByLabel("Asset classification type").selectOption("asset_category");
    await page.getByLabel("Asset classification code").fill(classificationCode);
    await page.getByLabel("Asset classification name").fill("Playbook QA");
    await page.getByLabel("Asset classification description").fill("Client-safe browser QA classification.");
    await page.getByLabel("Asset classification sort order").fill("95");
    await page.getByRole("button", { name: "Create classification" }).click();
    await page.getByText(`Classification ${classificationCode} created.`).waitFor();
    const classificationCreateScreenshotPath = url.fileURLToPath(
      new URL("../../var/qa/assets-classification-create-route.png", import.meta.url)
    );
    await fs.mkdir(path.dirname(classificationCreateScreenshotPath), { recursive: true });
    await page.screenshot({ fullPage: true, path: classificationCreateScreenshotPath });
    const classificationIndex = await apiRequest("/api/v1/modules/assets/classifications", { token });
    const createdClassification = (classificationIndex.items ?? [])
      .flatMap((group) => group.items ?? [])
      .find((classification) => classification.code === classificationCode);
    if (!createdClassification) {
      throw new Error("Created classification was not available for direct edit-route QA.");
    }
    await page.goto(`${baseUrl}/assets/classifications/${createdClassification.id}/edit`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Edit Playbook QA" }).waitFor();
    await page.getByLabel("Asset classification name").fill("Playbook QA Updated");
    await page.getByLabel("Asset classification description").fill("Updated client-safe browser QA classification.");
    await page.getByRole("button", { name: "Save classification" }).click();
    await page.getByText(`Classification ${classificationCode} saved.`).waitFor();
    const classificationEditScreenshotPath = url.fileURLToPath(
      new URL("../../var/qa/assets-classification-edit-route.png", import.meta.url)
    );
    await fs.mkdir(path.dirname(classificationEditScreenshotPath), { recursive: true });
    await page.screenshot({ fullPage: true, path: classificationEditScreenshotPath });
    await page.goto(`${baseUrl}/assets/library`, { waitUntil: "domcontentloaded" });
    await page.getByLabel("Assets Library workflow").waitFor();
    await page.getByLabel("Asset name search").fill("Rate Table");
    await page.getByLabel("Asset name operator").selectOption("contains");
    await page.getByLabel("Asset description search").fill("support asset");
    await page.getByLabel("Asset description operator").selectOption("contains");
    await page.getByLabel("Asset type filter").selectOption("SPEC");
    await page.getByLabel("Asset category filter").selectOption("INTEGRATION");
    await page.getByLabel("Asset status filter").selectOption("DRAFT");
    await page.getByLabel("Asset tag filter").fill("MVP0");
    await page.getByLabel("Asset scope filter").selectOption("MODULE");
    await page.getByLabel("Asset module filter").fill("rates");
    await page.getByLabel("Asset module operator").selectOption("one_of");
    await page.getByLabel("Asset macro object filter").fill("RATE_GEO");
    await page.getByLabel("Asset macro object operator").selectOption("begins_with");
    await page.getByLabel("Asset OTM table filter").fill("RATE_GEO_COST");
    await page.getByLabel("Asset OTM table operator").selectOption("one_of");
    await page.getByLabel("Asset target OTM version filter").fill("26A");
    await page.getByLabel("Asset target OTM version operator").selectOption("one_of");
    await page.getByLabel("Asset linked target type filter").selectOption("MODULE");
    await page.getByLabel("Asset linked target type operator").selectOption("one_of");
    await page.getByLabel("Asset page size").selectOption("25");
    await page.getByRole("button", { name: "Apply search" }).click();
    await page.getByText(/Showing .* assets/).waitFor();
    const librarySearchScreenshotPath = url.fileURLToPath(new URL("../../var/qa/assets-library-search.png", import.meta.url));
    await fs.mkdir(path.dirname(librarySearchScreenshotPath), { recursive: true });
    await page.screenshot({ fullPage: true, path: librarySearchScreenshotPath });
    await page.getByRole("button", { name: "Reset search" }).click();
    await assertControlValue(page.getByLabel("Asset name search"), "", "Asset name search after reset");
    await assertControlValue(page.getByLabel("Asset name operator"), "contains", "Asset name operator after reset");
    await assertControlValue(page.getByLabel("Asset description search"), "", "Asset description search after reset");
    await assertControlValue(page.getByLabel("Asset description operator"), "contains", "Asset description operator after reset");
    await assertControlValue(page.getByLabel("Asset type filter"), "", "Asset type filter after reset");
    await assertControlValue(page.getByLabel("Asset category filter"), "", "Asset category filter after reset");
    await assertControlValue(page.getByLabel("Asset status filter"), "", "Asset status filter after reset");
    await assertControlValue(page.getByLabel("Asset tag filter"), "", "Asset tag filter after reset");
    await assertControlValue(page.getByLabel("Asset scope filter"), "", "Asset scope filter after reset");
    await assertControlValue(page.getByLabel("Asset module filter"), "", "Asset module filter after reset");
    await assertControlValue(page.getByLabel("Asset module operator"), "contains", "Asset module operator after reset");
    await assertControlValue(page.getByLabel("Asset macro object filter"), "", "Asset macro object filter after reset");
    await assertControlValue(page.getByLabel("Asset macro object operator"), "contains", "Asset macro object operator after reset");
    await assertControlValue(page.getByLabel("Asset OTM table filter"), "", "Asset OTM table filter after reset");
    await assertControlValue(page.getByLabel("Asset OTM table operator"), "contains", "Asset OTM table operator after reset");
    await assertControlValue(page.getByLabel("Asset target OTM version filter"), "", "Asset target OTM version filter after reset");
    await assertControlValue(
      page.getByLabel("Asset target OTM version operator"),
      "contains",
      "Asset target OTM version operator after reset"
    );
    await assertControlValue(page.getByLabel("Asset linked target type filter"), "", "Asset linked target type filter after reset");
    await assertControlValue(page.getByLabel("Asset linked target type operator"), "one_of", "Asset linked target type operator after reset");
    await assertControlValue(page.getByLabel("Asset page size"), "50", "Asset page size after reset");

    await page.goto(`${baseUrl}/assets/new`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Create asset" }).waitFor();
    const assetCreateScreenshotPath = url.fileURLToPath(new URL("../../var/qa/assets-create-route.png", import.meta.url));
    await fs.mkdir(path.dirname(assetCreateScreenshotPath), { recursive: true });
    await page.screenshot({ fullPage: true, path: assetCreateScreenshotPath });
    await page.getByLabel("Asset name").fill("Synthetic Rate Table Notes");
    await page.getByLabel("Asset description").fill("Client-safe rate table support asset.");
    await page.getByLabel("Asset type").selectOption("SPEC");
    await page.getByLabel("Asset category").selectOption("INTEGRATION");
    await page.getByLabel("Asset visibility").selectOption("PROJECT");
    await page.getByLabel("Asset scope").selectOption("MODULE");
    await page.getByLabel("Asset sensitivity").selectOption("INTERNAL");
    await page.getByLabel("Asset module id").fill("rates");
    await page.getByLabel("Asset macro object").fill("RATE_RECORD");
    await page.getByLabel("Asset OTM table").fill("RATE_GEO_COST");
    await page.getByLabel("Asset tags").fill("SYNTHETIC,RATE");
    await page.getByRole("button", { name: "Create asset" }).click();
    await page.getByText("Asset Synthetic Rate Table Notes created.").waitFor();
    await page.goto(`${baseUrl}/assets/library`, { waitUntil: "domcontentloaded" });
    await page.getByLabel("Assets Library workflow").waitFor();
    await page.locator(".load-plan-workflow-step").filter({ hasText: "Library" }).click();
    await page.getByRole("button", { name: /Synthetic Rate Table Notes/ }).first().click();
    await page.getByLabel("Selected asset", { exact: true }).getByText("Synthetic Rate Table Notes").waitFor();

    await page.locator(".load-plan-workflow-step").filter({ hasText: "Create" }).click();
    await page.getByLabel("Asset name").fill("Synthetic Rate Table Notes Updated");
    await page.getByLabel("Asset description").fill("Updated client-safe rate table support asset.");
    await page.getByLabel("Asset tags").fill("SYNTHETIC,RATE,UPDATED");
    await page.getByRole("button", { name: "Update asset" }).click();
    await page.getByText("Asset Synthetic Rate Table Notes Updated updated.").waitFor();
    await page.getByLabel("Selected asset", { exact: true }).getByText("Synthetic Rate Table Notes Updated").waitFor();

    let assetIndex = await apiRequest("/api/v1/modules/assets/assets", { token });
    let createdRouteAsset = assetIndex.items?.find((item) => item.name === "Synthetic Rate Table Notes Updated");
    if (!createdRouteAsset) {
      throw new Error("Created asset was not available for direct edit-route QA.");
    }
    await page.goto(`${baseUrl}/assets/${createdRouteAsset.id}/edit`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Edit Synthetic Rate Table Notes Updated" }).waitFor();
    await page.getByLabel("Asset name").fill("Synthetic Rate Table Notes Direct Edited");
    await page.getByLabel("Asset description").fill("Direct route metadata update for client-safe browser QA.");
    await page.getByRole("button", { name: "Save metadata" }).click();
    await page.getByText("Asset Synthetic Rate Table Notes Direct Edited updated.").waitFor();
    await page.getByRole("link", { name: "Back to Asset" }).waitFor();
    const editScreenshotPath = url.fileURLToPath(new URL("../../var/qa/assets-edit-metadata-route.png", import.meta.url));
    await fs.mkdir(path.dirname(editScreenshotPath), { recursive: true });
    await page.screenshot({ fullPage: true, path: editScreenshotPath });
    await page.getByRole("link", { name: "Back to Library" }).click();
    await page.getByLabel("Assets Library workflow").waitFor();
    await page.locator(".load-plan-workflow-step").filter({ hasText: "Library" }).click();
    await page.getByRole("button", { name: /Synthetic Rate Table Notes Direct Edited/ }).first().click();
    await page.getByLabel("Selected asset", { exact: true }).getByText("Synthetic Rate Table Notes Direct Edited").waitFor();

    assetIndex = await apiRequest("/api/v1/modules/assets/assets", { token });
    createdRouteAsset = assetIndex.items?.find((item) => item.name === "Synthetic Rate Table Notes Direct Edited");
    if (!createdRouteAsset) {
      throw new Error("Created asset was not available for direct versions-route QA.");
    }
    await page.goto(`${baseUrl}/assets/${createdRouteAsset.id}/versions/new`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Upload version for Synthetic Rate Table Notes Direct Edited" }).waitFor();
    await page.getByLabel("Asset version file").setInputFiles({
      name: "synthetic_direct_version.md",
      mimeType: "text/markdown",
      buffer: Buffer.from("# synthetic direct version\n")
    });
    await page.getByRole("button", { name: "Upload version" }).click();
    await page.getByText("Asset version synthetic_direct_version.md uploaded.").waitFor();
    const versionUploadScreenshotPath = url.fileURLToPath(new URL("../../var/qa/assets-version-upload-route.png", import.meta.url));
    await fs.mkdir(path.dirname(versionUploadScreenshotPath), { recursive: true });
    await page.screenshot({ fullPage: true, path: versionUploadScreenshotPath });
    await page.getByRole("link", { name: "Version history" }).click();
    await page.getByRole("heading", { name: "Versions for Synthetic Rate Table Notes Direct Edited" }).waitFor();
    await page.getByLabel("Asset versions rows").getByText("synthetic_direct_version.md").waitFor();
    const versionsScreenshotPath = url.fileURLToPath(new URL("../../var/qa/assets-versions-route.png", import.meta.url));
    await fs.mkdir(path.dirname(versionsScreenshotPath), { recursive: true });
    await page.screenshot({ fullPage: true, path: versionsScreenshotPath });
    await page.getByRole("link", { name: "Back to Library" }).click();
    await page.getByLabel("Assets Library workflow").waitFor();
    await page.locator(".load-plan-workflow-step").filter({ hasText: "Library" }).click();
    await page.getByRole("button", { name: /Synthetic Rate Table Notes Direct Edited/ }).first().click();
    await page.getByLabel("Selected asset", { exact: true }).getByText("Synthetic Rate Table Notes Direct Edited").waitFor();

    assetIndex = await apiRequest("/api/v1/modules/assets/assets", { token });
    createdRouteAsset = assetIndex.items?.find((item) => item.name === "Synthetic Rate Table Notes Direct Edited");
    if (!createdRouteAsset) {
      throw new Error("Created asset was not available for direct links-route QA.");
    }
    await page.goto(`${baseUrl}/assets/${createdRouteAsset.id}/links`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Links for Synthetic Rate Table Notes Direct Edited" }).waitFor();
    await page.getByLabel("Asset link type").selectOption("MODULE");
    await page.getByLabel("Asset guided link target").selectOption("load_plan");
    await page.getByRole("button", { name: "Create link" }).click();
    await page.getByText("Asset link load_plan created.").waitFor();
    await page.getByLabel("Asset links rows").getByText("Load Plan").waitFor();
    const linksScreenshotPath = url.fileURLToPath(new URL("../../var/qa/assets-links-route.png", import.meta.url));
    await fs.mkdir(path.dirname(linksScreenshotPath), { recursive: true });
    await page.screenshot({ fullPage: true, path: linksScreenshotPath });
    await page.getByRole("link", { name: "Back to Library" }).click();
    await page.getByLabel("Assets Library workflow").waitFor();
    await page.locator(".load-plan-workflow-step").filter({ hasText: "Library" }).click();
    await page.getByRole("button", { name: /Synthetic Rate Table Notes Direct Edited/ }).first().click();
    await page.getByLabel("Selected asset", { exact: true }).getByText("Synthetic Rate Table Notes Direct Edited").waitFor();

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

    await page.locator(".load-plan-workflow-step").filter({ hasText: "Link" }).click();
    await page.getByLabel("Asset link type").selectOption("ARTIFACT");
    await page.getByLabel("Evidence target source module filter").fill(evidenceTarget.source_module);
    await page.getByLabel("Evidence target type filter").fill(evidenceTarget.evidence_type);
    await page.getByRole("button", { name: "Apply evidence target filters" }).click();
    await page.getByRole("button", { name: "Reset evidence target filters" }).click();
    await assertControlValue(
      page.getByLabel("Evidence target source module filter"),
      "",
      "Evidence target source module filter after reset"
    );
    await assertControlValue(
      page.getByLabel("Evidence target type filter"),
      "",
      "Evidence target type filter after reset"
    );
    await assertControlValue(
      page.getByLabel("Evidence target status filter"),
      "",
      "Evidence target status filter after reset"
    );
    await assertControlValue(
      page.getByLabel("Evidence target artifact id filter"),
      "",
      "Evidence target artifact id filter after reset"
    );
    await page.getByLabel("Evidence target source module filter").fill(evidenceTarget.source_module);
    await page.getByLabel("Evidence target type filter").fill(evidenceTarget.evidence_type);
    await page.getByRole("button", { name: "Apply evidence target filters" }).click();
    await page.getByLabel("Asset guided link target").selectOption(evidenceTarget.artifact.id);
    await page.getByRole("button", { name: "Create link" }).click();
    await page.getByText(`Asset link ${evidenceTarget.artifact.id} created.`).waitFor();
    await page.getByLabel("Selected asset links").getByText(evidenceTarget.artifact.file_name).waitFor();

    await page.locator(".load-plan-workflow-step").filter({ hasText: "Link" }).click();
    await page.getByLabel("Asset link type").selectOption("EVIDENCE");
    await page.getByLabel("Asset guided link target").selectOption(evidenceTarget.id);
    await page.getByRole("button", { name: "Create link" }).click();
    await page.getByText(`Asset link ${evidenceTarget.id} created.`).waitFor();
    await page.getByLabel("Selected asset links").getByText(`${evidenceTarget.evidence_type} evidence`).waitFor();

    await page.locator(".load-plan-workflow-step").filter({ hasText: "Lifecycle" }).click();
    await page.getByRole("button", { name: "Download current version" }).click();
    await page.getByText("Download started: synthetic_mapping_spec.md.").waitFor();

    assetIndex = await apiRequest("/api/v1/modules/assets/assets", { token });
    createdRouteAsset = assetIndex.items?.find((item) => item.name === "Synthetic Rate Table Notes Direct Edited");
    if (!createdRouteAsset) {
      throw new Error("Created asset was not available for direct detail action QA.");
    }
    await page.goto(`${baseUrl}/assets/${createdRouteAsset.id}`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Synthetic Rate Table Notes Direct Edited" }).waitFor();
    await page.getByRole("link", { name: "Upload version" }).waitFor();
    await page.getByRole("link", { name: "View versions" }).waitFor();
    await page.getByRole("link", { name: "Manage links" }).waitFor();
    await page.getByRole("link", { name: "Archive asset" }).waitFor();
    await page.getByRole("button", { name: "Download current version" }).click();
    await page.getByText("Download started: synthetic_mapping_spec.md.").waitFor();
    const detailActionsScreenshotPath = url.fileURLToPath(new URL("../../var/qa/assets-detail-actions-route.png", import.meta.url));
    await fs.mkdir(path.dirname(detailActionsScreenshotPath), { recursive: true });
    await page.screenshot({ fullPage: true, path: detailActionsScreenshotPath });

    assetIndex = await apiRequest("/api/v1/modules/assets/assets", { token });
    createdRouteAsset = assetIndex.items?.find((item) => item.name === "Synthetic Rate Table Notes Direct Edited");
    if (!createdRouteAsset) {
      throw new Error("Created asset was not available for direct archive-route QA.");
    }
    await page.goto(`${baseUrl}/assets/${createdRouteAsset.id}/archive`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Archive Synthetic Rate Table Notes Direct Edited" }).waitFor();
    await page.getByLabel("Asset archive impact").getByText("synthetic_mapping_spec.md").waitFor();
    const archiveScreenshotPath = url.fileURLToPath(new URL("../../var/qa/assets-archive-route.png", import.meta.url));
    await fs.mkdir(path.dirname(archiveScreenshotPath), { recursive: true });
    await page.screenshot({ fullPage: true, path: archiveScreenshotPath });
    await page.getByRole("button", { name: "Archive asset" }).click();
    await page.getByText("Asset Synthetic Rate Table Notes Direct Edited archived.").waitFor();
    await page.getByLabel("Asset archive impact rows").getByText("ARCHIVED").first().waitFor();
    assetIndex = await apiRequest("/api/v1/modules/assets/assets", { token });
    createdRouteAsset = assetIndex.items?.find((item) => item.name === "Synthetic Rate Table Notes Direct Edited");
    if (!createdRouteAsset) {
      throw new Error("Created asset was not available for direct detail-route QA.");
    }
    await page.goto(`${baseUrl}/assets/${createdRouteAsset.id}`, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Synthetic Rate Table Notes Direct Edited" }).waitFor();
    await page.getByLabel("Asset detail metadata").getByText("RATE_RECORD").waitFor();
    await page.getByLabel("Asset detail versions").getByText("synthetic_mapping_spec.md").waitFor();
    await page.getByLabel("Asset detail links").getByText("RATE_GEO_COST table").waitFor();
    await page.getByRole("link", { name: "Back to Library" }).waitFor();
    const screenshotPath = url.fileURLToPath(new URL("../../var/qa/assets-detail-route.png", import.meta.url));
    await fs.mkdir(path.dirname(screenshotPath), { recursive: true });
    await page.screenshot({ fullPage: true, path: screenshotPath });
    await page.getByRole("link", { name: "Back to Library" }).click();
    await page.getByLabel("Assets Library workflow").waitFor();
    await page.locator(".load-plan-workflow-step").filter({ hasText: "Version" }).click();
    if (await page.getByRole("button", { name: "Upload version" }).isEnabled()) {
      throw new Error("Upload version remains enabled after asset archive.");
    }
    await page.locator(".load-plan-workflow-step").filter({ hasText: "Link" }).click();
    if (await page.getByRole("button", { name: "Create link" }).isEnabled()) {
      throw new Error("Create link remains enabled after asset archive.");
    }
    await page.locator(".load-plan-workflow-step").filter({ hasText: "Library" }).click();
    await page.getByRole("button", { name: new RegExp(referenceAsset.name) }).click();
    await page.getByLabel("Selected asset", { exact: true }).getByText(referenceAsset.name).waitFor();
    if ((await page.getByText("Asset Synthetic Rate Table Notes Direct Edited archived.").count()) > 0) {
      throw new Error("Archived asset feedback remains visible after selecting another asset.");
    }
    await page.locator(".load-plan-workflow-step").filter({ hasText: "Version" }).click();
    if (await page.getByLabel("Asset version file").isDisabled()) {
      throw new Error("Asset version file remains disabled after selecting a non-archived asset.");
    }
    await page.locator(".load-plan-workflow-step").filter({ hasText: "Link" }).click();
    if (await page.getByRole("button", { name: "Create link" }).isDisabled()) {
      throw new Error("Create link remains disabled after selecting a non-archived asset.");
    }

    await page.locator('a[href="/home"]').click();
    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    await page.locator('a[href="/assets"]').first().click();
    await page.getByRole("heading", { name: "Assets Library" }).waitFor();
    await page.getByRole("link", { name: "Open library" }).click();
    await page.locator(".load-plan-workflow-step").filter({ hasText: "Library" }).click();
    await page.getByRole("button", { name: /Synthetic Rate Table Notes Direct Edited/ }).first().waitFor();

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
          journey: "assets-classifications-list-create-edit-filtered-metadata-direct-create-workflow-edit-direct-edit-direct-version-upload-history-direct-link-upload-link-download-direct-archive-switch-guards-return",
          baseUrl,
          apiBaseUrl,
          project_id: context.project.id,
          profile_id: context.profile.id,
          environment_id: context.environment.id,
          navigation_ids: navigationIds,
          reference_asset_id: referenceAsset.id,
          classifications_route_screenshot: "var/qa/assets-classifications-route.png",
          classification_create_route_screenshot: "var/qa/assets-classification-create-route.png",
          classification_edit_route_screenshot: "var/qa/assets-classification-edit-route.png",
          asset_create_route_screenshot: "var/qa/assets-create-route.png",
          detail_actions_route_screenshot: "var/qa/assets-detail-actions-route.png",
          detail_route_screenshot: "var/qa/assets-detail-route.png",
          edit_route_screenshot: "var/qa/assets-edit-metadata-route.png",
          versions_route_screenshot: "var/qa/assets-versions-route.png",
          version_upload_route_screenshot: "var/qa/assets-version-upload-route.png",
          links_route_screenshot: "var/qa/assets-links-route.png",
          archive_route_screenshot: "var/qa/assets-archive-route.png",
          downloaded_file: "synthetic_mapping_spec.md",
          linked_artifact_id: evidenceTarget.artifact.id,
          linked_evidence_id: evidenceTarget.id
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
