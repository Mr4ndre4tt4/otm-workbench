import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { describe, expect, it } from "vitest";

const sourceRoot = resolve("src");
const allowedRawModuleTemplateFiles = new Set(["ui/components/layouts.tsx", "ui/components/panels.tsx"]);

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

describe("GUI module workspace layout pattern contract", () => {
  it("keeps module-template markup centralized in shared UI components", () => {
    const offenders = tsxFilesUnder(sourceRoot)
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => !allowedRawModuleTemplateFiles.has(file.path))
      .filter((file) => file.source.includes("module-template"))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });

  it("requires module views to use ModuleWorkspaceLayout for the main workspace grid", () => {
    const offenders = tsxFilesUnder(join(sourceRoot, "modules"))
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => !file.source.includes("<ModuleWorkspaceLayout"))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });
});
