import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ComponentGalleryRoute } from "./ComponentGalleryRoute";
import { AuthProvider } from "../../platform/auth";

function renderGallery() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false }
    }
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ComponentGalleryRoute />
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe("ComponentGalleryRoute", () => {
  it("renders the internal gallery with synthetic shared component fixtures", () => {
    renderGallery();

    expect(screen.getByRole("heading", { name: "Component Gallery" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "WorkbenchShell" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "LoginPanel" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Context" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Preferences" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "ActionBar" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "StatusChip" })).toBeInTheDocument();
    expect(screen.getAllByText("Synthetic ready object")).toHaveLength(2);
    expect(screen.getByText("synthetic_export.csv")).toBeInTheDocument();
    expect(screen.getByText("SYNTHETIC_REQUIRED_FIELD")).toBeInTheDocument();
    expect(screen.getByText("SYNTHETIC_BLOCKER")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Primary command" })).toBeInTheDocument();
    for (const disabledAction of screen.getAllByRole("button", { name: "Export gallery snapshot" })) {
      expect(disabledAction).toBeDisabled();
    }
    expect(screen.getByLabelText("Gallery ContextSwitcher preview")).toBeInTheDocument();
    expect(screen.getByLabelText("Gallery status chip variants")).toBeInTheDocument();
  });
});
