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

describe("GUI operational panel pattern contract", () => {
  it("keeps raw panel card markup out of app and module screens", () => {
    const offenders = tsxFilesUnder(sourceRoot)
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => file.path.startsWith("app/") || file.path.startsWith("modules/"))
      .filter((file) => file.source.includes('className="panel"') || file.source.includes('className={`panel '))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });

  it("requires accessible labels for every operational panel usage", () => {
    const offenders = tsxFilesUnder(sourceRoot)
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => file.path.startsWith("app/") || file.path.startsWith("modules/"))
      .filter((file) => file.source.includes("<OperationalPanel"))
      .filter((file) => !/<OperationalPanel[\s\S]*?ariaLabel=/.test(file.source))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });
});
