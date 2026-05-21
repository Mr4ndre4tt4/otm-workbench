import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

function readSource(path: string) {
  return readFileSync(resolve("src", path), "utf-8");
}

describe("GUI workbench shell pattern contract", () => {
  it("keeps App focused on data wiring and route selection", () => {
    const appSource = readSource("app/App.tsx");

    expect(appSource).toContain('import { LoginPanel, WorkbenchShell } from "./shell"');
    expect(appSource).not.toContain('className="app-shell"');
    expect(appSource).not.toContain('className="sidebar"');
    expect(appSource).not.toContain('className="topbar"');
    expect(appSource).not.toContain("PreferenceControls");
    expect(appSource).not.toContain("SidebarNav");
  });

  it("keeps the shared shell frame centralized in WorkbenchShell", () => {
    const shellSource = readSource("app/shell/WorkbenchShell.tsx");
    const shellBarrel = readSource("app/shell/index.ts");

    expect(shellSource).toContain('className="app-shell"');
    expect(shellSource).toContain('className="sidebar"');
    expect(shellSource).toContain('className="topbar"');
    expect(shellSource).toContain("PreferenceControls");
    expect(shellSource).toContain("SidebarNav");
    expect(shellBarrel).toContain('export { WorkbenchShell } from "./WorkbenchShell"');
  });
});
