import { Link, useLocation } from "react-router-dom";

import { PageHeader } from "../../app/shell";
import { useDevToolsFkCatalog } from "../../platform/hooks";
import { DetailList, MetricGrid, ModuleWorkspaceLayout, ModuleWorkspaceSide, StatePanel } from "../../ui/components";
import { booleanStatus } from "../moduleStatus";

export function DeveloperToolsFkCatalogView({ token }: { token: string }) {
  const location = useLocation();
  const sourceTable = new URLSearchParams(location.search).get("source_table") ?? "RATE_GEO_COST";
  const relationships = useDevToolsFkCatalog(token, sourceTable);
  const rows = relationships.data?.items ?? [];
  const visibleRowLimit = 12;

  return (
    <>
      <PageHeader
        description="Read-only foreign-key relationships from the backend Data Dictionary."
        label="Developer tools"
        title="FK Catalog Explorer"
      />

      <MetricGrid
        ariaLabel="FK Catalog Explorer metrics"
        items={[
          {
            key: "relationships",
            label: "Relationships",
            status: booleanStatus(relationships.data?.total ?? 0),
            value: relationships.data?.total ?? 0
          },
          {
            key: "visible",
            label: "Visible rows",
            status: booleanStatus(rows.length),
            value: Math.min(rows.length, visibleRowLimit)
          },
          { key: "source", label: "Source table", status: sourceTable ? "ACTIVE" : "EMPTY", value: sourceTable || "None" }
        ]}
      />

      <ModuleWorkspaceLayout
        ariaLabel="Developer Tools FK Catalog workspace"
        side={
          <ModuleWorkspaceSide title="Relationship guardrails">
            <ul>
              <li>Read-only foreign-key metadata from the backend Data Dictionary.</li>
              <li>Parent table links open Data Dictionary table detail routes.</li>
              <li>No local dictionary file paths are exposed.</li>
              <li>Use Catalog Core load plan routes for functional sequencing decisions.</li>
            </ul>
          </ModuleWorkspaceSide>
        }
        status={relationships.data?.status ?? "loading"}
        title="Foreign-key relationships"
      >
        {relationships.isLoading ? (
          <StatePanel>Loading FK Catalog relationships.</StatePanel>
        ) : relationships.isError ? (
          <StatePanel tone="error">FK Catalog relationships are unavailable.</StatePanel>
        ) : (
          <div className="detail-stack">
            <p className="empty-text">Source contract: {relationships.data?.source_contract}</p>
            <DetailList
              ariaLabel="FK Catalog relationships"
              emptyText="No foreign-key relationships are available for this source table."
              maxVisibleItems={visibleRowLimit}
              items={rows.map((row, index) => ({
                action: (
                  <Link className="button button-secondary" to={row.parent_table_href}>
                    Open parent table {row.parent_table_name}
                  </Link>
                ),
                id: `${row.column_name}-${row.parent_table_name}-${row.parent_column_name}-${index}`,
                meta: [row.relationship_type, row.parent_table_name, row.parent_column_name],
                status: "ACTIVE",
                title: row.column_name
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
