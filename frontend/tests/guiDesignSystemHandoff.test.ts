import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const handoffPath = resolve(guiDocsRoot, "GUI_DESIGN_SYSTEM_HANDOFF.md");

describe("GUI design system handoff", () => {
  it("keeps the handoff document discoverable from the GUI contract index", () => {
    const index = readFileSync(resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md"), "utf-8");

    expect(index).toContain("GUI_DESIGN_SYSTEM_HANDOFF.md");
  });

  it("defines Figma foundation pages for the current GUI contracts", () => {
    const handoff = readFileSync(handoffPath, "utf-8");

    for (const section of [
      "01 Foundations",
      "03 Shell",
      "04 Components",
      "05 Module Workspace",
      "07 Operational",
      "09 Module Screens"
    ]) {
      expect(handoff).toContain(section);
    }
  });

  it("keeps Lucide as the MVP1 implementation default and Iconly as a governed pilot", () => {
    const handoff = readFileSync(handoffPath, "utf-8");
    const decisions = readFileSync(resolve(guiDocsRoot, "GUI_DECISIONS_LOG.md"), "utf-8");

    expect(handoff).toContain("Keep Lucide as the implementation icon family");
    expect(handoff).toContain("Iconly V3.0 / Iconly Pro Community can be evaluated as a Figma/design pilot");
    expect(handoff).toContain("No module may choose a different icon family independently");
    expect(decisions).toContain("GUI-DEC-006");
    expect(decisions).toContain("Keep Lucide as the MVP1 implementation icon family");
  });

  it("keeps backend ownership and client-safe handoff rules explicit", () => {
    const handoff = readFileSync(handoffPath, "utf-8");

    expect(handoff).toContain("Code contracts remain authoritative for behavior");
    expect(handoff).toContain("Use synthetic content only");
    expect(handoff).toContain("backend-owned");
  });
});
