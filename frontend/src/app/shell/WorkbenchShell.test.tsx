import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { updateUserPreferences } from "../../platform/hooks";
import type { NavigationItem, UserPreferences } from "../../platform/types";
import { WorkbenchShell } from "./WorkbenchShell";

vi.mock("../../platform/hooks", () => ({
  updateUserPreferences: vi.fn()
}));

const navigationItems: NavigationItem[] = [
  {
    id: "rates",
    label: "Rates",
    label_key: "module.rates.label",
    description: "Rates workspace",
    path: "/rates",
    status: "ready",
    icon_key: "rates",
    icon_family: "iconly",
    icon_variant: "regular",
    icon_style: "broken",
    icon_name: "Chart",
    icon_light_ref: {},
    icon_dark_ref: {}
  }
];

const preferences: UserPreferences = {
  density: "compact",
  follow_system_theme: false,
  sidebar_mode: "collapsed",
  theme_mode: "dark"
};

function renderShell({ isAuthenticated = true }: { isAuthenticated?: boolean } = {}) {
  const queryClient = new QueryClient();
  const onSignOut = vi.fn();
  const view = render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <WorkbenchShell
          currentPath="/rates"
          isAuthenticated={isAuthenticated}
          navigationItems={navigationItems}
          onSignOut={onSignOut}
          preferences={preferences}
          sidebarMode={preferences.sidebar_mode}
          token={isAuthenticated ? "session_token" : null}
        >
          <section>Route content</section>
        </WorkbenchShell>
      </MemoryRouter>
    </QueryClientProvider>
  );
  return { onSignOut, view };
}

describe("WorkbenchShell", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders the shared shell frame with backend-owned preference attributes", () => {
    const { view } = renderShell();

    expect(view.container.querySelector(".app-shell")).toHaveAttribute("data-theme", "dark");
    expect(view.container.querySelector(".app-shell")).toHaveAttribute("data-density", "compact");
    expect(view.container.querySelector(".app-shell")).toHaveAttribute("data-sidebar", "collapsed");
    expect(screen.getByText("Workbench")).toBeInTheDocument();
    expect(screen.getByText("Backend-owned contracts")).toBeInTheDocument();
    expect(screen.getByText("Route content")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Rates/ })).toHaveAttribute("href", "/rates");
    expect(screen.getByRole("button", { name: "Expand sidebar" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Collapse sidebar" })).not.toBeInTheDocument();
  });

  it("keeps sign out visible only for authenticated sessions", () => {
    renderShell({ isAuthenticated: false });

    expect(screen.queryByRole("button", { name: "Sign out" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Use light mode" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Expand sidebar" })).toBeDisabled();
  });

  it("persists sidebar collapse changes from the sidebar control", async () => {
    vi.mocked(updateUserPreferences).mockResolvedValue({
      ...preferences,
      sidebar_mode: "expanded"
    });
    renderShell();

    await userEvent.click(screen.getByRole("button", { name: "Expand sidebar" }));

    expect(updateUserPreferences).toHaveBeenCalledWith("session_token", {
      ...preferences,
      sidebar_mode: "expanded"
    });
  });
});
