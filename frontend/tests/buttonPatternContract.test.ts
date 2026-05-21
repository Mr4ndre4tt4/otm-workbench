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

describe("GUI button pattern contract", () => {
  it("keeps raw button elements centralized in shared UI components", () => {
    const offenders = tsxFilesUnder(sourceRoot)
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => file.path.startsWith("app/") || file.path.startsWith("modules/"))
      .filter((file) => file.source.includes("<button"))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });

  it("keeps command button classes centralized in the shared UI implementation", () => {
    const offenders = tsxFilesUnder(sourceRoot)
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => file.path !== "ui/components.tsx")
      .filter((file) => file.source.includes("button-primary") || file.source.includes("button-secondary"))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });
});
