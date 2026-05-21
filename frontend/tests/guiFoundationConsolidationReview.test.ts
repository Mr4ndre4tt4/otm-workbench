import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const reviewPath = resolve(guiDocsRoot, "GUI_FOUNDATION_CONSOLIDATION_REVIEW.md");

describe("GUI foundation consolidation review", () => {
  it("records the current GUI foundation branch stack and review order", () => {
    const review = readFileSync(reviewPath, "utf-8");

    for (const branchName of [
      "codex/gui-synthetic-fixtures-foundation",
      "codex/gui-fixtures-ui-kit-tests",
      "codex/gui-internal-component-gallery-shell",
      "codex/gui-gallery-app-route-guardrail",
      "codex/gui-foundation-consolidation-review"
    ]) {
      expect(review).toContain(branchName);
    }

    expect(review).toContain("Synthetic fixtures and client-data guardrails");
    expect(review).toContain("Internal component gallery route");
    expect(review).toContain("App-level route guardrail");
  });

  it("keeps the consolidation review linked from GUI governance docs", () => {
    const index = readFileSync(resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md"), "utf-8");
    const checklist = readFileSync(resolve(guiDocsRoot, "GUI_IMPLEMENTATION_CHECKLIST.md"), "utf-8");

    expect(index).toContain("GUI_FOUNDATION_CONSOLIDATION_REVIEW.md");
    expect(checklist).toContain("GUI_FOUNDATION_CONSOLIDATION_REVIEW.md");
  });

  it("keeps follow-up Linear issues visible for the next GUI workstreams", () => {
    const review = readFileSync(reviewPath, "utf-8");

    for (const issueId of ["OTM-64", "OTM-65", "OTM-66", "OTM-67", "OTM-68"]) {
      expect(review).toContain(issueId);
    }
  });
});
