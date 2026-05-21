import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const contractPath = resolve(guiDocsRoot, "GUI_LONG_LABEL_RESPONSIVE_CONTRACT.md");
const layoutsCssPath = resolve("src/ui/layouts.css");

describe("GUI long label responsive contract", () => {
  it("keeps the contract discoverable from the GUI contract index and MVP1 plan", () => {
    const index = readFileSync(resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md"), "utf-8");
    const plan = readFileSync(resolve(guiDocsRoot, "GUI_MVP1_PLAN.md"), "utf-8");

    expect(index).toContain("GUI_LONG_LABEL_RESPONSIVE_CONTRACT.md");
    expect(plan).toContain("GUI_LONG_LABEL_RESPONSIVE_CONTRACT.md");
  });

  it("documents the shared surfaces that must handle long labels", () => {
    const contract = readFileSync(contractPath, "utf-8");

    for (const surface of [
      "MetricGrid",
      "ModuleObjectList",
      "SelectedObjectPanel",
      "DetailList",
      "ArtifactList",
      "BlockerPanel",
      "OperationalPanel",
      "ActivityRow",
      "StatusChip",
      "ActionBar",
      "ContextSummary",
      "ReadinessPanel"
    ]) {
      expect(contract).toContain(surface);
    }
  });

  it("documents path-like values that must wrap safely", () => {
    const contract = readFileSync(contractPath, "utf-8");

    for (const valueType of [
      "table names",
      "OTM table/object codes",
      "payload artifact file names",
      "generated artifact file names",
      "source XML paths",
      "target JSON paths",
      "schema root names",
      "mapping target paths",
      "blocker codes and messages"
    ]) {
      expect(contract).toContain(valueType);
    }
  });

  it("keeps the shared CSS wrapping guardrail on text-heavy surfaces", () => {
    const css = readFileSync(layoutsCssPath, "utf-8");

    for (const selector of [
      ".metric",
      ".module-row",
      ".activity-row",
      ".table-list-item",
      ".artifact-list-item",
      ".blocker-item",
      ".detail-stack",
      ".detail-field",
      ".panel-header",
      ".status-chip",
      ".action-bar",
      ".context-summary",
      ".readiness",
      ".empty-text"
    ]) {
      expect(css).toContain(selector);
    }

    expect(css).toContain("overflow-wrap: anywhere;");
    expect(css).toContain("word-break: normal;");
    expect(css).toContain("min-width: 0;");
  });

  it("keeps long-label fixtures synthetic and client-safe", () => {
    const contract = readFileSync(contractPath, "utf-8");

    expect(contract).toContain("synthetic_order_release_export_with_extra_long_file_name_for_responsive_checks.xml");
    expect(contract).toContain("synthetic values only");
    expect(contract).toContain("Do not use real client names");
    expect(contract).toContain("CNPJ");
    expect(contract).toContain("CPF");
  });

  it("records browser visual QA boundaries and current fallback evidence", () => {
    const contract = readFileSync(contractPath, "utf-8");

    expect(contract).toContain("does not claim visual pixel evidence");
    expect(contract).toContain("Browser visual QA is accepted only when");
    expect(contract).toContain("OTM-77");
    expect(contract).toContain("OTM-78");
  });
});
