import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { describe, expect, it } from "vitest";

const sourceRoot = resolve("src");
const allowedRawStatusChipFiles = new Set(["ui/components/primitives.tsx"]);

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

describe("GUI status chip pattern contract", () => {
  it("keeps raw status chip classes centralized in StatusChip", () => {
    const offenders = tsxFilesUnder(sourceRoot)
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => !allowedRawStatusChipFiles.has(file.path))
      .filter((file) => file.source.includes("status-chip") || file.source.includes("status-"))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });

  it("keeps StatusChip exported from the shared UI components barrel", () => {
    const components = readFileSync(resolve(sourceRoot, "ui/components.tsx"), "utf-8");

    expect(components).toContain('export { Button, IconButton, StatusChip } from "./components/primitives"');
  });
});
