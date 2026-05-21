import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const contractPath = resolve(guiDocsRoot, "GUI_MODULE_OPERATIONAL_SURFACES_CONTRACT.md");

describe("GUI module operational surfaces contract", () => {
  it("keeps the contract discoverable from the GUI contract index and MVP1 plan", () => {
    const index = readFileSync(resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md"), "utf-8");
    const plan = readFileSync(resolve(guiDocsRoot, "GUI_MVP1_PLAN.md"), "utf-8");

    expect(index).toContain("GUI_MODULE_OPERATIONAL_SURFACES_CONTRACT.md");
    expect(plan).toContain("GUI_MODULE_OPERATIONAL_SURFACES_CONTRACT.md");
  });

  it("anchors operational surfaces to shared components instead of module-local widgets", () => {
    const contract = readFileSync(contractPath, "utf-8");

    for (const componentName of [
      "ModuleWorkspaceLayout",
      "SelectedObjectPanel",
      "OperationalPanel",
      "ArtifactList",
      "BlockerPanel",
      "ActivityRow",
      "StatePanel"
    ]) {
      expect(contract).toContain(componentName);
    }

    expect(contract).toContain("Do not create module-local replacements");
  });

  it("keeps backend-owned operational decisions explicit", () => {
    const contract = readFileSync(contractPath, "utf-8");

    for (const backendOwnedRule of [
      "whether artifacts exist",
      "whether an artifact can be downloaded",
      "whether evidence is client-safe",
      "job status and progress",
      "blocker codes and blocker messages",
      "permission and capability decisions"
    ]) {
      expect(contract).toContain(backendOwnedRule);
    }
  });

  it("documents required states and client-safe content rules", () => {
    const contract = readFileSync(contractPath, "utf-8");

    for (const stateName of [
      "loading",
      "empty",
      "no results",
      "error/unavailable",
      "warning",
      "success",
      "blocked",
      "disabled by permission",
      "read-only"
    ]) {
      expect(contract).toContain(stateName);
    }

    expect(contract).toContain("synthetic content only");
    expect(contract).toContain("local artifact file paths");
    expect(contract).toContain("raw XML/JSON payload bodies");
  });

  it("keeps all current backend-backed modules in the operational matrix", () => {
    const contract = readFileSync(contractPath, "utf-8");

    for (const moduleName of [
      "Rates Studio",
      "Catalog Core",
      "Load Plan",
      "Assets Library",
      "Evidence Hub",
      "Master Data",
      "Order Release Generator",
      "Integration Mapping Studio"
    ]) {
      expect(contract).toContain(moduleName);
    }
  });
});
