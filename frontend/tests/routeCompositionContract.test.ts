import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

function readSource(path: string) {
  return readFileSync(resolve("src", path), "utf-8");
}

describe("GUI route composition contract", () => {
  it("keeps App focused on shell orchestration", () => {
    const appSource = readSource("app/App.tsx");

    expect(appSource).toContain('import { WorkbenchRoute } from "./routes/WorkbenchRoute"');
    expect(appSource).not.toContain("function CockpitContent");
    expect(appSource).not.toContain("function ModulePlaceholder");
    expect(appSource).not.toContain("function UnknownRoute");
    expect(appSource).not.toContain("item?.id ===");
  });

  it("keeps module route composition centralized in WorkbenchRoute", () => {
    const routeSource = readSource("app/routes/WorkbenchRoute.tsx");

    expect(routeSource).toContain("export function WorkbenchRoute");
    expect(routeSource).toContain("function CockpitContent");
    expect(routeSource).toContain("function ModulePlaceholder");
    expect(routeSource).toContain("function UnknownRoute");
    expect(routeSource).toContain("MODULE_DESCRIPTIONS");
    expect(routeSource).toContain("isNavigationItemActive");
  });
});
