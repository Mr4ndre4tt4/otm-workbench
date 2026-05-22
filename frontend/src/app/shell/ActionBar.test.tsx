import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { AvailableAction } from "../../platform/types";
import { ActionBar } from "./ActionBar";

function action(overrides: Partial<AvailableAction>): AvailableAction {
  return {
    disabled: false,
    disabled_reason: null,
    href: "/api/v1/test/actions/run",
    icon_key: "play",
    key: "run",
    label: "Run",
    method: "POST",
    requires_confirmation: false,
    variant: "secondary",
    ...overrides
  };
}

describe("ActionBar", () => {
  it("renders backend-provided actions and dispatches the selected action", async () => {
    const selected: AvailableAction[] = [];
    const runAction = action({ key: "validate", label: "Validate", variant: "primary" });

    render(<ActionBar actions={[runAction]} onAction={(candidate) => selected.push(candidate)} />);

    await userEvent.click(screen.getByRole("button", { name: "Validate" }));

    expect(selected).toEqual([runAction]);
  });

  it("renders action icons from backend-owned icon keys", () => {
    render(<ActionBar actions={[action({ icon_key: "download", key: "download", label: "Download" })]} />);

    expect(screen.getByTestId("action-icon-download")).toHaveAttribute("data-icon-key", "download");
    expect(screen.getByRole("button", { name: "Download" })).toBeInTheDocument();
  });

  it("keeps disabled and running action states centralized", () => {
    render(
      <ActionBar
        actions={[
          action({ disabled: true, disabled_reason: "Backend permission denied.", key: "approve", label: "Approve" }),
          action({ key: "validate", label: "Validate" })
        ]}
        runningActionKey="validate"
      />
    );

    expect(screen.getByRole("button", { name: "Approve" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Approve" })).toHaveAttribute("title", "Backend permission denied.");
    expect(screen.getByRole("button", { name: "Running..." })).toBeDisabled();
  });
});
