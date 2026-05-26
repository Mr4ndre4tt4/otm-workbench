import { Link } from "react-router-dom";

import { PageHeader } from "../../app/shell";
import { useDevToolsEnvironmentReadiness } from "../../platform/hooks";
import { DetailList, MetricGrid, ModuleWorkspaceLayout, ModuleWorkspaceSide, StatePanel } from "../../ui/components";
import { booleanStatus } from "../moduleStatus";

export function DeveloperToolsEnvironmentReadinessView({ token }: { token: string }) {
  const readiness = useDevToolsEnvironmentReadiness(token);
  const checks = readiness.data?.checks ?? [];
  const environments = readiness.data?.environments ?? [];
  const context = readiness.data?.active_context;
  const domainScope = context?.domain_name ?? "All allowed domains";

  return (
    <>
      <PageHeader
        description={readiness.data?.description ?? "Read-only checks for the active implementation context."}
        label="Developer tools"
        title="Environment Readiness"
      />

      <MetricGrid
        ariaLabel="Environment Readiness metrics"
        items={[
          {
            key: "environments",
            label: "Environments",
            status: booleanStatus(readiness.data?.counts.environments ?? 0),
            value: readiness.data?.counts.environments ?? 0
          },
          {
            key: "ready",
            label: "Ready checks",
            status: booleanStatus(readiness.data?.counts.ready_checks ?? 0),
            value: readiness.data?.counts.ready_checks ?? 0
          },
          {
            key: "blocked",
            label: "Blocked checks",
            status: readiness.data?.counts.blocked_checks ? "GUARDED" : "ACTIVE",
            value: readiness.data?.counts.blocked_checks ?? 0
          }
        ]}
      />

      <ModuleWorkspaceLayout
        ariaLabel="Developer Tools Environment Readiness workspace"
        side={
          <ModuleWorkspaceSide title="Environment scope">
            {readiness.isLoading ? (
              <StatePanel>Loading active environment scope.</StatePanel>
            ) : readiness.isError ? (
              <StatePanel tone="error">Environment scope is unavailable.</StatePanel>
            ) : (
              <div className="detail-stack">
                <p className="empty-text">Domain scope: {domainScope}</p>
                <DetailList
                  ariaLabel="Environment scope"
                  emptyText="No environments are available for the active project."
                  items={environments.map((environment) => ({
                    id: environment.id,
                    meta: [`Type ${environment.environment_type}`, environment.is_active ? "Active context" : "Available"],
                    status: environment.status,
                    title: environment.name
                  }))}
                />
              </div>
            )}
          </ModuleWorkspaceSide>
        }
        status={readiness.data?.status ?? "loading"}
        title="Readiness checks"
      >
        {readiness.isLoading ? (
          <StatePanel>Loading Environment Readiness checks.</StatePanel>
        ) : readiness.isError ? (
          <StatePanel tone="error">Environment Readiness is unavailable.</StatePanel>
        ) : (
          <div className="detail-stack">
            <p className="empty-text">Source contract: {readiness.data?.source_contract}</p>
            <DetailList
              ariaLabel="Environment Readiness checks"
              emptyText="No readiness checks are available."
              items={checks.map((check) => ({
                id: check.key,
                meta: [check.message],
                status: check.status,
                title: check.label
              }))}
            />
          </div>
        )}
      </ModuleWorkspaceLayout>

      <Link className="button button-secondary" to="/dev-tools">
        Back to Developer Tools
      </Link>
    </>
  );
}
