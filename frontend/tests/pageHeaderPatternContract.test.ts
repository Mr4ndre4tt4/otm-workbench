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

describe("GUI page header pattern contract", () => {
  it("keeps page-header markup centralized in PageHeader", () => {
    const offenders = tsxFilesUnder(sourceRoot)
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => file.path.startsWith("app/") || file.path.startsWith("modules/"))
      .filter((file) => file.path !== "app/shell/PageHeader.tsx")
      .filter((file) => file.source.includes("page-header"))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });

  it("keeps module-level h1 rendering behind PageHeader", () => {
    const offenders = tsxFilesUnder(join(sourceRoot, "modules"))
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => file.source.includes("<h1"))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });
});
