import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const sourceRoot = resolve("src");
const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const auditPath = resolve(guiDocsRoot, "GUI_MODULE_SCREEN_CONSISTENCY_AUDIT.md");

const moduleViewPaths = [
  "modules/rates/RatesSummaryView.tsx",
  "modules/catalog/CatalogCoreView.tsx",
  "modules/load-plan/LoadPlanView.tsx",
  "modules/assets/AssetsLibraryView.tsx",
  "modules/evidence/EvidenceHubView.tsx",
  "modules/master-data/MasterDataView.tsx",
  "modules/order-release-generator/OrderReleaseGeneratorView.tsx",
  "modules/integration-mapping/IntegrationMappingView.tsx"
];

const requiredTemplateMarkers = [
  "<PageHeader",
  "<MetricGrid",
  "<ModuleWorkspaceLayout",
  "<ModuleObjectList",
  "<SelectedObjectPanel",
  "<DetailList",
  "<StatePanel"
];

function readSource(relativePath: string) {
  return readFileSync(resolve(sourceRoot, relativePath), "utf-8");
}

describe("GUI module screen consistency audit", () => {
  it("keeps the audit document linked from the GUI contract index", () => {
    const index = readFileSync(resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md"), "utf-8");

    expect(index).toContain("GUI_MODULE_SCREEN_CONSISTENCY_AUDIT.md");
  });

  it("documents every implemented backend-backed module", () => {
    const audit = readFileSync(auditPath, "utf-8");
    const expectedModules = [
      "Rates Studio",
      "Catalog Core",
      "Load Plan",
      "Assets Library",
      "Evidence Hub",
      "Master Data",
      "Order Release Generator",
      "Integration Mapping Studio"
    ];

    for (const moduleName of expectedModules) {
      expect(audit).toContain(moduleName);
    }
  });

  it("keeps implemented module screens on the shared module template", () => {
    for (const moduleViewPath of moduleViewPaths) {
      const source = readSource(moduleViewPath);

      for (const marker of requiredTemplateMarkers) {
        expect(source, `${moduleViewPath} should contain ${marker}`).toContain(marker);
      }
    }
  });

  it("keeps modules importing the public UI kit barrel instead of internal component files", () => {
    const moduleRoot = resolve(sourceRoot, "modules");
    const moduleFiles = readdirSync(moduleRoot, { recursive: true })
      .map(String)
      .filter((path) => path.endsWith(".tsx"));

    for (const moduleFile of moduleFiles) {
      const source = readFileSync(resolve(moduleRoot, moduleFile), "utf-8");

      expect(source).not.toContain("/ui/components/");
      expect(source).not.toContain("../../ui/components/");
    }
  });

  it("records the concrete follow-up issues for the gaps found", () => {
    const audit = readFileSync(auditPath, "utf-8");

    expect(audit).toContain("OTM-69");
    expect(audit).toContain("OTM-70");
    expect(audit).toContain("OTM-71");
  });
});
