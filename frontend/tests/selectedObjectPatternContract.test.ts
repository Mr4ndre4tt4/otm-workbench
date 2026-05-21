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

describe("GUI selected object pattern contract", () => {
  it("keeps selected object panel markup centralized in SelectedObjectPanel", () => {
    const offenders = tsxFilesUnder(join(sourceRoot, "modules"))
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) =>
        ["module-template-side", "detail-stack", "detail-grid", "detail-actions"].some((className) =>
          file.source.includes(className)
        )
      )
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });

  it("requires accessible labels for every selected object panel usage", () => {
    const offenders = tsxFilesUnder(join(sourceRoot, "modules"))
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => file.source.includes("<SelectedObjectPanel"))
      .filter((file) => !/<SelectedObjectPanel[\s\S]*?ariaLabel=/.test(file.source))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });
});
