import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { describe, expect, it } from "vitest";

const sourceRoot = resolve("src");

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

describe("GUI object list pattern contract", () => {
  it("keeps module list markup centralized in ModuleObjectList", () => {
    const offenders = tsxFilesUnder(join(sourceRoot, "modules"))
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => file.source.includes("module-list") || file.source.includes("module-row"))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });

  it("requires accessible labels for every module object list usage", () => {
    const offenders = tsxFilesUnder(join(sourceRoot, "modules"))
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => file.source.includes("<ModuleObjectList"))
      .filter((file) => !/<ModuleObjectList[\s\S]*?ariaLabel=/.test(file.source))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });
});
