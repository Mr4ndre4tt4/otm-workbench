import { describe, expect, it } from "vitest";

import {
  syntheticAction,
  syntheticArtifactItems,
  syntheticBlockers,
  syntheticCompactDarkPreferences,
  syntheticDetailRows,
  syntheticMetricItems,
  syntheticModuleObjects,
  syntheticNavigationItems,
  syntheticUserPreferences
} from "./gui";

describe("synthetic GUI fixtures", () => {
  it("provides backend-shaped platform fixtures without real client data", () => {
    expect(syntheticNavigationItems.map((item) => item.id)).toEqual(["rates", "catalog", "evidence"]);
    expect(syntheticUserPreferences.theme_mode).toBe("light");
    expect(syntheticCompactDarkPreferences.sidebar_mode).toBe("collapsed");
    expect(syntheticAction({ disabled: true }).disabled).toBe(true);
  });

  it("provides shared UI kit fixtures for gallery and component checks", () => {
    expect(syntheticMetricItems).toHaveLength(3);
    expect(syntheticModuleObjects[1].title).toContain("deliberately long");
    expect(syntheticDetailRows.some((row) => row.status === "READ_ONLY")).toBe(true);
    expect(syntheticArtifactItems.some((item) => item.status === "ACTIVE")).toBe(true);
    expect(syntheticBlockers[0].codes).toEqual(["SYNTHETIC_BLOCKER"]);
  });
});
