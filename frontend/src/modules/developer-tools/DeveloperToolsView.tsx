import { Link } from "react-router-dom";

import { PageHeader } from "../../app/shell";
import { useDevToolsSummary } from "../../platform/hooks";
import type { NavigationItem } from "../../platform/types";
import { ActivityRow, DetailList, MetricGrid, ModuleWorkspaceLayout, ModuleWorkspaceSide, StatePanel } from "../../ui/components";
import { booleanStatus } from "../moduleStatus";

export function DeveloperToolsView({ item, token }: { item: NavigationItem; token: string }) {
  const summary = useDevToolsSummary(token);
  const counts = summary.data?.counts ?? { available_tools: 0, disabled_tools: 0, recent_runs: 0 };
  const tools = summary.data?.tools ?? [];
  const recentRuns = summary.data?.recent_runs ?? [];
  const guards = summary.data?.guards ?? [];

  if (summary.isError) {
    return (
      <>
        <PageHeader
          description="Developer Tools is controlled by backend navigation, feature flags, and capabilities."
          label="Developer tools"
          title="Technical Diagnostics Hub"
        />
        <StatePanel tone="error">Developer Tools summary is unavailable.</StatePanel>
      </>
    );
  }

  return (
    <>
      <PageHeader
        description="Developer Tools is controlled by backend navigation, feature flags, and capabilities."
        label="Developer tools"
        title="Technical Diagnostics Hub"
      />

      <MetricGrid
        ariaLabel="Developer Tools guard metrics"
        items={[
          {
            key: "route_status",
            label: "Route status",
            status: item.status,
            value: item.status
          },
          {
            key: "available_tools",
            label: "Available tools",
            status: booleanStatus(counts.available_tools),
            value: counts.available_tools
          },
          {
            key: "disabled_tools",
            label: "Disabled tools",
            status: counts.disabled_tools ? "GUARDED" : "EMPTY",
            value: counts.disabled_tools
          },
          {
            key: "recent_runs",
            label: "Recent runs",
            status: booleanStatus(counts.recent_runs),
            value: counts.recent_runs
          }
        ]}
      />

      <ModuleWorkspaceLayout
        ariaLabel="Developer Tools guarded workspace"
        side={
          <ModuleWorkspaceSide title="Backend gates">
            {guards.length ? (
              <div className="activity-list" aria-label="Developer Tools backend gates">
                {guards.map((guard) => (
                  <ActivityRow key={guard.key} status={guard.status} subtitle={guard.message} title={guard.label} />
                ))}
              </div>
            ) : (
              <ul>
                <li>Feature flag must enable the route.</li>
                <li>Capability must authorize technical diagnostics.</li>
                <li>Summary contracts must define tools and disabled reasons.</li>
                <li>Diagnostic actions must produce audit-safe results.</li>
              </ul>
            )}
          </ModuleWorkspaceSide>
        }
        status={summary.data?.status ?? item.status}
        title={summary.isLoading ? "Loading diagnostic contracts" : "Diagnostic tools"}
      >
        {summary.isLoading ? (
          <StatePanel>Loading backend-owned Developer Tools summary.</StatePanel>
        ) : (
          <div className="detail-stack">
            <p className="empty-text">Summary returns backend-safe metadata only; raw diagnostic payloads remain hidden.</p>
            <DetailList
              ariaLabel="Developer Tools available tools"
              emptyText="No diagnostic tools are available for this context."
              items={tools.map((tool) => ({
                id: tool.key,
                action: tool.href ? (
                  <Link className="button button-secondary" to={tool.href}>
                    Open {tool.label}
                  </Link>
                ) : undefined,
                meta: [
                  tool.required_capability,
                  tool.href ?? "No route",
                  tool.disabled_reason ?? "Open from dedicated route"
                ],
                status: tool.status,
                title: tool.label
              }))}
            />
            <DetailList
              ariaLabel="Developer Tools recent runs"
              emptyText="No recent diagnostic runs."
              items={recentRuns.map((run) => ({
                id: run.id,
                meta: [
                  run.message,
                  run.domain_name ?? "No domain",
                  run.input_present ? "Input stored" : "No input",
                  run.result_present ? "Result stored" : "No result"
                ],
                status: run.status,
                title: run.job_type
              }))}
            />
          </div>
        )}
      </ModuleWorkspaceLayout>
    </>
  );
}
