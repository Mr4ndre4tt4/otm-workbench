import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  ActivityRow,
  ArtifactList,
  BlockerPanel,
  Button,
  DetailList,
  FeedbackMessage,
  IconButton,
  ModuleObjectList,
  ModuleWorkspaceLayout,
  ModuleWorkspaceSide,
  OperationalPanel,
  SelectedObjectPanel,
  StatePanel
} from "./components";

describe("Button patterns", () => {
  it("renders command buttons through the shared Button component", () => {
    render(
      <>
        <Button>Secondary action</Button>
        <Button variant="primary">Primary action</Button>
      </>
    );

    expect(screen.getByRole("button", { name: "Secondary action" })).toHaveClass("button-secondary");
    expect(screen.getByRole("button", { name: "Primary action" })).toHaveClass("button-primary");
  });

  it("renders icon-only commands with accessible labels", () => {
    render(<IconButton label="Use dark mode">D</IconButton>);

    expect(screen.getByRole("button", { name: "Use dark mode" })).toHaveAttribute("title", "Use dark mode");
  });
});

describe("StatePanel", () => {
  it("renders shared loading and error states", () => {
    const { container, rerender } = render(<StatePanel>Loading Rates Studio...</StatePanel>);

    expect(screen.getByText("Loading Rates Studio...")).toBeInTheDocument();
    expect(container.querySelector("svg")).not.toBeInTheDocument();

    rerender(<StatePanel tone="error">Rates Studio summary is unavailable.</StatePanel>);

    expect(screen.getByText("Rates Studio summary is unavailable.")).toBeInTheDocument();
    expect(container.querySelector("svg")).toBeInTheDocument();
  });
});

describe("FeedbackMessage", () => {
  it("renders shared success and error feedback styles", () => {
    const { rerender } = render(<FeedbackMessage tone="success">Context updated.</FeedbackMessage>);

    expect(screen.getByText("Context updated.")).toHaveClass("form-success");

    rerender(<FeedbackMessage tone="error">Unable to sign in.</FeedbackMessage>);

    expect(screen.getByText("Unable to sign in.")).toHaveClass("form-error");
  });
});

describe("DetailList", () => {
  it("renders detail rows with metadata and status", () => {
    render(
      <DetailList
        ariaLabel="Selected batch tables"
        items={[
          {
            id: "table_1",
            meta: ["1 row"],
            status: "VALID",
            title: "ACCESSORIAL_COST"
          }
        ]}
      />
    );

    expect(screen.getByLabelText("Selected batch tables")).toBeInTheDocument();
    expect(screen.getByText("ACCESSORIAL_COST")).toBeInTheDocument();
    expect(screen.getByText("1 row")).toBeInTheDocument();
    expect(screen.getByText("VALID")).toBeInTheDocument();
  });

  it("renders an empty state for missing detail rows", () => {
    render(<DetailList ariaLabel="Selected batch tables" emptyText="No rows found." items={[]} />);

    expect(screen.getByText("No rows found.")).toBeInTheDocument();
  });
});

describe("ArtifactList", () => {
  it("renders artifact identity, metadata, and action", () => {
    render(
      <ArtifactList
        items={[
          {
            action: <Button>Download</Button>,
            id: "artifact_1",
            meta: ["text/csv", "128 bytes"],
            subtitle: "CSV export",
            title: "rates.csv"
          }
        ]}
      />
    );

    expect(screen.getByText("rates.csv")).toBeInTheDocument();
    expect(screen.getByText("CSV export")).toBeInTheDocument();
    expect(screen.getByText("text/csv")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download" })).toBeInTheDocument();
  });

  it("renders artifact status when no action is provided", () => {
    render(
      <ArtifactList
        items={[
          {
            id: "evidence_1",
            meta: ["Artifact linked", "Client safe"],
            status: "ACTIVE",
            subtitle: "Internal",
            title: "Validation evidence"
          }
        ]}
      />
    );

    expect(screen.getByText("ACTIVE")).toBeInTheDocument();
  });
});

describe("ModuleObjectList", () => {
  it("renders selectable module objects with metadata and status", async () => {
    const selected: string[] = [];
    render(
      <ModuleObjectList
        ariaLabel="Rate batches"
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
    expect(screen.getByLabelText("Rate batches")).toBeInTheDocument();
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
    render(
      <ModuleObjectList
        ariaLabel="Module objects"
        emptyText="No objects available."
        items={[]}
        onSelect={() => undefined}
        selectedId={null}
      />
    );

    expect(screen.getByText("No objects available.")).toBeInTheDocument();
  });
});

describe("BlockerPanel", () => {
  it("renders blockers with backend codes and messages", () => {
    render(
      <BlockerPanel
        emptyText="No blockers."
        items={[{ codes: ["RATE_GEO_MISSING"], id: "blocker_1", message: "Missing geography reference." }]}
        title="Open blockers"
      />
    );

    expect(screen.getByRole("heading", { name: "Open blockers" })).toBeInTheDocument();
    expect(screen.getByText("BLOCKED")).toBeInTheDocument();
    expect(screen.getByText("RATE_GEO_MISSING")).toBeInTheDocument();
    expect(screen.getByText("Missing geography reference.")).toBeInTheDocument();
  });

  it("renders a ready empty state when no blockers exist", () => {
    render(<BlockerPanel emptyText="No blockers." items={[]} title="Open blockers" />);

    expect(screen.getByText("READY")).toBeInTheDocument();
    expect(screen.getByText("No blockers.")).toBeInTheDocument();
  });
});

describe("ModuleWorkspaceLayout", () => {
  it("renders the shared module workspace grid, primary panel, and side panel", () => {
    render(
      <ModuleWorkspaceLayout
        ariaLabel="Rates Studio workspace"
        side={
          <ModuleWorkspaceSide title="Expected panels">
            <ul>
              <li>Available actions from backend</li>
            </ul>
          </ModuleWorkspaceSide>
        }
        status="ACTIVE"
        title="Recent rate batches"
      >
        <div>Rate batch list</div>
      </ModuleWorkspaceLayout>
    );

    expect(screen.getByLabelText("Rates Studio workspace")).toHaveClass("module-template");
    expect(screen.getByRole("heading", { name: "Recent rate batches" })).toBeInTheDocument();
    expect(screen.getByText("ACTIVE")).toBeInTheDocument();
    expect(screen.getByText("Rate batch list")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Expected panels" })).toBeInTheDocument();
    expect(screen.getByText("Available actions from backend")).toBeInTheDocument();
  });
});

describe("SelectedObjectPanel", () => {
  it("renders object identity, metadata, actions, and detail content", () => {
    render(
      <SelectedObjectPanel
        actions={<Button>Approve</Button>}
        ariaLabel="Selected rate batch"
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
    expect(screen.getByLabelText("Selected rate batch")).toBeInTheDocument();
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
      <SelectedObjectPanel
        ariaLabel="Selected object"
        emptyText="Select an object."
        isLoading
        loadingText="Loading selected object..."
        status="PENDING"
      />
    );

    expect(screen.getByText("Loading selected object...")).toBeInTheDocument();

    rerender(<SelectedObjectPanel ariaLabel="Selected object" emptyText="Select an object." status="PENDING" />);

    expect(screen.getByText("Select an object.")).toBeInTheDocument();
  });
});

describe("OperationalPanel", () => {
  it("renders accessible operational content and status", () => {
    render(
      <OperationalPanel ariaLabel="Recent jobs" emptyText="No recent jobs." hasItems status="ACTIVE" title="Recent jobs">
        <div>load_package.build</div>
      </OperationalPanel>
    );

    expect(screen.getByLabelText("Recent jobs")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Recent jobs" })).toBeInTheDocument();
    expect(screen.getByText("ACTIVE")).toBeInTheDocument();
    expect(screen.getByText("load_package.build")).toBeInTheDocument();
  });

  it("renders loading and empty states without caller-owned panel markup", () => {
    const { rerender } = render(
      <OperationalPanel
        ariaLabel="Rate batch evidence"
        emptyText="No evidence registered."
        hasItems={false}
        isLoading
        loadingText="Loading evidence..."
        status="EMPTY"
        title="Evidence"
      />
    );

    expect(screen.getByText("Loading evidence...")).toBeInTheDocument();

    rerender(
      <OperationalPanel
        ariaLabel="Rate batch evidence"
        emptyText="No evidence registered."
        hasItems={false}
        status="EMPTY"
        title="Evidence"
      />
    );

    expect(screen.getByText("No evidence registered.")).toBeInTheDocument();
  });
});

describe("ActivityRow", () => {
  it("renders activity identity, source, and backend status", () => {
    render(<ActivityRow status="SUCCEEDED" subtitle="rates" title="load_package.build" />);

    expect(screen.getByText("load_package.build")).toBeInTheDocument();
    expect(screen.getByText("rates")).toBeInTheDocument();
    expect(screen.getByText("SUCCEEDED")).toBeInTheDocument();
  });
});
