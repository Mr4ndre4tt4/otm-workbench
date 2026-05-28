import { Link, useLocation } from "react-router-dom";

import { PageHeader } from "../../app/shell";
import { useDevToolsDataDictionaryTable } from "../../platform/hooks";
import { DetailList, MetricGrid, ModuleWorkspaceLayout, ModuleWorkspaceSide, StatePanel } from "../../ui/components";
import { booleanStatus } from "../moduleStatus";

export function DeveloperToolsDataDictionaryTableView({ token }: { token: string }) {
  const location = useLocation();
  const tableName = decodeURIComponent(location.pathname.split("/").filter(Boolean).at(-1) ?? "");
  const detail = useDevToolsDataDictionaryTable(token, tableName);
  const table = detail.data?.table;
  const columns = detail.data?.columns ?? [];
  const backQuery = table?.table_name ?? tableName ?? "";

  return (
    <>
      <PageHeader
        description={table?.description || "Read-only table detail from the backend Data Dictionary."}
        label="Data Dictionary Table Detail"
        title={table?.table_name ?? tableName ?? "Data Dictionary Table"}
      />

      <MetricGrid
        ariaLabel="Data Dictionary table detail metrics"
        items={[
          {
            key: "columns",
            label: "Columns",
            status: booleanStatus(detail.data?.column_total ?? 0),
            value: detail.data?.column_total ?? 0
          },
          {
            key: "foreign_keys",
            label: "Foreign keys",
            status: booleanStatus(table?.foreign_key_count ?? 0),
            value: table?.foreign_key_count ?? 0
          },
          {
            key: "category",
            label: "Category",
            status: table?.data_category && table.data_category !== "UNKNOWN" ? "ACTIVE" : "EMPTY",
            value: table?.data_category ?? "Unknown"
          },
          {
            key: "csvutil",
            label: "CSVUTIL",
            status: table?.allow_csvutil ? "AVAILABLE" : "GUARDED",
            value: table?.allow_csvutil ? "Allowed" : "Blocked"
          }
        ]}
      />

      <ModuleWorkspaceLayout
        ariaLabel="Developer Tools Data Dictionary table detail workspace"
        side={
          <ModuleWorkspaceSide title="Table guardrails">
            <ul>
              <li>Read-only table and column metadata.</li>
              <li>No local dictionary file paths are exposed.</li>
              <li>Primary keys and required columns are backend-owned.</li>
              <li>Use Catalog Core for functional validation and load-order workflows.</li>
            </ul>
          </ModuleWorkspaceSide>
        }
        status={detail.data?.status ?? "loading"}
        title="Column metadata"
      >
        {detail.isLoading ? (
          <StatePanel>Loading Data Dictionary table detail.</StatePanel>
        ) : detail.isError ? (
          <StatePanel tone="error">Data Dictionary table detail is unavailable.</StatePanel>
        ) : (
          <div className="detail-stack">
            <p className="empty-text">Source contract: {detail.data?.source_contract}</p>
            <DetailList
              ariaLabel="Data Dictionary table columns"
              emptyText="No columns are available for this table."
              maxVisibleItems={40}
              items={columns.map((column) => ({
                id: column.column_name,
                meta: [
                  column.data_type ?? "Unknown type",
                  column.nullable ? "Nullable" : "Required",
                  column.is_primary_key ? "Primary key" : "Non-key",
                  column.is_required ? "Required by dictionary" : "Optional by dictionary"
                ],
                status: column.is_required || column.is_primary_key ? "ACTIVE" : "EMPTY",
                title: column.column_name
              }))}
            />
          </div>
        )}
      </ModuleWorkspaceLayout>

      <Link className="button button-secondary" to={`/dev-tools/data-dictionary?query=${encodeURIComponent(backQuery)}`}>
        Back to Data Dictionary
      </Link>
    </>
  );
}
