import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ComponentGalleryRoute } from "./ComponentGalleryRoute";

describe("ComponentGalleryRoute", () => {
  it("renders the internal gallery with synthetic shared component fixtures", () => {
    render(<ComponentGalleryRoute />);

    expect(screen.getByRole("heading", { name: "Component Gallery" })).toBeInTheDocument();
    expect(screen.getAllByText("Synthetic ready object")).toHaveLength(2);
    expect(screen.getByText("synthetic_export.csv")).toBeInTheDocument();
    expect(screen.getByText("SYNTHETIC_REQUIRED_FIELD")).toBeInTheDocument();
    expect(screen.getByText("SYNTHETIC_BLOCKER")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Primary command" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Export gallery snapshot" })).toBeDisabled();
  });
});
