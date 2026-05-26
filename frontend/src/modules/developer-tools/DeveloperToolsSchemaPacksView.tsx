import { Link, useLocation } from "react-router-dom";

import { PageHeader } from "../../app/shell";
import { useDevToolsSchemaPacks } from "../../platform/hooks";
import { DetailList, MetricGrid, ModuleWorkspaceLayout, ModuleWorkspaceSide, StatePanel } from "../../ui/components";
import { booleanStatus } from "../moduleStatus";

export function DeveloperToolsSchemaPacksView({ token }: { token: string }) {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const otmVersion = params.get("otm_version") ?? "26A";
  const code = params.get("code") ?? "";
  const schemaPacks = useDevToolsSchemaPacks(token, otmVersion, code);
  const packs = schemaPacks.data?.items ?? [];
  const roots = packs.flatMap((pack) =>
    pack.root_preview.map((root) => ({
      ...root,
      packName: pack.name
    }))
  );
  const visibleRootLimit = 12;

  return (
    <>
      <PageHeader
        description="Read-only WSDL/XSD schema-pack diagnostics from Catalog Core."
        label="Developer tools"
        title="Schema Pack Diagnostics"
      />

      <MetricGrid
        ariaLabel="Schema Pack Diagnostics metrics"
        items={[
          {
            key: "packs",
            label: "Schema packs",
            status: booleanStatus(schemaPacks.data?.total ?? 0),
            value: schemaPacks.data?.total ?? 0
          },
          {
            key: "roots",
            label: "Visible roots",
            status: booleanStatus(roots.length),
            value: Math.min(roots.length, visibleRootLimit)
          },
          { key: "version", label: "OTM version", status: otmVersion ? "ACTIVE" : "EMPTY", value: otmVersion || "None" }
        ]}
      />

      <ModuleWorkspaceLayout
        ariaLabel="Developer Tools Schema Pack workspace"
        side={
          <ModuleWorkspaceSide title="Schema guardrails">
            <ul>
              <li>Read-only metadata from Catalog Core schema-pack contracts.</li>
              <li>Source folders and local schema paths stay hidden from the UI.</li>
              <li>Use Catalog Core schema guidance for official path browsing.</li>
              <li>Use Integration Mapping or Order Release routes for product-facing authoring.</li>
            </ul>
          </ModuleWorkspaceSide>
        }
        status={schemaPacks.data?.status ?? "loading"}
        title="Governed schema roots"
      >
        {schemaPacks.isLoading ? (
          <StatePanel>Loading schema-pack diagnostics.</StatePanel>
        ) : schemaPacks.isError ? (
          <StatePanel tone="error">Schema Pack Diagnostics are unavailable.</StatePanel>
        ) : (
          <div className="detail-stack">
            <p className="empty-text">Source contract: {schemaPacks.data?.source_contract}</p>
            <DetailList
              ariaLabel="Schema pack roots"
              emptyText="No schema-pack roots are available for this OTM version."
              maxVisibleItems={visibleRootLimit}
              items={roots.map((root, index) => ({
                id: `${root.id}-${index}`,
                meta: [root.packName, root.schema_guidance_role, root.domain_area, root.root_type],
                status: "ACTIVE",
                title: root.root_display_label || root.root_name
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
