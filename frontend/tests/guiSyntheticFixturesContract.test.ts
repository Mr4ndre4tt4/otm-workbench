import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");

describe("GUI synthetic fixtures contract", () => {
  it("documents the shared synthetic fixture source and forbidden real data", () => {
    const contract = readFileSync(resolve(guiDocsRoot, "GUI_SYNTHETIC_FIXTURES_CONTRACT.md"), "utf-8");

    expect(contract).toContain("frontend/src/test/fixtures/gui.ts");
    expect(contract).toContain("synthetic backend-shaped examples");
    expect(contract).toContain("real client names");
    expect(contract).toContain("CNPJ");
    expect(contract).toContain("CPF");
  });

  it("keeps the gallery plan and implementation checklist linked to synthetic fixtures", () => {
    const galleryPlan = readFileSync(resolve(guiDocsRoot, "GUI_COMPONENT_GALLERY_PLAN.md"), "utf-8");
    const checklist = readFileSync(resolve(guiDocsRoot, "GUI_IMPLEMENTATION_CHECKLIST.md"), "utf-8");

    expect(galleryPlan).toContain("frontend/src/test/fixtures/gui.ts");
    expect(checklist).toContain("frontend/src/test/fixtures/gui.ts");
  });
});
