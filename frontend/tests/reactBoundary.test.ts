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
  it("keeps App module views behind the modules barrel", () => {
    const imports = importSpecifiers(readSource("app/App.tsx"));

    expect(imports).toContain("../modules");
    expect(imports.filter((specifier) => specifier.startsWith("../modules/"))).toEqual(["../modules/moduleStatus"]);
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
      "PageHeader",
      "PreferenceControls",
      "SidebarNav"
    ];

    for (const componentName of expectedExports) {
      expect(barrel).toContain(`export { ${componentName} }`);
    }
  });
});
