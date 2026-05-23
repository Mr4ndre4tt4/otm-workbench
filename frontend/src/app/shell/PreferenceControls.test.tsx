import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { updateUserPreferences } from "../../platform/hooks";
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
  afterEach(() => {
    vi.clearAllMocks();
  });

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

  it("prevents overlapping preference writes while one update is saving", async () => {
    let resolveUpdate: (value: UserPreferences) => void = () => undefined;
    vi.mocked(updateUserPreferences).mockImplementation(
      () =>
        new Promise<UserPreferences>((resolve) => {
          resolveUpdate = resolve;
        })
    );

    renderWithQueryClient({
      density: "comfortable",
      follow_system_theme: false,
      sidebar_mode: "expanded",
      theme_mode: "light"
    });

    await userEvent.click(screen.getByRole("button", { name: "Use compact density" }));

    expect(screen.getByRole("button", { name: "Collapse sidebar" })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "Collapse sidebar" }));
    expect(updateUserPreferences).toHaveBeenCalledTimes(1);
    expect(updateUserPreferences).toHaveBeenCalledWith("token", {
      density: "compact",
      follow_system_theme: false,
      sidebar_mode: "expanded",
      theme_mode: "light"
    });

    resolveUpdate({
      density: "compact",
      follow_system_theme: false,
      sidebar_mode: "expanded",
      theme_mode: "light"
    });

    await waitFor(() => expect(screen.getByRole("button", { name: "Collapse sidebar" })).toBeEnabled());
  });
});
