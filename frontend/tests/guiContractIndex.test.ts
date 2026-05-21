import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const indexPath = resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md");

function contractDocs() {
  return readdirSync(guiDocsRoot)
    .filter((fileName) => fileName.startsWith("GUI_"))
    .filter((fileName) => fileName.endsWith("_CONTRACT.md") || fileName.endsWith("_CONTRACTS.md"))
    .filter((fileName) => fileName !== "GUI_CONTRACT_INDEX.md")
    .sort();
}

describe("GUI contract index", () => {
  it("lists every GUI contract document", () => {
    const index = readFileSync(indexPath, "utf-8");
    const missing = contractDocs().filter((fileName) => !index.includes(fileName));

    expect(missing).toEqual([]);
  });

  it("keeps the backend ownership reminder in the contract index", () => {
    const index = readFileSync(indexPath, "utf-8");

    expect(index).toContain("Backend remains source of truth");
    expect(index).toContain("navigation and module visibility");
    expect(index).toContain("active context and user preferences");
  });
});
