import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ContextSummary } from "./ContextSummary";

describe("ContextSummary", () => {
  it("renders selected backend context markers", () => {
    render(
      <ContextSummary
        context={{
          domain_name: "PUBLIC",
          environment_id: "env_1",
          profile_id: "profile_1",
          project_id: "project_1"
        }}
      />
    );

    expect(screen.getByLabelText("Active context")).toBeInTheDocument();
    expect(screen.getByText("Project selected")).toBeInTheDocument();
    expect(screen.getByText("Profile selected")).toBeInTheDocument();
    expect(screen.getByText("Environment selected")).toBeInTheDocument();
    expect(screen.getByText("PUBLIC")).toBeInTheDocument();
  });

  it("renders pending context markers and default domain", () => {
    render(<ContextSummary context={{}} />);

    expect(screen.getByText("No project selected")).toBeInTheDocument();
    expect(screen.getByText("Profile pending")).toBeInTheDocument();
    expect(screen.getByText("Environment pending")).toBeInTheDocument();
    expect(screen.getByText("PUBLIC")).toBeInTheDocument();
  });
});
