import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const srcRoot = resolve("src");
const stylesPath = resolve(srcRoot, "styles.css");

const expectedImports = [
  '@import "./ui/tokens/theme.css";',
  '@import "./ui/base.css";',
  '@import "./app/shell/shell.css";',
  '@import "./ui/components.css";',
  '@import "./ui/layouts.css";',
  '@import "./ui/tokens/density.css";',
  '@import "./ui/tokens/sidebar.css";',
  '@import "./ui/tokens/responsive.css";'
];

describe("CSS architecture", () => {
  it("keeps styles.css as the ordered GUI stylesheet entrypoint", () => {
    const content = readFileSync(stylesPath, "utf-8").trim();

    expect(content.split(/\r?\n/)).toEqual(expectedImports);
  });

  it("keeps imported CSS layers in their expected ownership paths", () => {
    for (const importLine of expectedImports) {
      const relativePath = importLine.match(/"(.+)"/)?.[1];
      expect(relativePath).toBeDefined();
      expect(existsSync(resolve(srcRoot, relativePath as string))).toBe(true);
    }
  });
});
