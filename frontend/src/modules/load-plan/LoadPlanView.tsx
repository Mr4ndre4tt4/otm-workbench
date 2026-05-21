import { useState } from 'react';

import { useLoadPlanPackageDetail, useLoadPlanPackages, useLoadPlanSummary } from '../../platform/hooks';
import type { LoadPlanPackage } from '../../platform/types';
import { PageHeader } from '../../app/shell';
import { DetailList, MetricGrid, ModuleObjectList, SelectedObjectPanel, StatePanel, StatusChip } from '../../ui/components';
import { booleanStatus } from '../moduleStatus';

function loadPlanPackageMeta(item: LoadPlanPackage) {
  const tableCount = item.summary.table_count ?? item.load_sequence.length;
  const rowCount =
    item.summary.row_count ?? item.load_sequence.reduce((total, sequenceItem) => total + sequenceItem.row_count, 0);
  return [item.source_module, item.summary.catalog_macro_object_code ?? "No catalog macro", `${tableCount} table(s)`, `${rowCount} row(s)`];
}

export function LoadPlanView({ token }: { token: string }) {
  const summary = useLoadPlanSummary(token);
  const packages = useLoadPlanPackages(token);
  const [selectedPackageId, setSelectedPackageId] = useState<string | null>(null);
  const packageItems = packages.data?.items ?? [];
  const effectivePackageId = selectedPackageId ?? packageItems[0]?.id ?? null;
  const packageDetail = useLoadPlanPackageDetail(token, effectivePackageId);
  const selectedPackage = packageDetail.data;
  const sourceModuleCount = Object.keys(summary.data?.by_source_module ?? {}).length;
  const catalogMacroCount = Object.keys(summary.data?.by_catalog_macro_object ?? {}).length;
  const registeredCount = summary.data?.registered_packages ?? 0;
  const sequenceRowCount =
    selectedPackage?.summary.row_count ??
    selectedPackage?.load_sequence.reduce((total, sequenceItem) => total + sequenceItem.row_count, 0) ??
    0;

  if (summary.isLoading || packages.isLoading) {
    return <StatePanel>Loading Load Plan...</StatePanel>;
  }

  if (summary.isError || packages.isError || !summary.data || !packages.data) {
    return <StatePanel tone="error">Load Plan is unavailable.</StatePanel>;
  }

  return (
    <>
      <PageHeader
        description="Load package intake, CSVUTIL planning, review queues, cutover readiness, and handoff controls."
        label="Module workspace"
        title="Load Plan"
      />

      <MetricGrid
        ariaLabel="Load Plan metrics"
        items={[
          { key: "registered", label: "Packages", status: booleanStatus(registeredCount), value: registeredCount },
          { key: "sources", label: "Sources", status: booleanStatus(sourceModuleCount), value: sourceModuleCount },
          { key: "catalog", label: "Catalog macros", status: booleanStatus(catalogMacroCount), value: catalogMacroCount },
          { key: "visible", label: "Visible rows", status: booleanStatus(packageItems.length), value: packageItems.length }
        ]}
      />

      <section className="module-template" aria-label="Load Plan workspace">
        <div className="module-template-main">
          <div className="panel-header">
            <h2>Packages</h2>
            <StatusChip status={packageItems.length ? "ACTIVE" : "EMPTY"} />
          </div>
          <ModuleObjectList
            ariaLabel="Load plan packages"
            emptyText="No Load Plan packages registered for the current context."
            items={packageItems.map((item) => ({
              id: item.id,
              meta: loadPlanPackageMeta(item),
              status: item.status,
              subtitle: item.summary.catalog_macro_object_code ?? item.source_module,
              title: item.package_type
            }))}
            onSelect={setSelectedPackageId}
            selectedId={effectivePackageId}
          />
        </div>

        <SelectedObjectPanel
          emptyText="Select a Load Plan package to inspect backend-owned package metadata."
          fields={
            selectedPackage
              ? [
                  { label: "Source module", value: selectedPackage.source_module },
                  { label: "Source entity", value: selectedPackage.source_entity_type },
                  { label: "Catalog macro", value: selectedPackage.summary.catalog_macro_object_code ?? "None" },
                  { label: "Rows", value: sequenceRowCount }
                ]
              : []
          }
          isLoading={packageDetail.isLoading && Boolean(effectivePackageId)}
          loadingText="Loading selected package..."
          status={selectedPackage?.status ?? "PENDING"}
          subtitle={selectedPackage?.summary.catalog_macro_object_code ?? selectedPackage?.source_module}
          title={selectedPackage?.package_type}
        >
          <DetailList
            ariaLabel="Selected package load sequence"
            emptyText="No load sequence available for this package."
            items={(selectedPackage?.load_sequence ?? []).map((item) => ({
              id: `${selectedPackage?.id ?? "package"}-${item.position}-${item.table_name}`,
              meta: [`Position ${item.position}`, `${item.row_count} rows`],
              status: item.requirement_level,
              title: item.table_name
            }))}
          />
        </SelectedObjectPanel>
      </section>
    </>
  );
}
