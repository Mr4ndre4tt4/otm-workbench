import { useState } from 'react';

import { useCatalogMacroObjectDetail, useCatalogMacroObjectLoadPlan, useCatalogMacroObjects, useCatalogMacroObjectTables } from '../../platform/hooks';
import type { CatalogMacroObject } from '../../platform/types';
import { PageHeader } from '../../app/shell';
import { DetailList, MetricGrid, ModuleObjectList, SelectedObjectPanel, StatePanel, StatusChip } from '../../ui/components';
import { booleanStatus } from '../moduleStatus';

function catalogMacroMeta(item: CatalogMacroObject) {
  const tableCount = item.summary?.table_count ?? 0;
  const dependencyCount = item.summary?.dependency_count ?? 0;
  return [item.category, item.default_method, `${tableCount} table(s)`, `${dependencyCount} dependency(ies)`];
}

export function CatalogCoreView({ token }: { token: string }) {
  const macroObjects = useCatalogMacroObjects(token);
  const [selectedMacroCode, setSelectedMacroCode] = useState<string | null>(null);
  const macroItems = macroObjects.data?.items ?? [];
  const effectiveMacroCode = selectedMacroCode ?? macroItems[0]?.code ?? null;
  const macroDetail = useCatalogMacroObjectDetail(token, effectiveMacroCode);
  const macroTables = useCatalogMacroObjectTables(token, effectiveMacroCode);
  const macroLoadPlan = useCatalogMacroObjectLoadPlan(token, effectiveMacroCode);
  const selectedMacro = macroDetail.data;
  const tableItems = macroTables.data?.items ?? [];
  const loadPlanItems = macroLoadPlan.data?.items ?? [];
  const csvutilMacroCount = macroItems.filter((item) => item.allow_csvutil).length;
  const cutoverMacroCount = macroItems.filter((item) => item.allow_cutover).length;
  const validatedTableCount = tableItems.filter((item) => item.validated_by_datadict).length;

  if (macroObjects.isLoading) {
    return <StatePanel>Loading OTM Catalog Core...</StatePanel>;
  }

  if (macroObjects.isError || !macroObjects.data) {
    return <StatePanel tone="error">OTM Catalog Core is unavailable.</StatePanel>;
  }

  return (
    <>
      <PageHeader
        description="Canonical OTM catalog foundation for macro objects, load plans, data dictionary alignment, and module contracts."
        label="Module workspace"
        title="OTM Catalog Core"
      />

      <MetricGrid
        ariaLabel="OTM Catalog Core metrics"
        items={[
          { key: "macro_objects", label: "Macro objects", status: booleanStatus(macroObjects.data.total), value: macroObjects.data.total },
          { key: "csvutil", label: "CSVUTIL allowed", status: booleanStatus(csvutilMacroCount), value: csvutilMacroCount },
          { key: "cutover", label: "Cutover allowed", status: booleanStatus(cutoverMacroCount), value: cutoverMacroCount },
          { key: "validated", label: "Validated tables", status: booleanStatus(validatedTableCount), value: validatedTableCount }
        ]}
      />

      <section className="module-template" aria-label="OTM Catalog Core workspace">
        <div className="module-template-main">
          <div className="panel-header">
            <h2>Macro objects</h2>
            <StatusChip status={macroItems.length ? "ACTIVE" : "EMPTY"} />
          </div>
          <ModuleObjectList
            ariaLabel="Catalog macro objects"
            emptyText="No catalog macro objects available for the current context."
            items={macroItems.map((item) => ({
              id: item.code,
              meta: catalogMacroMeta(item),
              status: item.allow_csvutil || item.allow_cutover ? "ACTIVE" : "READ_ONLY",
              subtitle: item.name,
              title: item.code
            }))}
            onSelect={setSelectedMacroCode}
            selectedId={effectiveMacroCode}
          />
        </div>

        <SelectedObjectPanel
          ariaLabel="Selected catalog macro object"
          emptyText="Select a macro object to inspect backend-owned catalog metadata."
          fields={
            selectedMacro
              ? [
                  { label: "Category", value: selectedMacro.category },
                  { label: "Default method", value: selectedMacro.default_method },
                  { label: "Tables", value: selectedMacro.summary?.table_count ?? tableItems.length },
                  { label: "Dependencies", value: selectedMacro.summary?.dependency_count ?? loadPlanItems.length - 1 }
                ]
              : []
          }
          isLoading={(macroDetail.isLoading || macroTables.isLoading || macroLoadPlan.isLoading) && Boolean(effectiveMacroCode)}
          loadingText="Loading selected macro object..."
          status={selectedMacro?.allow_csvutil || selectedMacro?.allow_cutover ? "ACTIVE" : "READ_ONLY"}
          subtitle={selectedMacro?.name}
          title={selectedMacro?.code}
        >
          {selectedMacro?.description ? <p className="empty-text">{selectedMacro.description}</p> : null}
          <DetailList
            ariaLabel="Selected macro object tables"
            emptyText="No tables linked to this macro object."
            items={tableItems.map((item) => ({
              id: item.id,
              meta: [item.relationship_role, item.data_category, item.allow_csvutil ? "CSVUTIL" : "No CSVUTIL"],
              status: item.validated_by_datadict ? "VALIDATED" : "NEEDS_REVIEW",
              title: item.table_name
            }))}
          />
          <DetailList
            ariaLabel="Selected macro object load plan"
            emptyText="No load plan available for this macro object."
            items={loadPlanItems.map((item) => ({
              id: `${item.dependency_role}-${item.macro_object_code}`,
              meta: [item.dependency_role, item.dependency_type, `${item.table_count} table(s)`],
              status: item.all_tables_validated ? "VALIDATED" : "NEEDS_REVIEW",
              title: item.macro_object_code
            }))}
          />
        </SelectedObjectPanel>
      </section>
    </>
  );
}
