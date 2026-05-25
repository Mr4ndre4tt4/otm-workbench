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
  MetricGrid,
  ModuleObjectList,
  ModuleWorkspaceLayout,
  ModuleWorkspaceSide,
  NextActionPanel,
  OperationalPanel,
  SelectedObjectPanel,
  StatePanel
} from "./components";
import {
  syntheticArtifactItems,
  syntheticBlockers,
  syntheticDetailRows,
  syntheticMetricItems,
  syntheticModuleObjects
} from "../test/fixtures/gui";

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

    expect(screen.getByRole("status")).toHaveClass("form-success");
    expect(screen.getByRole("status")).toHaveAttribute("aria-live", "polite");
    expect(screen.getByText("Context updated.")).toBeInTheDocument();

    rerender(<FeedbackMessage tone="error">Unable to sign in.</FeedbackMessage>);

    expect(screen.getByRole("alert")).toHaveClass("form-error");
    expect(screen.getByText("Unable to sign in.")).toBeInTheDocument();
  });
});

describe("MetricGrid", () => {
  it("renders shared metric cards from synthetic backend-shaped fixtures", () => {
    render(<MetricGrid ariaLabel="Synthetic metrics" items={syntheticMetricItems} />);

    expect(screen.getByLabelText("Synthetic metrics")).toBeInTheDocument();
    expect(screen.getByText("Ready")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("Blocked")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("EMPTY")).toBeInTheDocument();
  });
});

describe("DetailList", () => {
  it("renders detail rows with metadata and status", () => {
    const { container } = render(<DetailList ariaLabel="Selected batch fields" items={syntheticDetailRows} />);

    expect(screen.getByLabelText("Selected batch fields")).toBeInTheDocument();
    expect(screen.getByText("SYNTHETIC_REQUIRED_FIELD")).toBeInTheDocument();
    expect(screen.getByText("Required")).toBeInTheDocument();
    expect(screen.getByText("ACTIVE")).toBeInTheDocument();
    expect(container.querySelector(".table-list-main")).toBeInTheDocument();
    expect(container.querySelector(".table-list-meta")).toBeInTheDocument();
    expect(container.querySelector(".table-list-status")).toBeInTheDocument();
  });

  it("renders an empty state for missing detail rows", () => {
    render(<DetailList ariaLabel="Selected batch tables" emptyText="No rows found." items={[]} />);

    expect(screen.getByText("No rows found.")).toBeInTheDocument();
  });
});

describe("ArtifactList", () => {
  it("renders artifact identity, metadata, and action", () => {
    const { container } = render(
      <ArtifactList
        items={[
          {
            ...syntheticArtifactItems[0],
            action: <Button>Download</Button>
          }
        ]}
      />
    );

    expect(screen.getByText("synthetic_export.csv")).toBeInTheDocument();
    expect(screen.getByText("CSV export")).toBeInTheDocument();
    expect(screen.getByText("text/csv")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download" })).toBeInTheDocument();
    expect(container.querySelector(".artifact-list-main")).toBeInTheDocument();
    expect(container.querySelector(".artifact-list-meta")).toBeInTheDocument();
    expect(container.querySelector(".artifact-list-action")).toBeInTheDocument();
  });

  it("renders artifact status when no action is provided", () => {
    render(<ArtifactList items={[syntheticArtifactItems[1]]} />);

    expect(screen.getByText("ACTIVE")).toBeInTheDocument();
  });
});

describe("ModuleObjectList", () => {
  it("renders selectable module objects with metadata and status", async () => {
    const selected: string[] = [];
    render(
      <ModuleObjectList
        ariaLabel="Synthetic objects"
        items={syntheticModuleObjects}
        onSelect={(id) => selected.push(id)}
        selectedId={syntheticModuleObjects[0].id}
      />
    );

    const row = screen.getByRole("button", { name: /Synthetic ready object/ });
    expect(screen.getByLabelText("Synthetic objects")).toBeInTheDocument();
    expect(row).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Synthetic scenario")).toBeInTheDocument();
    expect(screen.getByText("3 table(s)")).toBeInTheDocument();
    expect(screen.getByText("42 row(s)")).toBeInTheDocument();
    expect(screen.getByText("0 issue(s)")).toBeInTheDocument();
    expect(screen.getByText("READY")).toBeInTheDocument();

    row.click();

    expect(selected).toEqual([syntheticModuleObjects[0].id]);
  });

  it("limits noisy object lists while preserving a selected object outside the first viewport", () => {
    const manyObjects = Array.from({ length: 14 }, (_, index) => ({
      ...syntheticModuleObjects[index % syntheticModuleObjects.length],
      id: `synthetic_object_${index}`,
      meta: [`${index} table(s)`, "42 row(s)", "0 issue(s)"],
      title: `Synthetic very long object ${index}`
    }));

    render(
      <ModuleObjectList
        ariaLabel="High volume synthetic objects"
        items={manyObjects}
        maxVisibleItems={5}
        onSelect={() => undefined}
        selectedId="synthetic_object_13"
      />
    );

    expect(screen.getAllByRole("button")).toHaveLength(5);
    expect(screen.getByRole("button", { name: /Synthetic very long object 13/ })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Showing 5 of 14; selected item pinned")).toBeInTheDocument();
    expect(screen.getByText("Synthetic very long object 13")).toHaveAttribute("title", "Synthetic very long object 13");
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

describe("ArtifactList density", () => {
  it("limits artifact rows and keeps long labels available through title attributes", () => {
    const manyArtifacts = Array.from({ length: 12 }, (_, index) => ({
      ...syntheticArtifactItems[index % syntheticArtifactItems.length],
      id: `synthetic_artifact_${index}`,
      subtitle: `Synthetic generated artifact subtitle ${index}`,
      title: `synthetic_generated_artifact_with_long_identifier_${index}.json`
    }));

    render(<ArtifactList items={manyArtifacts} maxVisibleItems={4} />);

    expect(screen.getAllByText(/synthetic_generated_artifact_with_long_identifier_/)).toHaveLength(4);
    expect(screen.getByText("Showing 4 of 12")).toBeInTheDocument();
    expect(screen.getByText("synthetic_generated_artifact_with_long_identifier_0.json")).toHaveAttribute(
      "title",
      "synthetic_generated_artifact_with_long_identifier_0.json"
    );
  });
});

describe("BlockerPanel", () => {
  it("renders blockers with backend codes and messages", () => {
    render(<BlockerPanel emptyText="No blockers." items={syntheticBlockers} title="Open blockers" />);

    expect(screen.getByRole("heading", { name: "Open blockers" })).toBeInTheDocument();
    expect(screen.getByText("BLOCKED")).toBeInTheDocument();
    expect(screen.getByText("SYNTHETIC_BLOCKER")).toBeInTheDocument();
    expect(screen.getByText("Synthetic blocker message for layout and status checks.")).toBeInTheDocument();
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

describe("NextActionPanel", () => {
  it("renders the selected object, current stage, and backend-recommended action", () => {
    render(
      <NextActionPanel
        action={{
          description: "Backend action is ready for the selected template.",
          label: "Build workbook",
          status: "NEXT"
        }}
        ariaLabel="Data Factory next action"
        context={["Template", "REGIONS_BASIC"]}
        objectLabel="Template"
        objectValue="REGIONS_BASIC"
        stageLabel="Workbook"
        title="Next action"
      />
    );

    expect(screen.getByLabelText("Data Factory next action")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Next action" })).toBeInTheDocument();
    expect(screen.getAllByText("Template")).toHaveLength(2);
    expect(screen.getAllByText("REGIONS_BASIC")).toHaveLength(2);
    expect(screen.getByText("Workbook")).toBeInTheDocument();
    expect(screen.getByText("Build workbook")).toBeInTheDocument();
    expect(screen.getByText("NEXT")).toBeInTheDocument();
    expect(screen.getByText("Backend action is ready for the selected template.")).toBeInTheDocument();
  });

  it("renders disabled guidance and blockers without caller-owned panel markup", () => {
    render(
      <NextActionPanel
        action={{
          disabled: true,
          disabledReason: "PUBLISHED_TEMPLATE_REQUIRED",
          label: "Build workbook",
          status: "BLOCKED"
        }}
        ariaLabel="Blocked next action"
        blockers={["PUBLISHED_TEMPLATE_REQUIRED"]}
        objectLabel="Template"
        objectValue="LOCATIONS_DYNAMIC_UI"
        stageLabel="Workbook"
        title="Next action"
      />
    );

    expect(screen.getByText("BLOCKED")).toBeInTheDocument();
    expect(screen.getAllByText("PUBLISHED_TEMPLATE_REQUIRED")).toHaveLength(2);
    expect(screen.getByText("Build workbook")).toBeInTheDocument();
  });
});

describe("SelectedObjectPanel", () => {
  it("renders object identity, metadata, actions, and detail content", () => {
    const selectedObject = syntheticModuleObjects[0];

    render(
      <SelectedObjectPanel
        actions={<Button>Approve</Button>}
        ariaLabel="Selected synthetic object"
        emptyText="Select an object."
        fields={[
          { label: "Status", value: selectedObject.status },
          { label: "Rows", value: "42" }
        ]}
        status={selectedObject.status}
        subtitle={selectedObject.subtitle}
        title={selectedObject.title}
      >
        <DetailList ariaLabel="Selected synthetic details" items={syntheticDetailRows} />
      </SelectedObjectPanel>
    );

    expect(screen.getByRole("heading", { name: "Selected object" })).toBeInTheDocument();
    expect(screen.getByLabelText("Selected synthetic object")).toBeInTheDocument();
    expect(screen.getAllByText("READY")).toHaveLength(2);
    expect(screen.getByText("Synthetic ready object")).toBeInTheDocument();
    expect(screen.getByText("Synthetic scenario")).toBeInTheDocument();
    expect(screen.getByText("Rows")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByText("SYNTHETIC_REQUIRED_FIELD")).toBeInTheDocument();
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
