import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const matrixPath = resolve(guiDocsRoot, "GUI_ACCESSIBILITY_QA_MATRIX.md");

describe("GUI accessibility QA matrix", () => {
  it("defines the baseline routes, viewports, and preference states", () => {
    const matrix = readFileSync(matrixPath, "utf-8");

    for (const route of ["/login", "/", "/rates", "/integration-mapping", "/__gui/component-gallery"]) {
      expect(matrix).toContain(route);
    }

    expect(matrix).toContain("Desktop: 1280 x 840");
    expect(matrix).toContain("Mobile:  390 x 844");
    expect(matrix).toContain("light mode");
    expect(matrix).toContain("dark mode");
    expect(matrix).toContain("system mode");
    expect(matrix).toContain("compact density");
    expect(matrix).toContain("collapsed sidebar");
  });

  it("requires keyboard, accessibility, responsive, console, and client-data-safe checks", () => {
    const matrix = readFileSync(matrixPath, "utf-8");

    expect(matrix).toContain("Keyboard Baseline");
    expect(matrix).toContain("sidebar navigation links");
    expect(matrix).toContain("accessible names");
    expect(matrix).toContain("aria labels");
    expect(matrix).toContain("no horizontal page overflow");
    expect(matrix).toContain("console has zero errors");
    expect(matrix).toContain("console has zero warnings");
    expect(matrix).toContain("synthetic data only");
    expect(matrix).toContain("CNPJ");
    expect(matrix).toContain("CPF");
  });

  it("links the current browser-backed evidence and governance docs", () => {
    const matrix = readFileSync(matrixPath, "utf-8");
    const index = readFileSync(resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md"), "utf-8");
    const checklist = readFileSync(resolve(guiDocsRoot, "GUI_IMPLEMENTATION_CHECKLIST.md"), "utf-8");
    const shellQa = readFileSync(resolve(guiDocsRoot, "GUI_SHELL_QA_CONTRACTS.md"), "utf-8");

    for (const evidence of ["OTM-77", "OTM-78", "OTM-79", "OTM-80"]) {
      expect(matrix).toContain(evidence);
    }

    expect(index).toContain("GUI_ACCESSIBILITY_QA_MATRIX.md");
    expect(checklist).toContain("GUI_ACCESSIBILITY_QA_MATRIX.md");
    expect(shellQa).toContain("GUI_ACCESSIBILITY_QA_MATRIX.md");
  });
});
