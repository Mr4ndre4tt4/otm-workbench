import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { UserPreferences } from "../../platform/types";
import { PreferenceControls } from "./PreferenceControls";

vi.mock("../../platform/hooks", () => ({
  updateUserPreferences: vi.fn()
}));

function renderWithQueryClient(preferences: UserPreferences | undefined, token: string | null = "token") {
  const queryClient = new QueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <PreferenceControls preferences={preferences} token={token} />
    </QueryClientProvider>
  );
}

describe("PreferenceControls", () => {
  it("renders backend-owned preference controls with active state", () => {
    renderWithQueryClient({
      density: "comfortable",
      follow_system_theme: false,
      sidebar_mode: "expanded",
      theme_mode: "light"
    });

    expect(screen.getByLabelText("Workbench preferences")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Use light mode" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Use dark mode" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("button", { name: "Use compact density" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("button", { name: "Collapse sidebar" })).toHaveAttribute("aria-pressed", "false");
  });

  it("disables preference controls without a backend token", () => {
    renderWithQueryClient(undefined, null);

    expect(screen.getByRole("button", { name: "Use light mode" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Follow system theme" })).toBeDisabled();
  });
});
