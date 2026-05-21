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

describe("GUI feedback message pattern contract", () => {
  it("keeps feedback classes centralized in FeedbackMessage", () => {
    const offenders = tsxFilesUnder(sourceRoot)
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => file.path !== "ui/components.tsx")
      .filter((file) => file.source.includes("form-success") || file.source.includes("form-error"))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });

  it("keeps FeedbackMessage exported from the shared UI components module", () => {
    const components = readFileSync(resolve(sourceRoot, "ui/components.tsx"), "utf-8");

    expect(components).toContain("export function FeedbackMessage");
  });
});
