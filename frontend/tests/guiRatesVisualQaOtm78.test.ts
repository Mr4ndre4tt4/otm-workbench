import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const visualQaPath = resolve(guiDocsRoot, "GUI_RATES_VISUAL_QA_OTM78.md");

describe("GUI Rates visual QA OTM-78", () => {
  it("records the Rates slice, synthetic scope, and screenshot evidence paths", () => {
    const visualQa = readFileSync(visualQaPath, "utf-8");

    expect(visualQa).toContain("OTM-78");
    expect(visualQa).toContain("Playwright fallback");
    expect(visualQa).toContain("synthetic.user@example.test");
    expect(visualQa).toContain("otm78_rates_desktop_final.png");
    expect(visualQa).toContain("otm78_rates_mobile_final3.png");
  });

  it("documents the Rates action, artifact, evidence, and keyboard checks", () => {
    const visualQa = readFileSync(visualQaPath, "utf-8");

    expect(visualQa).toContain("Validate, Approve, Export CSV");
    expect(visualQa).toContain("Artifact and evidence rows");
    expect(visualQa).toContain("Keyboard smoke");
    expect(visualQa).toContain("Download");
  });
});
