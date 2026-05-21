import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ReadinessPanel } from "./ReadinessPanel";

describe("ReadinessPanel", () => {
  it("renders ready project context counts", () => {
    render(
      <ReadinessPanel
        setupStatus={{
          active_context_selected: true,
          environment_count: 2,
          missing_requirements: [],
          profile_count: 1,
          status: "ready"
        }}
        status="ready"
      />
    );

    expect(screen.getByText("Project context ready")).toBeInTheDocument();
    expect(screen.getByText("1 profile(s), 2 environment(s)")).toBeInTheDocument();
  });

  it("renders missing context guidance", () => {
    render(<ReadinessPanel setupStatus={null} status="needs_context" />);

    expect(screen.getByText("Select an active project context")).toBeInTheDocument();
    expect(screen.getByText("The shell is waiting for project, profile, and environment context.")).toBeInTheDocument();
  });
});
