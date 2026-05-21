import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const sourceRoot = resolve("src");
const guiDocsRoot = resolve("../docs/otm-workbench/gui");

describe("GUI frontend ownership component split", () => {
  it("keeps the public UI kit barrel stable while splitting internal ownership files", () => {
    const barrel = readFileSync(resolve(sourceRoot, "ui/components.tsx"), "utf-8");
    const internalFiles = [
      "activity.tsx",
      "layouts.tsx",
      "lists.tsx",
      "metrics.tsx",
      "panels.tsx",
      "primitives.tsx",
      "states.tsx"
    ];

    for (const fileName of internalFiles) {
      expect(existsSync(resolve(sourceRoot, "ui/components", fileName))).toBe(true);
    }

    expect(barrel).toContain('from "./components/primitives"');
    expect(barrel).toContain('from "./components/lists"');
    expect(barrel).toContain('from "./components/panels"');
  });

  it("records the accepted frontend ownership layout in architecture docs", () => {
    const architecture = readFileSync(resolve(guiDocsRoot, "GUI_FRONTEND_ARCHITECTURE.md"), "utf-8");
    const cleanup = readFileSync(resolve(guiDocsRoot, "GUI_FRONTEND_ARCHITECTURE_CLEANUP.md"), "utf-8");

    expect(architecture).toContain("accepted and incrementally implemented");
    expect(architecture).toContain("frontend/src/ui/components/");
    expect(architecture).toContain("stable public barrel");
    expect(cleanup).toContain("Internal component families now live");
    expect(cleanup).toContain("primitives.tsx");
    expect(cleanup).toContain("panels.tsx");
  });
});
