import { Link, useLocation } from "react-router-dom";

import { PageHeader } from "../../app/shell";
import { useDevToolsDataDictionary } from "../../platform/hooks";
import { DetailList, MetricGrid, ModuleWorkspaceLayout, ModuleWorkspaceSide, StatePanel } from "../../ui/components";
import { booleanStatus } from "../moduleStatus";

export function DeveloperToolsDataDictionaryView({ token }: { token: string }) {
  const location = useLocation();
  const query = new URLSearchParams(location.search).get("query") ?? "";
  const dictionary = useDevToolsDataDictionary(token, query);
  const rows = dictionary.data?.items ?? [];

  return (
    <>
      <PageHeader
        description="Read-only technical table metadata from the backend Data Dictionary."
        label="Developer tools"
        title="Data Dictionary Explorer"
      />

      <MetricGrid
        ariaLabel="Data Dictionary Explorer metrics"
        items={[
          { key: "matches", label: "Matches", status: booleanStatus(dictionary.data?.total ?? 0), value: dictionary.data?.total ?? 0 },
          { key: "visible", label: "Visible rows", status: booleanStatus(rows.length), value: rows.length },
          { key: "query", label: "Query", status: query ? "ACTIVE" : "EMPTY", value: query || "None" }
        ]}
      />

      <ModuleWorkspaceLayout
        ariaLabel="Developer Tools Data Dictionary workspace"
        side={
          <ModuleWorkspaceSide title="Technical guardrails">
            <ul>
              <li>Read-only metadata from the backend Data Dictionary.</li>
              <li>No local dictionary file paths are exposed.</li>
              <li>Use Catalog Core for functional validation workflows.</li>
              <li>Dedicated table detail routes remain backend-owned.</li>
            </ul>
          </ModuleWorkspaceSide>
        }
        status={dictionary.data?.status ?? "loading"}
        title="Table metadata"
      >
        {dictionary.isLoading ? (
          <StatePanel>Loading Data Dictionary metadata.</StatePanel>
        ) : dictionary.isError ? (
          <StatePanel tone="error">Data Dictionary metadata is unavailable.</StatePanel>
        ) : (
          <div className="detail-stack">
            <p className="empty-text">Source contract: {dictionary.data?.source_contract}</p>
            <DetailList
              ariaLabel="Developer Tools Data Dictionary tables"
              emptyText="No Data Dictionary tables match this query."
              items={rows.map((row) => ({
                action: (
                  <Link className="button button-secondary" to={`/dev-tools/data-dictionary/tables/${row.table_name}`}>
                    Open table
                  </Link>
                ),
                id: row.table_name,
                meta: [
                  row.schema_name,
                  row.data_category,
                  `${row.column_count} column(s)`,
                  row.allow_csvutil ? "CSVUTIL allowed" : "CSVUTIL blocked"
                ],
                status: row.allow_cutover ? "AVAILABLE" : "GUARDED",
                title: row.table_name
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
