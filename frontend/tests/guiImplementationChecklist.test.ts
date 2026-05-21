import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const checklistPath = resolve(guiDocsRoot, "GUI_IMPLEMENTATION_CHECKLIST.md");

describe("GUI implementation checklist", () => {
  it("keeps backend ownership and no frontend-only durable state explicit", () => {
    const checklist = readFileSync(checklistPath, "utf-8");

    expect(checklist).toContain("backend-first architecture");
    expect(checklist).toContain("no durable product state lives only in frontend");
    expect(checklist).toContain("Navigation, permissions, lifecycle, readiness, actions, jobs, artifacts");
    expect(checklist).toContain("preferences remain backend-owned");
  });

  it("requires contract, decision, exception, and Linear tracking checks", () => {
    const checklist = readFileSync(checklistPath, "utf-8");

    expect(checklist).toContain("GUI_CONTRACT_INDEX.md");
    expect(checklist).toContain("GUI_EXCEPTIONS_REGISTER.md");
    expect(checklist).toContain("GUI_DECISIONS_LOG.md");
    expect(checklist).toContain("Linear updated");
  });

  it("lists the shared GUI components before new markup is created", () => {
    const checklist = readFileSync(checklistPath, "utf-8");
    const requiredComponents = [
      "WorkbenchShell",
      "WorkbenchRoute",
      "ModuleWorkspaceLayout",
      "SelectedObjectPanel",
      "ArtifactList",
      "BlockerPanel",
      "FeedbackMessage",
      "StatePanel",
      "StatusChip"
    ];

    for (const componentName of requiredComponents) {
      expect(checklist).toContain(componentName);
    }
  });

  it("keeps architecture docs pointing at the checklist", () => {
    const architecture = readFileSync(resolve(guiDocsRoot, "GUI_FRONTEND_ARCHITECTURE.md"), "utf-8");

    expect(architecture).toContain("GUI_IMPLEMENTATION_CHECKLIST.md");
  });
});
