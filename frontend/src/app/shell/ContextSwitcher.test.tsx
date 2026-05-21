import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ContextSwitcher } from "./ContextSwitcher";

vi.mock("../../platform/hooks", () => ({
  updateActiveContext: vi.fn(),
  useEnvironments: () => ({ data: { items: [] }, isLoading: false }),
  useProfiles: () => ({ data: { items: [] }, isLoading: false }),
  useProjects: () => ({
    data: {
      items: [
        {
          id: "project_1",
          name: "Synthetic Project"
        }
      ]
    },
    isLoading: false
  })
}));

function renderWithQueryClient() {
  const queryClient = new QueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <ContextSwitcher token="token" />
    </QueryClientProvider>
  );
}

describe("ContextSwitcher", () => {
  it("renders backend-owned context selectors", () => {
    renderWithQueryClient();

    expect(screen.getByLabelText("Project")).toBeInTheDocument();
    expect(screen.getByLabelText("Profile")).toBeInTheDocument();
    expect(screen.getByLabelText("Environment")).toBeInTheDocument();
    expect(screen.getByLabelText("Domain")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apply context" })).toBeDisabled();
  });
});
