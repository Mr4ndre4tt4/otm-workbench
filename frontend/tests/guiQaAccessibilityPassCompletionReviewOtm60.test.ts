import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const reviewPath = resolve(guiDocsRoot, "GUI_QA_ACCESSIBILITY_PASS_COMPLETION_REVIEW_OTM60.md");

describe("GUI QA accessibility pass completion review OTM-60", () => {
  it("records the completed QA evidence trail for the current GUI foundation", () => {
    const review = readFileSync(reviewPath, "utf-8");

    expect(review).toContain("OTM-60");

    for (const evidence of ["OTM-77", "OTM-78", "OTM-79", "OTM-80", "OTM-81", "OTM-82", "OTM-83"]) {
      expect(review).toContain(evidence);
    }

    expect(review).toContain("GUI_ACCESSIBILITY_QA_MATRIX.md");
    expect(review).toContain("Project Cockpit");
    expect(review).toContain("Rates Studio");
    expect(review).toContain("Integration Mapping Studio");
    expect(review).toContain("internal component gallery");
  });

  it("keeps browser fallback, keyboard coverage, and client-data guardrails explicit", () => {
    const review = readFileSync(reviewPath, "utf-8");

    expect(review).toContain("Playwright fallback");
    expect(review).toContain("Desktop: 1280 x 840");
    expect(review).toContain("Mobile:  390 x 844");
    expect(review).toContain("Keyboard smoke");
    expect(review).toContain("console smoke");
    expect(review).toContain("synthetic data only");
    expect(review).toContain("CNPJ");
    expect(review).toContain("CPF");
  });

  it("documents residual risk for future richer interaction QA and remains indexed", () => {
    const review = readFileSync(reviewPath, "utf-8");
    const index = readFileSync(resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md"), "utf-8");

    for (const risk of ["dialogs", "editable forms", "mapping canvas", "assistive technology testing"]) {
      expect(review).toContain(risk);
    }

    expect(index).toContain("GUI_QA_ACCESSIBILITY_PASS_COMPLETION_REVIEW_OTM60.md");
  });
});
