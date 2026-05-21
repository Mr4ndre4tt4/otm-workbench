import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { describe, expect, it } from "vitest";

const sourceRoot = resolve("src");
const allowedRawOperationalListFiles = new Set(["ui/components/lists.tsx", "ui/components/panels.tsx"]);

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

describe("GUI operational list pattern contract", () => {
  it("keeps artifact and blocker list classes centralized in shared UI components", () => {
    const rawClassNames = ["artifact-list", "artifact-list-item", "blocker-list", "blocker-item", "blockers-panel"];
    const offenders = tsxFilesUnder(sourceRoot)
      .map((path) => ({
        path: sourcePath(path),
        source: readFileSync(path, "utf-8")
      }))
      .filter((file) => !allowedRawOperationalListFiles.has(file.path))
      .filter((file) => rawClassNames.some((className) => file.source.includes(className)))
      .map((file) => file.path);

    expect(offenders).toEqual([]);
  });

  it("keeps Rates operational lists on shared components", () => {
    const ratesSource = readFileSync(resolve(sourceRoot, "modules/rates/RatesSummaryView.tsx"), "utf-8");

    expect(ratesSource).toContain("<BlockerPanel");
    expect(ratesSource).toContain("<ArtifactList");
  });
});
