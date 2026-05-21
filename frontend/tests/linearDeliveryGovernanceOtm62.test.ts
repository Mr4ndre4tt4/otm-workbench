import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const docsRoot = resolve("../docs/otm-workbench");
const governancePath = resolve(docsRoot, "governance/LINEAR_DELIVERY_GOVERNANCE_OTM62.md");

describe("Linear delivery governance OTM-62", () => {
  it("defines Linear as a visibility layer with repo docs as durable detail", () => {
    const governance = readFileSync(governancePath, "utf-8");

    expect(governance).toContain("OTM-62");
    expect(governance).toContain("Linear is the project visibility layer");
    expect(governance).toContain("Repo docs remain the source of durable technical detail");
    expect(governance).toContain("one Linear issue per coherent delivery slice");
  });

  it("documents issue creation, status, comment, PR, and client-data rules", () => {
    const governance = readFileSync(governancePath, "utf-8");

    for (const section of [
      "When To Create An Issue",
      "Required Issue Fields",
      "Status Rules",
      "Comment Cadence",
      "PR Update Rule",
      "Client Data Rule"
    ]) {
      expect(governance).toContain(section);
    }

    expect(governance).toContain("synthetic/client-safe");
    expect(governance).toContain("CNPJ");
    expect(governance).toContain("CPF");
  });

  it("records the current GUI cleanup trail and is linked from docs README", () => {
    const governance = readFileSync(governancePath, "utf-8");
    const readme = readFileSync(resolve(docsRoot, "README.md"), "utf-8");

    for (const issueId of ["OTM-58", "OTM-59", "OTM-60", "OTM-77", "OTM-78", "OTM-79", "OTM-80", "OTM-84"]) {
      expect(governance).toContain(issueId);
    }

    expect(readme).toContain("governance/");
    expect(readme).toContain("LINEAR_DELIVERY_GOVERNANCE_OTM62.md");
  });
});
