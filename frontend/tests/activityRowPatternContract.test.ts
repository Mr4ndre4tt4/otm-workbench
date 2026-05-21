import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { describe, expect, it } from "vitest";

const sourceRoot = resolve("src");
const allowedRawActivityRowFiles = new Set(["ui/components/activity.tsx"]);

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

describe("GUI activity row pattern contract", () => {
  it("keeps activity-row markup centralized in ActivityRow", () => {
    const offenders = tsxFilesUnder(sourceRoot)
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => !allowedRawActivityRowFiles.has(file.path))
      .filter((file) => file.source.includes("activity-row"))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });

  it("keeps ActivityRow exported from the shared UI components barrel", () => {
    const components = readFileSync(resolve(sourceRoot, "ui/components.tsx"), "utf-8");

    expect(components).toContain('export { ActivityRow } from "./components/activity"');
  });
});
