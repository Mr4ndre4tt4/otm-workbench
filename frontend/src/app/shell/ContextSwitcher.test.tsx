import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ContextSwitcher } from "./ContextSwitcher";
import { updateActiveContext } from "../../platform/hooks";

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

  it("clears stale submit feedback when the context draft changes", async () => {
    vi.mocked(updateActiveContext).mockResolvedValue({
      project_id: "project_1",
      profile_id: null,
      environment_id: null,
      domain_name: "OTM1",
      allowed_domains: ["PUBLIC", "OTM1"],
      can_view_all_domains: false
    });
    renderWithQueryClient();

    await userEvent.selectOptions(screen.getByLabelText("Project"), "project_1");
    await userEvent.type(screen.getByLabelText("Domain"), "otm1");
    await userEvent.click(screen.getByRole("button", { name: "Apply context" }));

    expect(await screen.findByText("Context updated.")).toBeInTheDocument();

    await userEvent.clear(screen.getByLabelText("Domain"));
    await userEvent.type(screen.getByLabelText("Domain"), "otm2");

    expect(screen.queryByText("Context updated.")).not.toBeInTheDocument();
  });
});
