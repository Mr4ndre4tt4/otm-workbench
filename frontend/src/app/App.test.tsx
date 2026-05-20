import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false }
  }
});

function renderApp() {
  return render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  );
}

describe("App shell", () => {
  it("renders the workbench shell identity before API data resolves", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise(() => undefined))
    );

    renderApp();

    expect(screen.getByText("Workbench")).toBeInTheDocument();
    expect(screen.getByText("Backend-owned contracts")).toBeInTheDocument();
    expect(screen.getByText("Loading Project Cockpit...")).toBeInTheDocument();
  });
});
