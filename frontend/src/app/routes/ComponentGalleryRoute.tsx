import { ActionBar, ContextSummary, LoginPanel, PageHeader, PreferenceControls, ReadinessPanel } from "../shell";
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
  StatePanel,
  StatusChip
} from "../../ui/components";
import {
  syntheticAction,
  syntheticArtifactItems,
  syntheticBlockers,
  syntheticCompactDarkPreferences,
  syntheticDetailRows,
  syntheticMetricItems,
  syntheticModuleObjects,
  syntheticNavigationItems,
  syntheticUserPreferences
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

const statusVariants = ["READY", "BLOCKED", "ERROR", "READ_ONLY", "PENDING", "ACTIVE"];

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

      <section className="activity-layout" aria-label="Gallery shell examples">
        <OperationalPanel
          ariaLabel="Gallery shell frame"
          emptyText="No shell preview."
          hasItems
          status="READY"
          title="WorkbenchShell"
        >
          <div className="detail-stack">
            <div className="brand-lockup">
              <span className="brand-mark">OTM</span>
              <div className="brand-text">
                <strong>Workbench</strong>
                <span>Implementation cockpit</span>
              </div>
            </div>
            <DetailList
              ariaLabel="Gallery shell attributes"
              items={[
                {
                  id: "gallery_shell_theme",
                  meta: ["Light default", syntheticUserPreferences.theme_mode],
                  status: "READY",
                  title: "Theme"
                },
                {
                  id: "gallery_shell_sidebar",
                  meta: ["Desktop-ready", syntheticUserPreferences.sidebar_mode],
                  status: "READY",
                  title: "Sidebar"
                },
                {
                  id: "gallery_shell_navigation",
                  meta: [syntheticNavigationItems.length, "backend navigation item(s)"],
                  status: "ACTIVE",
                  title: "Navigation"
                }
              ]}
            />
          </div>
        </OperationalPanel>

        <OperationalPanel
          ariaLabel="Gallery login panel"
          className="gallery-auth-preview"
          emptyText="No login panel preview."
          hasItems
          status="READY"
          title="LoginPanel"
        >
          <LoginPanel />
        </OperationalPanel>
      </section>

      <section className="activity-layout" aria-label="Gallery context and preference examples">
        <OperationalPanel
          ariaLabel="Gallery context states"
          emptyText="No context preview."
          hasItems
          status="ACTIVE"
          title="Context"
        >
          <div className="detail-stack">
            <ContextSummary
              context={{
                domain_name: "SYN_DOMAIN",
                environment_id: "synthetic_environment",
                profile_id: "synthetic_profile",
                project_id: "synthetic_project"
              }}
            />
            <form className="gallery-selector-preview" aria-label="Gallery ContextSwitcher preview">
              <label>
                <span>Project</span>
                <select defaultValue="synthetic_project" disabled>
                  <option value="synthetic_project">Project QA</option>
                </select>
              </label>
              <label>
                <span>Profile</span>
                <select defaultValue="synthetic_profile" disabled>
                  <option value="synthetic_profile">Default</option>
                </select>
              </label>
              <label>
                <span>Environment</span>
                <select defaultValue="synthetic_environment" disabled>
                  <option value="synthetic_environment">DEV</option>
                </select>
              </label>
              <label>
                <span>Domain</span>
                <input readOnly value="SYN_DOMAIN" />
              </label>
              <Button disabled variant="primary">
                Apply context
              </Button>
            </form>
            <ReadinessPanel
              setupStatus={{
                active_context_selected: true,
                environment_count: 1,
                missing_requirements: [],
                profile_count: 1,
                status: "READY"
              }}
              status="ready"
            />
          </div>
        </OperationalPanel>

        <OperationalPanel
          ariaLabel="Gallery preference controls"
          emptyText="No preferences preview."
          hasItems
          status="READY"
          title="Preferences"
        >
          <div className="detail-stack">
            <PreferenceControls preferences={syntheticUserPreferences} token={null} />
            <PreferenceControls preferences={syntheticCompactDarkPreferences} token={null} />
          </div>
        </OperationalPanel>
      </section>

      <section className="activity-layout" aria-label="Gallery action and status examples">
        <OperationalPanel
          ariaLabel="Gallery actions"
          emptyText="No actions preview."
          hasItems
          status="ACTIVE"
          title="ActionBar"
        >
          <div className="detail-stack">
            <ActionBar actions={galleryActions} />
            <ActionBar actions={galleryActions} runningActionKey="gallery_refresh" />
          </div>
        </OperationalPanel>

        <OperationalPanel
          ariaLabel="Gallery status variants"
          emptyText="No status preview."
          hasItems
          status="READY"
          title="StatusChip"
        >
          <div className="gallery-state-badge-preview" aria-label="Gallery status chip variants">
            {statusVariants.map((status) => (
              <StatusChip key={status} status={status} />
            ))}
          </div>
        </OperationalPanel>
      </section>

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
            <div className="detail-actions gallery-command-preview" aria-label="Gallery icon commands">
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
