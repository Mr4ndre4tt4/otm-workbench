import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

function readCss(path: string) {
  return readFileSync(resolve("src", path), "utf-8");
}

function selectors(css: string) {
  return Array.from(css.matchAll(/(^|\n)([^{}\n][^{]+)\{/g), (match) => match[2].trim());
}

describe("CSS layer ownership", () => {
  it("keeps component primitives out of shell and module layout selectors", () => {
    const componentSelectors = selectors(readCss("ui/components.css")).join("\n");
    const forbiddenFragments = [
      "app-shell",
      "sidebar",
      "brand-",
      "nav-",
      "topbar",
      "page-header",
      "module-",
      "metric",
      "panel",
      "activity-",
      "detail-",
      "table-",
      "artifact-",
      "blocker-",
      "context-",
      "readiness",
      "login-"
    ];

    for (const fragment of forbiddenFragments) {
      expect(componentSelectors).not.toContain(fragment);
    }
  });

  it("keeps density overrides scoped to the backend-owned density attribute", () => {
    for (const selector of selectors(readCss("ui/tokens/density.css"))) {
      expect(selector).toContain('.app-shell[data-density="compact"]');
    }
  });

  it("keeps collapsed sidebar overrides scoped to the backend-owned sidebar attribute", () => {
    for (const selector of selectors(readCss("ui/tokens/sidebar.css"))) {
      expect(selector).toContain('.app-shell[data-sidebar="collapsed"]');
    }
  });

  it("keeps responsive overrides inside the mobile breakpoint file", () => {
    const responsiveCss = readCss("ui/tokens/responsive.css").trim();

    expect(responsiveCss.startsWith("@media (max-width: 900px) {")).toBe(true);
    expect(responsiveCss.endsWith("}")).toBe(true);
    expect(responsiveCss.slice(1)).not.toContain("@media");
  });
});
