import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const attemptPath = resolve(guiDocsRoot, "GUI_GALLERY_VISUAL_QA_ATTEMPT.md");

describe("GUI gallery visual QA attempt", () => {
  it("records the browser-backed gallery QA attempt without claiming screenshots", () => {
    const attempt = readFileSync(attemptPath, "utf-8");

    expect(attempt).toContain("OTM-65");
    expect(attempt).toContain("/__gui/component-gallery");
    expect(attempt).toContain("HTTP readiness check");
    expect(attempt).toContain("CreateProcessWithLogonW failed: 1326");
    expect(attempt).toContain("no screenshot");
  });

  it("keeps the gallery plan linked to the visual QA attempt", () => {
    const plan = readFileSync(resolve(guiDocsRoot, "GUI_COMPONENT_GALLERY_PLAN.md"), "utf-8");

    expect(plan).toContain("GUI_GALLERY_VISUAL_QA_ATTEMPT.md");
  });
});
