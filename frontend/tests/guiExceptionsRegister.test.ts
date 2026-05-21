import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const guiDocsRoot = resolve("../docs/otm-workbench/gui");

describe("GUI exceptions register", () => {
  it("defines the required fields for custom GUI exceptions", () => {
    const register = readFileSync(resolve(guiDocsRoot, "GUI_EXCEPTIONS_REGISTER.md"), "utf-8");
    const requiredFields = [
      "ID:",
      "Status:",
      "Module or area:",
      "Pattern being bypassed:",
      "Backend contract impact:",
      "Accessibility impact:",
      "Responsive impact:",
      "Dark/light mode impact:",
      "Test coverage:",
      "Standardization or rollback plan:"
    ];

    for (const field of requiredFields) {
      expect(register).toContain(field);
    }
  });

  it("keeps architecture docs pointing at the exceptions register", () => {
    const architecture = readFileSync(resolve(guiDocsRoot, "GUI_FRONTEND_ARCHITECTURE.md"), "utf-8");

    expect(architecture).toContain("GUI_EXCEPTIONS_REGISTER.md");
  });
});
