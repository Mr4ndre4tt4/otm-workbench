import { useState } from 'react';

import { useMasterDataTemplateDetail, useMasterDataTemplates } from '../../platform/hooks';
import type { MasterDataTemplate } from '../../platform/types';
import { PageHeader } from '../../app/shell';
import { DetailList, MetricGrid, ModuleObjectList, SelectedObjectPanel, StatePanel, StatusChip } from '../../ui/components';
import { booleanStatus } from '../moduleStatus';

function masterDataTemplateMeta(item: MasterDataTemplate) {
  const fieldCount = item.sheets.reduce((total, sheet) => total + sheet.fields.length, 0);
  return [item.catalog_macro_object_code, item.data_category, `${item.sheets.length} sheet(s)`, `${fieldCount} field(s)`];
}

export function MasterDataView({ token }: { token: string }) {
  const templates = useMasterDataTemplates(token);
  const [selectedTemplateCode, setSelectedTemplateCode] = useState<string | null>(null);
  const templateItems = templates.data?.items ?? [];
  const effectiveTemplateCode = selectedTemplateCode ?? templateItems[0]?.code ?? null;
  const templateDetail = useMasterDataTemplateDetail(token, effectiveTemplateCode);
  const selectedTemplate = templateDetail.data;
  const targetTableCount = new Set(templateItems.flatMap((item) => item.target_tables)).size;
  const sheetCount = templateItems.reduce((total, item) => total + item.sheets.length, 0);
  const fieldCount =
    selectedTemplate?.sheets.reduce((total, sheet) => total + sheet.fields.length, 0) ??
    templateItems.reduce((total, item) => total + item.sheets.reduce((sheetTotal, sheet) => sheetTotal + sheet.fields.length, 0), 0);

  if (templates.isLoading) {
    return <StatePanel>Loading Data Factory...</StatePanel>;
  }

  if (templates.isError || !templates.data) {
    return <StatePanel tone="error">Data Factory is unavailable.</StatePanel>;
  }

  return (
    <>
      <PageHeader
        description="Template factory and master data batch preparation for backend-first OTM implementation flows."
        label="Module workspace"
        title="Data Factory"
      />

      <MetricGrid
        ariaLabel="Data Factory metrics"
        items={[
          { key: "templates", label: "Templates", status: booleanStatus(templates.data.total), value: templates.data.total },
          { key: "tables", label: "Target tables", status: booleanStatus(targetTableCount), value: targetTableCount },
          { key: "sheets", label: "Sheets", status: booleanStatus(sheetCount), value: sheetCount },
          { key: "fields", label: "Fields", status: booleanStatus(fieldCount), value: fieldCount }
        ]}
      />

      <section className="module-template" aria-label="Data Factory workspace">
        <div className="module-template-main">
          <div className="panel-header">
            <h2>Templates</h2>
            <StatusChip status={templateItems.length ? "ACTIVE" : "EMPTY"} />
          </div>
          <ModuleObjectList
            ariaLabel="Master Data templates"
            emptyText="No Master Data templates available for the current context."
            items={templateItems.map((item) => ({
              id: item.code,
              meta: masterDataTemplateMeta(item),
              status: item.status,
              subtitle: item.name,
              title: item.code
            }))}
            onSelect={setSelectedTemplateCode}
            selectedId={effectiveTemplateCode}
          />
        </div>

        <SelectedObjectPanel
          ariaLabel="Selected Master Data template"
          emptyText="Select a template to inspect backend-owned metadata."
          fields={
            selectedTemplate
              ? [
                  { label: "Macro object", value: selectedTemplate.catalog_macro_object_code },
                  { label: "Version", value: selectedTemplate.version },
                  { label: "Target tables", value: selectedTemplate.target_tables.length },
                  { label: "Fields", value: fieldCount }
                ]
              : []
          }
          isLoading={templateDetail.isLoading && Boolean(effectiveTemplateCode)}
          loadingText="Loading selected template..."
          status={selectedTemplate?.status ?? "PENDING"}
          subtitle={selectedTemplate?.name}
          title={selectedTemplate?.code}
        >
          {selectedTemplate?.description ? <p className="empty-text">{selectedTemplate.description}</p> : null}
          <DetailList
            ariaLabel="Selected template sheets"
            emptyText="No sheets defined for this template."
            items={(selectedTemplate?.sheets ?? []).map((sheet) => ({
              id: sheet.code,
              meta: [sheet.target_table, `${sheet.fields.length} field(s)`],
              status: "ACTIVE",
              title: sheet.code
            }))}
          />
          <DetailList
            ariaLabel="Selected template fields"
            emptyText="No fields defined for this template."
            items={(selectedTemplate?.sheets ?? []).flatMap((sheet) =>
              sheet.fields.map((field) => ({
                id: `${sheet.code}-${field.name}`,
                meta: [sheet.code, field.target_column, field.required ? "Required" : "Optional"],
                status: field.required ? "REQUIRED" : "OPTIONAL",
                title: field.label
              }))
            )}
          />
        </SelectedObjectPanel>
      </section>
    </>
  );
}
