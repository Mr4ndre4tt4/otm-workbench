import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");
const specsRoot = resolve("../docs/superpowers/specs");
const contractPath = resolve(guiDocsRoot, "GUI_MODULE_EXPERIENCE_ARCHITECTURE.md");

describe("GUI module experience architecture contract", () => {
  it("keeps the module experience architecture discoverable", () => {
    const index = readFileSync(resolve(guiDocsRoot, "GUI_CONTRACT_INDEX.md"), "utf-8");
    const checklist = readFileSync(resolve(guiDocsRoot, "GUI_IMPLEMENTATION_CHECKLIST.md"), "utf-8");
    const decisions = readFileSync(resolve(guiDocsRoot, "GUI_DECISIONS_LOG.md"), "utf-8");
    const plan = readFileSync(resolve(guiDocsRoot, "GUI_MVP1_PLAN.md"), "utf-8");

    expect(index).toContain("GUI_MODULE_EXPERIENCE_ARCHITECTURE.md");
    expect(index).toContain("GUI_MODULE_EXPERIENCE_ROADMAP.md");
    expect(index).toContain("GUI_MODULE_COMPLETION_ACCEPTANCE_CONTRACT.md");
    expect(checklist).toContain("GUI_MODULE_EXPERIENCE_ARCHITECTURE.md");
    expect(checklist).toContain("GUI_MODULE_COMPLETION_ACCEPTANCE_CONTRACT.md");
    expect(decisions).toContain("GUI-DEC-008");
    expect(decisions).toContain("GUI-DEC-009");
    expect(plan).toContain("GUI_MODULE_EXPERIENCE_ARCHITECTURE.md");
    expect(plan).toContain("GUI_MODULE_EXPERIENCE_ROADMAP.md");
  });

  it("requires one primary module story and backend-owned product truth", () => {
    const contract = readFileSync(contractPath, "utf-8");

    expect(contract).toContain("Every module screen needs one primary story");
    expect(contract).toContain("Do not stack unrelated authoring forms one below another");
    expect(contract).toContain("Backend remains authoritative");
    expect(contract).toContain("Frontend may disable a submit button for missing local form input");
    expect(contract).toContain("not infer lifecycle eligibility, permission eligibility");
  });

  it("keeps the module roadmap aligned with primary experience patterns", () => {
    const roadmap = readFileSync(resolve(guiDocsRoot, "GUI_MODULE_EXPERIENCE_ROADMAP.md"), "utf-8");

    expect(roadmap).toContain("Load Plan / Cutover");
    expect(roadmap).toContain("review queue + staged workflow");
    expect(roadmap).toContain("Master Data / Data Factory");
    expect(roadmap).toContain("staged workflow + object detail");
    expect(roadmap).toContain("Next implementation target");
    expect(roadmap).toContain("Order Release Generator functional workflow");
    expect(roadmap).toContain("First functional slice done");
    expect(roadmap).toContain("OTM-115 owns template factory");
    expect(roadmap).toContain("2026-05-22-master-data-dynamic-template-factory-design.md");
  });

  it("requires the cross-module completion acceptance contract", () => {
    const completion = readFileSync(resolve(guiDocsRoot, "GUI_MODULE_COMPLETION_ACCEPTANCE_CONTRACT.md"), "utf-8");
    const qaJourneys = readFileSync(resolve(guiDocsRoot, "GUI_FUNCTIONAL_QA_JOURNEYS.md"), "utf-8");

    expect(completion).toContain("First functional slice done");
    expect(completion).toContain("MVP workflow done");
    expect(completion).toContain("Module complete");
    expect(completion).toContain("Data dictionary and official-source validation");
    expect(completion).toContain("Import/export artifact parity");
    expect(completion).toContain("Positive, negative, and out-of-order QA");
    expect(qaJourneys).toContain("does not by itself prove module completion");
  });

  it("keeps the Master Data dynamic template factory backend-first", () => {
    const spec = readFileSync(
      resolve(specsRoot, "2026-05-22-master-data-dynamic-template-factory-design.md"),
      "utf-8",
    );

    expect(spec).toContain("backend-owned dynamic");
    expect(spec).toContain("master-data-template-definition/v2");
    expect(spec).toContain("FIXED_VALUE");
    expect(spec).toContain("one user field mapped to two target columns");
    expect(spec).toContain("local Data Dictionary/Catalog");
    expect(spec).toContain("Do not infer Oracle functional behavior");
  });
});
