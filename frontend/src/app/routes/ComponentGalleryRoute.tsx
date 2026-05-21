import { PageHeader } from "../shell";
import {
  ArtifactList,
  BlockerPanel,
  Button,
  DetailList,
  FeedbackMessage,
  IconButton,
  MetricGrid,
  ModuleObjectList,
  ModuleWorkspaceLayout,
  OperationalPanel,
  SelectedObjectPanel,
  StatePanel
} from "../../ui/components";
import {
  syntheticAction,
  syntheticArtifactItems,
  syntheticBlockers,
  syntheticDetailRows,
  syntheticMetricItems,
  syntheticModuleObjects
} from "../../test/fixtures/gui";

const galleryActions = [
  syntheticAction({ key: "gallery_refresh", label: "Refresh examples", variant: "secondary" }),
  syntheticAction({
    disabled: true,
    disabled_reason: "Synthetic disabled action",
    key: "gallery_export",
    label: "Export gallery snapshot",
    variant: "primary"
  })
];

export function ComponentGalleryRoute() {
  const selectedObject = syntheticModuleObjects[0];

  return (
    <>
      <PageHeader
        actions={galleryActions}
        description="Internal synthetic component gallery for shared GUI patterns. This route is not published through backend navigation."
        label="Internal GUI"
        title="Component Gallery"
      />

      <MetricGrid ariaLabel="Synthetic gallery metrics" items={syntheticMetricItems} />

      <ModuleWorkspaceLayout
        ariaLabel="Synthetic component gallery workspace"
        side={
          <SelectedObjectPanel
            actions={<Button variant="primary">Review synthetic object</Button>}
            ariaLabel="Gallery selected synthetic object"
            emptyText="Select a synthetic object."
            fields={[
              { label: "Status", value: selectedObject.status },
              { label: "Rows", value: "42" }
            ]}
            status={selectedObject.status}
            subtitle={selectedObject.subtitle}
            title={selectedObject.title}
          >
            <DetailList ariaLabel="Gallery selected object details" items={syntheticDetailRows} />
          </SelectedObjectPanel>
        }
        status="ACTIVE"
        title="Object workspace"
      >
        <ModuleObjectList
          ariaLabel="Gallery synthetic object list"
          items={syntheticModuleObjects}
          onSelect={() => undefined}
          selectedId={selectedObject.id}
        />
      </ModuleWorkspaceLayout>

      <section className="activity-layout" aria-label="Gallery operational examples">
        <OperationalPanel
          ariaLabel="Gallery artifacts"
          emptyText="No synthetic artifacts."
          hasItems
          status="ACTIVE"
          title="Artifacts"
        >
          <ArtifactList
            items={[
              { ...syntheticArtifactItems[0], action: <Button>Download</Button> },
              syntheticArtifactItems[1]
            ]}
          />
        </OperationalPanel>

        <OperationalPanel
          ariaLabel="Gallery state and feedback"
          emptyText="No synthetic states."
          hasItems
          status="READY"
          title="States"
        >
          <div className="detail-stack">
            <FeedbackMessage tone="success">Synthetic success feedback.</FeedbackMessage>
            <FeedbackMessage tone="error">Synthetic error feedback.</FeedbackMessage>
            <StatePanel>Loading synthetic component state...</StatePanel>
            <div className="detail-actions" aria-label="Gallery icon commands">
              <IconButton label="Synthetic icon action">S</IconButton>
              <Button>Secondary command</Button>
              <Button variant="primary">Primary command</Button>
            </div>
          </div>
        </OperationalPanel>
      </section>

      <BlockerPanel emptyText="No synthetic blockers." items={syntheticBlockers} title="Blockers" />
    </>
  );
}
