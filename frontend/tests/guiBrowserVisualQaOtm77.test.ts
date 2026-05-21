import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const visualQaPath = resolve(guiDocsRoot, "GUI_BROWSER_VISUAL_QA_OTM77.md");

describe("GUI browser visual QA OTM-77", () => {
  it("records the browser fallback, synthetic scope, and screenshot evidence paths", () => {
    const visualQa = readFileSync(visualQaPath, "utf-8");

    expect(visualQa).toContain("OTM-77");
    expect(visualQa).toContain("Playwright fallback");
    expect(visualQa).toContain("synthetic.user@example.test");
    expect(visualQa).toContain("otm77_home_desktop_dark_compact_collapsed_fixed.png");
    expect(visualQa).toContain("otm77_home_mobile_dark_compact_collapsed_fixed.png");
  });

  it("documents the dark mode contrast and favicon fixes found during QA", () => {
    const visualQa = readFileSync(visualQaPath, "utf-8");

    expect(visualQa).toContain("Dark mode contrast regression");
    expect(visualQa).toContain("Favicon 404");
    expect(visualQa).toContain("PYTHONPATH=src");
  });
});
