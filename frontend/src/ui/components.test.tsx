import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Button, ModuleObjectList, SelectedObjectPanel } from "./components";

describe("ModuleObjectList", () => {
  it("renders selectable module objects with metadata and status", async () => {
    const selected: string[] = [];
    render(
      <ModuleObjectList
        items={[
          {
            id: "batch_1",
            meta: ["1 table", "12 rows", "0 issues"],
            status: "READY",
            subtitle: "ACCESSORIAL_ONLY",
            title: "Synthetic ready batch"
          }
        ]}
        onSelect={(id) => selected.push(id)}
        selectedId="batch_1"
      />
    );

    const row = screen.getByRole("button", { name: /Synthetic ready batch/ });
    expect(row).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("ACCESSORIAL_ONLY")).toBeInTheDocument();
    expect(screen.getByText("1 table")).toBeInTheDocument();
    expect(screen.getByText("12 rows")).toBeInTheDocument();
    expect(screen.getByText("0 issues")).toBeInTheDocument();
    expect(screen.getByText("READY")).toBeInTheDocument();

    row.click();

    expect(selected).toEqual(["batch_1"]);
  });

  it("renders an empty state without caller-owned list markup", () => {
    render(<ModuleObjectList emptyText="No objects available." items={[]} onSelect={() => undefined} selectedId={null} />);

    expect(screen.getByText("No objects available.")).toBeInTheDocument();
  });
});

describe("SelectedObjectPanel", () => {
  it("renders object identity, metadata, actions, and detail content", () => {
    render(
      <SelectedObjectPanel
        actions={<Button>Approve</Button>}
        emptyText="Select an object."
        fields={[
          { label: "Domain", value: "OTM1" },
          { label: "Tables", value: 2 }
        ]}
        status="READY"
        subtitle="ACCESSORIAL_ONLY"
        title="Synthetic ready batch"
      >
        <div>ACCESSORIAL_COST</div>
      </SelectedObjectPanel>
    );

    expect(screen.getByRole("heading", { name: "Selected object" })).toBeInTheDocument();
    expect(screen.getByText("READY")).toBeInTheDocument();
    expect(screen.getByText("Synthetic ready batch")).toBeInTheDocument();
    expect(screen.getByText("ACCESSORIAL_ONLY")).toBeInTheDocument();
    expect(screen.getByText("Domain")).toBeInTheDocument();
    expect(screen.getByText("OTM1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByText("ACCESSORIAL_COST")).toBeInTheDocument();
  });

  it("renders loading and empty states without caller-owned panel markup", () => {
    const { rerender } = render(
      <SelectedObjectPanel emptyText="Select an object." isLoading loadingText="Loading selected object..." status="PENDING" />
    );

    expect(screen.getByText("Loading selected object...")).toBeInTheDocument();

    rerender(<SelectedObjectPanel emptyText="Select an object." status="PENDING" />);

    expect(screen.getByText("Select an object.")).toBeInTheDocument();
  });
});
