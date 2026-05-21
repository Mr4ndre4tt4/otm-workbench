import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const reviewPath = resolve(guiDocsRoot, "GUI_RATES_MVP_COMPLETION_REVIEW_OTM58.md");

describe("GUI Rates MVP completion review OTM-58", () => {
  it("records the delivered Rates GUI workflow and backend contracts", () => {
    const review = readFileSync(reviewPath, "utf-8");

    expect(review).toContain("OTM-58");
    expect(review).toContain("/rates backend-driven module route");
    expect(review).toContain("GET /api/v1/modules/rates/summary");
    expect(review).toContain("GET /api/v1/modules/rates/batches/{batch_id}");
    expect(review).toContain("available actions");
    expect(review).toContain("artifact download");
  });

  it("keeps backend ownership, client-data guardrails, and QA evidence explicit", () => {
    const review = readFileSync(reviewPath, "utf-8");

    expect(review).toContain("The GUI does not infer approval readiness");
    expect(review).toContain("GUI_RATES_VISUAL_QA_OTM78.md");
    expect(review).toContain("GUI_ACCESSIBILITY_QA_MATRIX.md");
    expect(review).toContain("keyboard smoke");
    expect(review).toContain("real client names");
    expect(review).toContain("CNPJ");
    expect(review).toContain("CPF");
    expect(review).toContain("CSV row payloads");
  });

  it("keeps the completion review discoverable from the GUI index", () => {
    const index = readFileSync(resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md"), "utf-8");

    expect(index).toContain("Module Completion Reviews");
    expect(index).toContain("GUI_RATES_MVP_COMPLETION_REVIEW_OTM58.md");
  });
});
