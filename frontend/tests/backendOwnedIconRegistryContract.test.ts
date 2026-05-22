import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const contractPath = resolve(guiDocsRoot, "GUI_BACKEND_OWNED_ICON_ASSET_REGISTRY.md");

function readSource(path: string) {
  return readFileSync(resolve("src", path), "utf-8");
}

describe("backend-owned icon and label registry contract", () => {
  it("keeps the registry contract discoverable", () => {
    const index = readFileSync(resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md"), "utf-8");
    const contract = readFileSync(contractPath, "utf-8");

    expect(index).toContain("GUI_BACKEND_OWNED_ICON_ASSET_REGISTRY.md");
    expect(contract).toContain("Navigation icons, module labels, action labels, and program display metadata");
    expect(contract).toContain("The frontend owns rendering mechanics only");
  });

  it("keeps SidebarNav consuming backend icon_key without module-local icon decisions", () => {
    const sidebarSource = readSource("app/shell/SidebarNav.tsx");

    expect(sidebarSource).toContain("item.icon_key");
    expect(sidebarSource).toContain("renderIcon");
    expect(sidebarSource).not.toContain("function navIcon");
    expect(sidebarSource).not.toContain("if (iconKey ===");
  });
});
