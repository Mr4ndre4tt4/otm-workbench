import { Link, useLocation } from "react-router-dom";

import { MODULE_DESCRIPTIONS } from "./moduleDescriptions";
import { isNavigationItemActive } from "./routeUtils";
import { ContextSummary, ContextSwitcher, PageHeader } from "../shell";
import {
  AssetsLibraryView,
  AdminConsoleView,
  CatalogCoreView,
  DeveloperToolsDataDictionaryTableView,
  DeveloperToolsDataDictionaryView,
  DeveloperToolsEnvironmentReadinessView,
  DeveloperToolsFkCatalogView,
  DeveloperToolsSchemaPacksView,
  DeveloperToolsView,
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
  ModuleWorkspaceLayout,
  ModuleWorkspaceSide,
  StatePanel
} from "../../ui/components";
import { renderIcon } from "../../ui/icons";

function contextModeLabel(mode: string) {
  return mode === "PUBLIC" ? "Public View" : "Private scope";
}

function CockpitContent({ token }: { token: string }) {
  const cockpit = useCockpitSummary(token);

  if (cockpit.isLoading) {
    return <StatePanel>Loading Project Cockpit...</StatePanel>;
  }

  if (cockpit.isError || !cockpit.data) {
    return <StatePanel tone="error">Project Cockpit is unavailable.</StatePanel>;
  }

  const data = cockpit.data;
  const contextSelector = data.context_selector ?? {
    active_context: data.active_context ?? {},
    mode: data.active_context?.project_id ? "PRIVATE" : "PUBLIC",
    public_view_available: true,
    requires_private_context: false,
    set_context_action_key: "set_active_context"
  };
  const projectInfo = data.project_info ?? {
    contacts: [],
    documents: [],
    links: [],
    secure_vault: {
      metadata_only: true,
      secret_values_available: false,
      status: "NOT_CONFIGURED"
    },
    status: data.setup_status?.active_context_selected ? "AVAILABLE" : "NEEDS_CONTEXT",
    title: "Project information"
  };
  const userScope = data.user_scope ?? {
    allowed_domains: Array.isArray(data.active_context?.allowed_domains) ? data.active_context.allowed_domains : ["PUBLIC"],
    can_view_all_domains: Boolean(data.active_context?.can_view_all_domains),
    is_dba: false,
    role_mode: "SCOPED"
  };
  const accelerators = data.accelerators ?? data.module_summary.items.map((module) => ({
    description: module.description ?? module.path,
    disabled: false,
    disabled_reason: null,
    href: module.path,
    icon_key: module.id,
    key: module.id,
    label: module.label,
    requires_private_context: module.id !== "home",
    status: module.status
  }));
  const routeRecovery = data.route_recovery ?? {
    blocked_route_message: "Return to Project Cockpit and select an available context or accelerator.",
    default_path: "/home",
    return_action_key: "return_to_cockpit"
  };

  return (
    <>
      <PageHeader
        actions={data.available_actions}
        description={data.description}
        label="Workbench home"
        title={data.title}
      />

      <ContextSummary context={data.active_context} />

      <section className="cockpit-deep-flow" aria-label="Project Cockpit workspace">
        <div className="panel cockpit-context-panel">
          <div className="panel-header">
            <h2>Context Selector</h2>
            <span className="status-chip">{contextModeLabel(contextSelector.mode)}</span>
          </div>
          <p className="empty-text">
            {contextSelector.mode === "PUBLIC"
              ? "Public scope is active. Private client/domain accelerators stay blocked until a private context is selected."
              : "Private client/domain and environment scope is active for module work."}
          </p>
          <ContextSwitcher activeContext={contextSelector.active_context} token={token} />
        </div>

        <div className="panel cockpit-project-info-panel">
          <div className="panel-header">
            <h2>{projectInfo.title}</h2>
            <span className="status-chip">{projectInfo.status}</span>
          </div>
          <div className="cockpit-info-grid">
            <span className="detail-field">
              <span>Vault</span>
              <strong>{projectInfo.secure_vault.status}</strong>
            </span>
            <span className="detail-field">
              <span>Secrets</span>
              <strong>{projectInfo.secure_vault.secret_values_available ? "Available" : "Metadata only"}</strong>
            </span>
            <span className="detail-field">
              <span>Access</span>
              <strong>{userScope.role_mode}</strong>
            </span>
            <span className="detail-field">
              <span>Domains</span>
              <strong>{userScope.allowed_domains.join(", ")}</strong>
            </span>
          </div>
          <p className="empty-text">Project links, documents, contacts, and secure-vault metadata are owned by Settings.</p>
        </div>

        <div className="panel cockpit-accelerators-panel">
          <div className="panel-header">
            <h2>Accelerators</h2>
            <span className="status-chip">{booleanStatus(accelerators.length)}</span>
          </div>
          <div className="cockpit-accelerator-grid">
            {accelerators.map((accelerator) =>
              accelerator.disabled ? (
                <div className="cockpit-accelerator cockpit-accelerator-disabled" key={accelerator.key}>
                  <span className="cockpit-accelerator-icon">{renderIcon(accelerator.icon_key)}</span>
                  <strong>
                    {accelerator.label}
                    {accelerator.disabled_reason ? ` / ${accelerator.disabled_reason}` : ""}
                  </strong>
                  <span>{accelerator.description}</span>
                </div>
              ) : (
                <Link className="cockpit-accelerator" key={accelerator.key} to={accelerator.href}>
                  <span className="cockpit-accelerator-icon">{renderIcon(accelerator.icon_key)}</span>
                  <strong>{accelerator.label}</strong>
                  <span>{accelerator.description}</span>
                </Link>
              )
            )}
          </div>
          <p className="empty-text">{routeRecovery.blocked_route_message}</p>
        </div>
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
      <StatePanel tone="error">
        Use the backend-owned navigation menu to open an available module.
        <div className="state-actions">
          <Link className="button button-primary" to="/home">
            Return to Cockpit
          </Link>
        </div>
      </StatePanel>
    </>
  );
}

export function WorkbenchRoute({ items, token }: { items: NavigationItem[]; token: string }) {
  const location = useLocation();
  const currentPath = location.pathname;
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
  if (item?.id === "settings") {
    return <AdminConsoleView token={token} />;
  }
  if (item?.id === "admin") {
    return <AdminConsoleView token={token} />;
  }
  if (item?.id === "dev_tools") {
    if (currentPath.startsWith("/dev-tools/data-dictionary/tables/")) {
      return <DeveloperToolsDataDictionaryTableView token={token} />;
    }
    if (currentPath === "/dev-tools/data-dictionary") {
      return <DeveloperToolsDataDictionaryView token={token} />;
    }
    if (currentPath === "/dev-tools/fk-catalog") {
      return <DeveloperToolsFkCatalogView token={token} />;
    }
    if (currentPath === "/dev-tools/schema-packs") {
      return <DeveloperToolsSchemaPacksView token={token} />;
    }
    if (currentPath === "/dev-tools/environment-readiness") {
      return <DeveloperToolsEnvironmentReadinessView token={token} />;
    }
    return <DeveloperToolsView item={item} token={token} />;
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
