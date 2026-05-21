import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

function readSource(path: string) {
  return readFileSync(resolve("src", path), "utf-8");
}

function importSpecifiers(source: string) {
  return Array.from(source.matchAll(/from\s+["']([^"']+)["']/g), (match) => match[1]);
}

describe("React architecture boundaries", () => {
  it("keeps route module views behind the modules barrel", () => {
    const appImports = importSpecifiers(readSource("app/App.tsx"));
    const routeImports = importSpecifiers(readSource("app/routes/WorkbenchRoute.tsx"));

    expect(appImports.filter((specifier) => specifier.includes("/modules"))).toEqual([]);
    expect(routeImports).toContain("../../modules");
    expect(routeImports.filter((specifier) => specifier.startsWith("../../modules/"))).toEqual([
      "../../modules/moduleStatus"
    ]);
  });

  it("keeps App shell components behind the shell barrel", () => {
    const imports = importSpecifiers(readSource("app/App.tsx"));

    expect(imports).toContain("./shell");
    expect(imports.filter((specifier) => specifier.startsWith("./shell/"))).toEqual([]);
  });

  it("keeps module view exports centralized in the modules barrel", () => {
    const barrel = readSource("modules/index.ts");
    const expectedExports = [
      "AssetsLibraryView",
      "CatalogCoreView",
      "EvidenceHubView",
      "IntegrationMappingView",
      "LoadPlanView",
      "MasterDataView",
      "OrderReleaseGeneratorView",
      "RatesSummaryView"
    ];

    for (const viewName of expectedExports) {
      expect(barrel).toContain(`export { ${viewName} }`);
    }
  });

  it("keeps shell component exports centralized in the shell barrel", () => {
    const barrel = readSource("app/shell/index.ts");
    const expectedExports = [
      "ActionBar",
      "ContextSummary",
      "ContextSwitcher",
      "LoginPanel",
      "PageHeader",
      "PreferenceControls",
      "ReadinessPanel",
      "SidebarNav"
    ];

    for (const componentName of expectedExports) {
      expect(barrel).toContain(`export { ${componentName} }`);
    }
  });
});
