import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");

describe("GUI decisions log", () => {
  it("keeps required fields for durable GUI decisions", () => {
    const log = readFileSync(resolve(guiDocsRoot, "GUI_DECISIONS_LOG.md"), "utf-8");
    const requiredFields = [
      "ID:",
      "Status:",
      "Date:",
      "Decision:",
      "Reason:",
      "Frontend impact:",
      "Backend ownership:",
      "Tests or guardrails:",
      "Supersedes:"
    ];

    for (const field of requiredFields) {
      expect(log).toContain(field);
    }
  });

  it("records the core accepted GUI architecture decisions", () => {
    const log = readFileSync(resolve(guiDocsRoot, "GUI_DECISIONS_LOG.md"), "utf-8");

    expect(log).toContain("browser-first React + TypeScript + Vite");
    expect(log).toContain("backend-owned user preferences");
    expect(log).toContain("Tauri first");
    expect(log).toContain("Shared components consume backend-owned data");
  });
});
