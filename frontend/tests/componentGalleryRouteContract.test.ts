import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

function readSource(path: string) {
  return readFileSync(resolve("src", path), "utf-8");
}

describe("Internal component gallery route contract", () => {
  it("keeps the component gallery hidden from backend-owned production navigation", () => {
    const routeSource = readSource("app/routes/WorkbenchRoute.tsx");
    const gallerySource = readSource("app/routes/ComponentGalleryRoute.tsx");

    expect(routeSource).toContain('currentPath === "/__gui/component-gallery"');
    expect(routeSource).toContain("<ComponentGalleryRoute />");
    expect(gallerySource).toContain("not published through backend navigation");
    expect(gallerySource).toContain("../../test/fixtures/gui");
  });

  it("uses the shared synthetic fixture contract for gallery examples", () => {
    const gallerySource = readSource("app/routes/ComponentGalleryRoute.tsx");

    for (const fixture of [
      "syntheticMetricItems",
      "syntheticModuleObjects",
      "syntheticDetailRows",
      "syntheticArtifactItems",
      "syntheticBlockers"
    ]) {
      expect(gallerySource).toContain(fixture);
    }
  });
});
