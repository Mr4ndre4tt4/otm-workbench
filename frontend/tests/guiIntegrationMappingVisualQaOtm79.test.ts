import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const visualQaPath = resolve(guiDocsRoot, "GUI_INTEGRATION_MAPPING_VISUAL_QA_OTM79.md");

describe("GUI Integration Mapping visual QA OTM-79", () => {
  it("records the Integration Mapping slice, synthetic scope, and screenshot evidence paths", () => {
    const visualQa = readFileSync(visualQaPath, "utf-8");

    expect(visualQa).toContain("OTM-79");
    expect(visualQa).toContain("Playwright fallback");
    expect(visualQa).toContain("synthetic.user@example.test");
    expect(visualQa).toContain("otm79_integration_desktop_fixed.png");
    expect(visualQa).toContain("otm79_integration_mobile_fixed.png");
  });

  it("documents the DetailList fix and keyboard/console QA coverage", () => {
    const visualQa = readFileSync(visualQaPath, "utf-8");

    expect(visualQa).toContain("DetailList");
    expect(visualQa).toContain("XML and JSON path-like labels");
    expect(visualQa).toContain("Keyboard smoke");
    expect(visualQa).toContain("React DevTools info message");
  });
});
