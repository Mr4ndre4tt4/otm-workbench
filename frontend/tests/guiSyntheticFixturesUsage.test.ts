import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("GUI synthetic fixtures usage", () => {
  it("keeps shared UI kit tests on the synthetic fixture contract", () => {
    const componentTests = readFileSync(resolve("src/ui/components.test.tsx"), "utf-8");

    expect(componentTests).toContain("from \"../test/fixtures/gui\"");
    expect(componentTests).toContain("syntheticMetricItems");
    expect(componentTests).toContain("syntheticModuleObjects");
    expect(componentTests).toContain("syntheticDetailRows");
    expect(componentTests).toContain("syntheticArtifactItems");
    expect(componentTests).toContain("syntheticBlockers");
  });
});
