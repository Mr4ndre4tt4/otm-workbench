import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const contractPath = resolve(guiDocsRoot, "GUI_STAGED_WORKFLOW_PATTERN_CONTRACT.md");

describe("GUI staged workflow pattern contract", () => {
  it("keeps the staged workflow contract discoverable from the index and MVP1 plan", () => {
    const index = readFileSync(resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md"), "utf-8");
    const plan = readFileSync(resolve(guiDocsRoot, "GUI_MVP1_PLAN.md"), "utf-8");

    expect(index).toContain("GUI_STAGED_WORKFLOW_PATTERN_CONTRACT.md");
    expect(plan).toContain("GUI_STAGED_WORKFLOW_PATTERN_CONTRACT.md");
  });

  it("forbids stacked disconnected authoring panels for complex modules", () => {
    const contract = readFileSync(contractPath, "utf-8");
    const checklist = readFileSync(resolve(guiDocsRoot, "GUI_IMPLEMENTATION_CHECKLIST.md"), "utf-8");
    const decisions = readFileSync(resolve(guiDocsRoot, "GUI_DECISIONS_LOG.md"), "utf-8");

    expect(contract).toContain("One primary operational stage is visible at a time");
    expect(contract).toContain("Do not stack unrelated OperationalPanel sections one after another");
    expect(checklist).toContain("Complex module screens must not stack unrelated authoring panels");
    expect(decisions).toContain("GUI-DEC-007");
  });
});
