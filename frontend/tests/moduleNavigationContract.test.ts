import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

type ActiveModuleRoute = {
  id: string;
  viewName: string;
};

function readSource(path: string) {
  return readFileSync(resolve("src", path), "utf-8");
}

function moduleDescriptionKeys(source: string) {
  return Array.from(source.matchAll(/^\s{2}([a-z_]+):/gm), (match) => match[1]);
}

const activeModuleRoutes: ActiveModuleRoute[] = [
  { id: "admin", viewName: "AdminConsoleView" },
  { id: "assets", viewName: "AssetsLibraryView" },
  { id: "catalog", viewName: "CatalogCoreView" },
  { id: "evidence", viewName: "EvidenceHubView" },
  { id: "integration_mapping", viewName: "IntegrationMappingView" },
  { id: "load_plan", viewName: "LoadPlanView" },
  { id: "master_data", viewName: "MasterDataView" },
  { id: "order_release_generator", viewName: "OrderReleaseGeneratorView" },
  { id: "rates", viewName: "RatesSummaryView" }
];

const placeholderOnlyModuleIds = ["dev_tools"];

describe("GUI module navigation contract", () => {
  it("documents every active GUI module id", () => {
    const descriptionKeys = moduleDescriptionKeys(readSource("app/routes/moduleDescriptions.ts"));

    expect(descriptionKeys).toEqual([...placeholderOnlyModuleIds, ...activeModuleRoutes.map((route) => route.id)].sort());
  });

  it("routes every active module id to its module view", () => {
    const routeSource = readSource("app/routes/WorkbenchRoute.tsx");

    for (const route of activeModuleRoutes) {
      expect(routeSource).toContain(`item?.id === "${route.id}"`);
      expect(routeSource).toContain(`<${route.viewName} token={token} />`);
    }
  });

  it("keeps active module views exported by the modules barrel", () => {
    const moduleBarrel = readSource("modules/index.ts");

    for (const route of activeModuleRoutes) {
      expect(moduleBarrel).toContain(`export { ${route.viewName} }`);
    }
  });

  it("keeps planned placeholder modules out of explicit App view routing", () => {
    const routeSource = readSource("app/routes/WorkbenchRoute.tsx");

    for (const moduleId of placeholderOnlyModuleIds) {
      expect(routeSource).not.toContain(`item?.id === "${moduleId}"`);
    }
  });
});
