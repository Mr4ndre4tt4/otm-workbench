import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const contractPath = resolve(guiDocsRoot, "GUI_MODULE_ACTION_SURFACES_CONTRACT.md");

describe("GUI module action surfaces contract", () => {
  it("keeps the contract discoverable from the GUI contract index and MVP1 plan", () => {
    const index = readFileSync(resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md"), "utf-8");
    const plan = readFileSync(resolve(guiDocsRoot, "GUI_MVP1_PLAN.md"), "utf-8");

    expect(index).toContain("GUI_MODULE_ACTION_SURFACES_CONTRACT.md");
    expect(plan).toContain("GUI_MODULE_ACTION_SURFACES_CONTRACT.md");
  });

  it("anchors action surfaces to shared components", () => {
    const contract = readFileSync(contractPath, "utf-8");

    for (const componentName of [
      "ActionBar",
      "Button",
      "FeedbackMessage",
      "PageHeader",
      "SelectedObjectPanel",
      "OperationalPanel",
      "ArtifactList",
      "StatePanel"
    ]) {
      expect(contract).toContain(componentName);
    }

    expect(contract).toContain("Action rendering must flow through `ActionBar`");
  });

  it("keeps backend-owned action metadata explicit", () => {
    const contract = readFileSync(contractPath, "utf-8");

    for (const backendOwnedField of [
      "action key",
      "action label",
      "method",
      "href",
      "variant",
      "icon_key",
      "disabled flag",
      "disabled reason",
      "permission",
      "requires_confirmation",
      "result_hint",
      "action ordering",
      "lifecycle and readiness gates"
    ]) {
      expect(contract).toContain(backendOwnedField);
    }
  });

  it("documents approved action slots and feedback states", () => {
    const contract = readFileSync(contractPath, "utf-8");

    for (const slotName of [
      "Page header actions",
      "Selected object actions",
      "Operational row actions",
      "Future bulk actions"
    ]) {
      expect(contract).toContain(slotName);
    }

    for (const feedbackState of [
      "running",
      "success",
      "backend error",
      "unknown error",
      "disabled by permission",
      "read-only",
      "unsupported method",
      "requires confirmation"
    ]) {
      expect(contract).toContain(feedbackState);
    }
  });

  it("keeps all current backend-backed modules in the action matrix", () => {
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

  it("keeps action examples synthetic and client-safe", () => {
    const contract = readFileSync(contractPath, "utf-8");

    expect(contract).toContain("synthetic content only");
    expect(contract).toContain("real endpoint payload bodies");
    expect(contract).toContain("local artifact file paths");
    expect(contract).toContain("raw XML/JSON payload bodies");
  });
});
