import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const reviewPath = resolve(guiDocsRoot, "GUI_SHARED_OPERATIONAL_PANELS_COMPLETION_REVIEW_OTM59.md");

describe("GUI shared operational panels completion review OTM-59", () => {
  it("records the delivered shared operational components and contracts", () => {
    const review = readFileSync(reviewPath, "utf-8");

    expect(review).toContain("OTM-59");

    for (const componentName of ["OperationalPanel", "ArtifactList", "BlockerPanel", "ActivityRow"]) {
      expect(review).toContain(componentName);
    }

    for (const contractName of [
      "GUI_SHARED_OPERATIONAL_PANELS.md",
      "GUI_OPERATIONAL_PANEL_PATTERN_CONTRACT.md",
      "GUI_OPERATIONAL_LIST_PATTERN_CONTRACT.md",
      "GUI_ACTIVITY_ROW_PATTERN_CONTRACT.md",
      "GUI_MODULE_OPERATIONAL_SURFACES_CONTRACT.md"
    ]) {
      expect(review).toContain(contractName);
    }
  });

  it("keeps backend ownership, guardrails, and client-data rules explicit", () => {
    const review = readFileSync(reviewPath, "utf-8");

    expect(review).toContain("whether artifacts exist");
    expect(review).toContain("whether evidence is client-safe");
    expect(review).toContain("job status and progress");
    expect(review).toContain("OperationalPanel usage without accessible labels");
    expect(review).toContain("synthetic content only");
    expect(review).toContain("CNPJ");
    expect(review).toContain("CPF");
  });

  it("keeps the completion review discoverable from the GUI index", () => {
    const index = readFileSync(resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md"), "utf-8");

    expect(index).toContain("Module Completion Reviews");
    expect(index).toContain("GUI_SHARED_OPERATIONAL_PANELS_COMPLETION_REVIEW_OTM59.md");
  });
});
