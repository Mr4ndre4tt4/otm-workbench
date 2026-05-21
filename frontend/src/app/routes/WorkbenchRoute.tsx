import { useLocation } from "react-router-dom";

import { ComponentGalleryRoute } from "./ComponentGalleryRoute";
import { MODULE_DESCRIPTIONS } from "./moduleDescriptions";
import { isNavigationItemActive } from "./routeUtils";
import { ContextSummary, ContextSwitcher, PageHeader, ReadinessPanel } from "../shell";
import {
  AssetsLibraryView,
  CatalogCoreView,
  EvidenceHubView,
  IntegrationMappingView,
  LoadPlanView,
  MasterDataView,
  OrderReleaseGeneratorView,
  RatesSummaryView
} from "../../modules";
import { booleanStatus } from "../../modules/moduleStatus";
import { useCockpitSummary } from "../../platform/hooks";
import type { NavigationItem } from "../../platform/types";
import {
  ActivityRow,
  MetricGrid,
  ModuleWorkspaceLayout,
  ModuleWorkspaceSide,
  OperationalPanel,
  StatePanel
} from "../../ui/components";

function CockpitContent({ token }: { token: string }) {
  const cockpit = useCockpitSummary(token);

  if (cockpit.isLoading) {
    return <StatePanel>Loading Project Cockpit...</StatePanel>;
  }

  if (cockpit.isError || !cockpit.data) {
    return <StatePanel tone="error">Project Cockpit is unavailable.</StatePanel>;
  }

  const data = cockpit.data;

  return (
    <>
      <PageHeader
        actions={data.available_actions}
        description={data.description}
        label="Workbench home"
        title={data.title}
      />

      <ContextSummary context={data.active_context} />
      <ContextSwitcher token={token} />

      <ReadinessPanel setupStatus={data.setup_status} status={data.status} />

      <MetricGrid
        ariaLabel="Project activity"
        items={[
          {
            key: "visible_modules",
            label: "Visible modules",
            status: booleanStatus(data.module_summary.total),
            value: data.module_summary.total
          },
          {
            key: "recent_jobs",
            label: "Recent jobs",
            status: booleanStatus(data.counts.recent_jobs),
            value: data.counts.recent_jobs
          },
          {
            key: "recent_artifacts",
            label: "Artifacts",
            status: booleanStatus(data.counts.recent_artifacts),
            value: data.counts.recent_artifacts
          },
          {
            key: "recent_evidence",
            label: "Evidence",
            status: booleanStatus(data.counts.recent_evidence),
            value: data.counts.recent_evidence
          }
        ]}
      />

      <section className="activity-layout">
        <OperationalPanel
          ariaLabel="Recent jobs"
          emptyText="No recent jobs for the active project."
          hasItems={data.recent_jobs.length > 0}
          status={data.counts.recent_jobs ? "ACTIVE" : "EMPTY"}
          title="Recent jobs"
        >
          {data.recent_jobs.map((job) => (
            <ActivityRow key={job.id} status={job.status} subtitle={job.source_module} title={job.job_type} />
          ))}
        </OperationalPanel>

        <OperationalPanel
          ariaLabel="Recent evidence"
          emptyText="No client-safe evidence for the active project."
          hasItems={data.recent_evidence.length > 0}
          status={data.counts.recent_evidence ? "ACTIVE" : "EMPTY"}
          title="Recent evidence"
        >
          {data.recent_evidence.map((evidence) => (
            <ActivityRow
              key={evidence.id}
              status={evidence.status}
              subtitle={evidence.source_module}
              title={evidence.evidence_type}
            />
          ))}
        </OperationalPanel>
      </section>
    </>
  );
}

function ModulePlaceholder({ item }: { item: NavigationItem }) {
  const description = MODULE_DESCRIPTIONS[item.id] ?? "Module workspace prepared for backend-owned contracts.";
  return (
    <>
      <PageHeader description={description} label="Module workspace" title={item.label} />
      <ModuleWorkspaceLayout
        ariaLabel={`${item.label} module template`}
        side={
          <ModuleWorkspaceSide title="Expected panels">
            <ul>
              <li>Primary list or work queue</li>
              <li>Selected object summary</li>
              <li>Available actions from backend</li>
              <li>Jobs, artifacts, and evidence links</li>
            </ul>
          </ModuleWorkspaceSide>
        }
        status={item.status}
        title="Overview"
      >
        <p className="empty-text">
          This route is wired into the shared shell. The next slice can attach the module list, detail, filters,
          actions, and evidence panels without creating a custom page framework.
        </p>
      </ModuleWorkspaceLayout>
    </>
  );
}

function UnknownRoute() {
  return (
    <>
      <PageHeader
        description="This route is not registered by the backend navigation contract for the current user."
        label="Route not available"
        title="Module unavailable"
      />
      <StatePanel tone="error">Use the backend-owned navigation menu to open an available module.</StatePanel>
    </>
  );
}

export function WorkbenchRoute({ items, token }: { items: NavigationItem[]; token: string }) {
  const location = useLocation();
  const currentPath = location.pathname;
  if (currentPath === "/__gui/component-gallery") {
    return <ComponentGalleryRoute />;
  }
  if (currentPath === "/" || currentPath === "/home") {
    return <CockpitContent token={token} />;
  }
  const item = items.find((candidate) => isNavigationItemActive(candidate, currentPath));
  if (item?.id === "rates") {
    return <RatesSummaryView token={token} />;
  }
  if (item?.id === "assets") {
    return <AssetsLibraryView token={token} />;
  }
  if (item?.id === "evidence") {
    return <EvidenceHubView token={token} />;
  }
  if (item?.id === "load_plan") {
    return <LoadPlanView token={token} />;
  }
  if (item?.id === "catalog") {
    return <CatalogCoreView token={token} />;
  }
  if (item?.id === "master_data") {
    return <MasterDataView token={token} />;
  }
  if (item?.id === "order_release_generator") {
    return <OrderReleaseGeneratorView token={token} />;
  }
  if (item?.id === "integration_mapping") {
    return <IntegrationMappingView token={token} />;
  }
  return item ? <ModulePlaceholder item={item} /> : <UnknownRoute />;
}
