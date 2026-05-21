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

describe("GUI readiness panel pattern contract", () => {
  it("keeps readiness markup centralized in ReadinessPanel", () => {
    const offenders = tsxFilesUnder(sourceRoot)
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => file.path !== "app/shell/ReadinessPanel.tsx")
      .filter((file) => file.source.includes('className="readiness') || file.source.includes("readiness-ready"))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });

  it("keeps ReadinessPanel exported from the shell barrel", () => {
    const shellBarrel = readFileSync(resolve(sourceRoot, "app/shell/index.ts"), "utf-8");

    expect(shellBarrel).toContain('export { ReadinessPanel } from "./ReadinessPanel"');
  });
});
