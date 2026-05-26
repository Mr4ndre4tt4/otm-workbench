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

async function waitForVisibleOrThrow(page, locator, description, context = {}) {
  const error = page.locator(".form-error");
  let winner;
  try {
    winner = await Promise.race([
      locator.waitFor({ timeout: 30000 }).then(() => "target"),
      error.waitFor({ timeout: 30000 }).then(() => "error")
    ]);
  } catch (waitError) {
    throw new Error(
      [
        `Timed out while waiting for ${description}.`,
        `URL: ${page.url()}`,
        context.failedResponses?.length ? `HTTP failures:\n${context.failedResponses.join("\n")}` : "",
        context.consoleErrors?.length ? `Console errors:\n${context.consoleErrors.join("\n")}` : "",
        `Visible text:\n${(await page.locator("body").innerText({ timeout: 5000 })).slice(0, 1200)}`,
        waitError instanceof Error ? waitError.message : String(waitError)
      ]
        .filter(Boolean)
        .join("\n")
    );
  }
  if (winner === "error") {
    throw new Error(`Visible UI error while waiting for ${description}: ${await error.textContent()}`);
  }
}

async function waitForSuccessOrThrow(page, text) {
  await waitForVisibleOrThrow(page, page.getByText(text), text);
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

    await waitForVisibleOrThrow(page, page.getByRole("heading", { name: "Project Cockpit" }), "Project Cockpit after sign in", {
      consoleErrors,
      failedResponses
    });
    await page.locator('a[href="/master-data"]').click();
    await waitForVisibleOrThrow(page, page.getByRole("heading", { name: "Master Data", exact: true }), "Master Data hub", {
      consoleErrors,
      failedResponses
    });
    await page.getByRole("link", { name: "Open Quality Tools" }).click();
    await waitForVisibleOrThrow(page, page.getByRole("heading", { name: "Quality Tools", exact: true }), "Quality Tools", {
      consoleErrors,
      failedResponses
    });

    await page.locator(".master-data-workflow-step").filter({ hasText: "Quality" }).click();
    await page.getByLabel("Coordinate Quality workflow").waitFor();

    await page.getByRole("button", { name: "Preview coordinates" }).click();
    await waitForSuccessOrThrow(page, "Coordinate Quality preview processed 2 location(s).");
    await page.getByLabel("Coordinate Quality results").getByText(/NULL_FILLED|CORRECTED|REVIEW/).first().waitFor();

    await page.getByRole("button", { name: "Create quality batch" }).click();
    await page.getByText(/^Coordinate Quality batch .+ created\.$/).waitFor();
    await page.getByLabel("Coordinate Quality batches").getByText("PROCESSED").first().waitFor();

    await page.getByRole("button", { name: "Export quality package" }).click();
    await page.getByText(/^Coordinate Quality package .+\.zip exported\.$/).waitFor();
    await page.getByLabel("Coordinate Quality export package").waitFor();

    await page.locator('a[href="/home"]').click();
    await page.getByRole("heading", { name: "Project Cockpit" }).waitFor();
    await page.locator('a[href="/master-data"]').click();
    await page.getByRole("heading", { name: "Master Data", exact: true }).waitFor();
    await page.getByRole("link", { name: "Open Quality Tools" }).click();
    await page.getByRole("heading", { name: "Quality Tools", exact: true }).waitFor();
    await page.locator(".master-data-workflow-step").filter({ hasText: "Quality" }).click();
    await page.getByLabel("Coordinate Quality batches").getByText("PROCESSED").first().waitFor();

    if (consoleErrors.length || failedResponses.length) {
      throw new Error(
        [
          "Coordinate Quality browser functional QA detected runtime failures.",
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
          journey: "master-data-coordinate-quality-preview-batch-export-route-recovery",
          baseUrl,
          apiBaseUrl
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
