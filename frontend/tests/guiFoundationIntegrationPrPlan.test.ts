import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const planPath = resolve(guiDocsRoot, "GUI_FOUNDATION_INTEGRATION_PR_PLAN.md");

describe("GUI foundation integration PR plan", () => {
  it("keeps the integration PR plan discoverable from governance docs", () => {
    const index = readFileSync(resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md"), "utf-8");
    const consolidation = readFileSync(resolve(guiDocsRoot, "GUI_FOUNDATION_CONSOLIDATION_REVIEW.md"), "utf-8");

    expect(index).toContain("GUI_FOUNDATION_INTEGRATION_PR_PLAN.md");
    expect(consolidation).toContain("GUI_FOUNDATION_INTEGRATION_PR_PLAN.md");
  });

  it("documents review sections for the delivered GUI foundation stack", () => {
    const plan = readFileSync(planPath, "utf-8");

    for (const section of [
      "Governance and backend ownership",
      "Shell, routing, auth, context, preferences, and navigation",
      "UI kit components and CSS layers",
      "Backend-backed module screens",
      "Rates Studio action/artifact/evidence affordances",
      "Synthetic fixtures and component gallery",
      "Module consistency, operational, action, and long-label guardrails",
      "Design system/Figma handoff",
      "Visual QA fallback evidence and browser runtime boundary"
    ]) {
      expect(plan).toContain(section);
    }
  });

  it("tracks the GUI issue coverage through the current integration plan", () => {
    const plan = readFileSync(planPath, "utf-8");

    for (const issueId of [
      "OTM-55",
      "OTM-56",
      "OTM-57",
      "OTM-58",
      "OTM-60",
      "OTM-63",
      "OTM-64",
      "OTM-65",
      "OTM-66",
      "OTM-67",
      "OTM-68",
      "OTM-69",
      "OTM-70",
      "OTM-71",
      "OTM-72",
      "OTM-77",
      "OTM-78"
    ]) {
      expect(plan).toContain(issueId);
    }
  });

  it("documents validation commands and sensitive scan expectations", () => {
    const plan = readFileSync(planPath, "utf-8");

    for (const command of ["npm run lint", "npm run test", "npm run build", "git diff --check", "rg -n"]) {
      expect(plan).toContain(command);
    }

    expect(plan).toContain('target_system: "NDD"');
    expect(plan).toContain("No real client data added");
    expect(plan).toContain("OTM_RESOURCES/");
  });

  it("keeps excluded scope, browser QA boundary, fallback evidence, and handoff expectations explicit", () => {
    const plan = readFileSync(planPath, "utf-8");

    for (const text of [
      "new backend module behavior",
      "new Figma file creation",
      "browser-control transport",
      "Playwright CLI",
      "must not claim pixel-perfect visual evidence",
      "GUI_BROWSER_VISUAL_QA_OTM77.md",
      "GUI_RATES_VISUAL_QA_OTM78.md",
      "Linear should contain",
      "GitHub PR should contain"
    ]) {
      expect(plan).toContain(text);
    }
  });
});
