import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { describe, expect, it } from "vitest";

const sourceRoot = resolve("src");
const allowedRawStatePanelFiles = new Set(["ui/components/states.tsx"]);

function tsxFilesUnder(path: string): string[] {
  return readdirSync(path).flatMap((entry) => {
    const absolutePath = join(path, entry);
    if (statSync(absolutePath).isDirectory()) {
      return tsxFilesUnder(absolutePath);
    }
    return absolutePath.endsWith(".tsx") && !absolutePath.endsWith(".test.tsx") ? [absolutePath] : [];
  });
}

function sourcePath(path: string) {
  return relative(sourceRoot, path).replaceAll("\\", "/");
}

describe("GUI shared state pattern contract", () => {
  it("keeps raw state-panel markup centralized in the UI kit", () => {
    const offenders = tsxFilesUnder(sourceRoot)
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => !allowedRawStatePanelFiles.has(file.path))
      .filter((file) => file.source.includes("state-panel"))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });

  it("exposes StatePanel from the shared UI components barrel", () => {
    const components = readFileSync(resolve(sourceRoot, "ui/components.tsx"), "utf-8");

    expect(components).toContain('export { FeedbackMessage, StatePanel } from "./components/states"');
  });
});
