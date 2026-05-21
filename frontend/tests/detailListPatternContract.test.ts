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

describe("GUI detail list pattern contract", () => {
  it("keeps detail row markup centralized in DetailList", () => {
    const offenders = tsxFilesUnder(join(sourceRoot, "modules"))
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => file.source.includes("table-list") || file.source.includes("table-list-item"))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });

  it("requires accessible labels for every detail list usage", () => {
    const offenders = tsxFilesUnder(join(sourceRoot, "modules"))
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => file.source.includes("<DetailList"))
      .filter((file) => !/<DetailList[\s\S]*?ariaLabel=/.test(file.source))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });
});
