import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const visualQaPath = resolve(guiDocsRoot, "GUI_COMPONENT_GALLERY_VISUAL_QA_OTM80.md");

describe("GUI Component Gallery visual QA OTM-80", () => {
  it("records the component gallery slice and screenshot evidence paths", () => {
    const visualQa = readFileSync(visualQaPath, "utf-8");

    expect(visualQa).toContain("OTM-80");
    expect(visualQa).toContain("Playwright fallback");
    expect(visualQa).toContain("/__gui/component-gallery");
    expect(visualQa).toContain("otm80_gallery_desktop_final.png");
    expect(visualQa).toContain("otm80_gallery_mobile_final.png");
  });

  it("documents the fixed reusable previews and keyboard/console QA coverage", () => {
    const visualQa = readFileSync(visualQaPath, "utf-8");

    expect(visualQa).toContain("LoginPanel");
    expect(visualQa).toContain("ContextSwitcher");
    expect(visualQa).toContain("gallery-selector-preview");
    expect(visualQa).toContain("Keyboard smoke");
    expect(visualQa).toContain("zero errors and zero warnings");
  });

  it("keeps the component gallery visual evidence indexed", () => {
    const index = readFileSync(resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md"), "utf-8");
    const attempt = readFileSync(resolve(guiDocsRoot, "GUI_GALLERY_VISUAL_QA_ATTEMPT.md"), "utf-8");

    expect(index).toContain("GUI_COMPONENT_GALLERY_VISUAL_QA_OTM80.md");
    expect(attempt).toContain("GUI_COMPONENT_GALLERY_VISUAL_QA_OTM80.md");
  });
});
