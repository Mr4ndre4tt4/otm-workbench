import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const planPath = resolve(guiDocsRoot, "GUI_COMPONENT_GALLERY_PLAN.md");

describe("GUI component gallery plan", () => {
  it("keeps the gallery backend-first and client-safe", () => {
    const plan = readFileSync(planPath, "utf-8");

    expect(plan).toContain("Backend-first");
    expect(plan).toContain("synthetic contract-shaped data");
    expect(plan).toContain("Client-safe");
    expect(plan).toContain("no real client names");
    expect(plan).toContain("CNPJ");
    expect(plan).toContain("CPF");
  });

  it("defines both internal route and Storybook rollout options", () => {
    const plan = readFileSync(planPath, "utf-8");

    expect(plan).toContain("Option A - Internal Component Gallery Route");
    expect(plan).toContain("Option B - Storybook");
    expect(plan).toContain("requires new frontend tooling dependencies");
  });

  it("covers the current shared GUI component patterns", () => {
    const plan = readFileSync(planPath, "utf-8");
    const requiredPatterns = [
      "WorkbenchShell",
      "LoginPanel",
      "PageHeader",
      "ContextSummary",
      "ContextSwitcher",
      "ReadinessPanel",
      "MetricGrid",
      "ModuleWorkspaceLayout",
      "ModuleObjectList",
      "SelectedObjectPanel",
      "DetailList",
      "OperationalPanel",
      "ArtifactList",
      "BlockerPanel",
      "ActionBar",
      "FeedbackMessage",
      "StatePanel",
      "StatusChip",
      "Button/IconButton"
    ];

    for (const pattern of requiredPatterns) {
      expect(plan).toContain(pattern);
    }
  });

  it("keeps architecture docs pointing at the gallery plan", () => {
    const architecture = readFileSync(resolve(guiDocsRoot, "GUI_FRONTEND_ARCHITECTURE.md"), "utf-8");
    const cleanup = readFileSync(resolve(guiDocsRoot, "GUI_FRONTEND_ARCHITECTURE_CLEANUP.md"), "utf-8");

    expect(architecture).toContain("GUI_COMPONENT_GALLERY_PLAN.md");
    expect(cleanup).toContain("GUI_COMPONENT_GALLERY_PLAN.md");
  });
});
