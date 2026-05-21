import { useState } from 'react';

import { useOrderReleaseTemplates } from '../../platform/hooks';
import type { OrderReleaseTemplate } from '../../platform/types';
import { PageHeader } from '../../app/shell';
import { DetailList, MetricGrid, ModuleObjectList, SelectedObjectPanel, StatePanel, StatusChip } from '../../ui/components';
import { booleanStatus } from '../moduleStatus';

function orderReleaseTemplateMeta(item: OrderReleaseTemplate) {
  return [
    item.macro_object_code,
    `v${item.version}`,
    `${item.required_columns.length} required`,
    `${item.optional_columns.length} optional`
  ];
}

export function OrderReleaseGeneratorView({ token }: { token: string }) {
  const templates = useOrderReleaseTemplates(token);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const templateItems = templates.data?.items ?? [];
  const effectiveTemplateId = selectedTemplateId ?? templateItems[0]?.id ?? null;
  const selectedTemplate = templateItems.find((item) => item.id === effectiveTemplateId) ?? null;
  const requiredColumnCount = selectedTemplate?.required_columns.length ?? 0;
  const optionalColumnCount = selectedTemplate?.optional_columns.length ?? 0;
  const defaultCount = selectedTemplate ? Object.keys(selectedTemplate.defaults).length : 0;

  if (templates.isLoading) {
    return <StatePanel>Loading Order Release Generator...</StatePanel>;
  }

  if (templates.isError || !templates.data) {
    return <StatePanel tone="error">Order Release Generator is unavailable.</StatePanel>;
  }

  return (
    <>
      <PageHeader
        description="Order release template, batch, XML preview, artifact, and job orchestration workspace."
        label="Module workspace"
        title="Order Release Generator"
      />

      <MetricGrid
        ariaLabel="Order Release Generator metrics"
        items={[
          { key: "templates", label: "Templates", status: booleanStatus(templates.data.total), value: templates.data.total },
          { key: "required", label: "Required columns", status: booleanStatus(requiredColumnCount), value: requiredColumnCount },
          { key: "optional", label: "Optional columns", status: booleanStatus(optionalColumnCount), value: optionalColumnCount },
          { key: "defaults", label: "Defaults", status: booleanStatus(defaultCount), value: defaultCount }
        ]}
      />

      <section className="module-template" aria-label="Order Release Generator workspace">
        <div className="module-template-main">
          <div className="panel-header">
            <h2>Templates</h2>
            <StatusChip status={templateItems.length ? "ACTIVE" : "EMPTY"} />
          </div>
          <ModuleObjectList
            ariaLabel="Order Release templates"
            emptyText="No Order Release templates available for the current context."
            items={templateItems.map((item) => ({
              id: item.id,
              meta: orderReleaseTemplateMeta(item),
              status: item.status,
              subtitle: item.name,
              title: item.code
            }))}
            onSelect={setSelectedTemplateId}
            selectedId={effectiveTemplateId}
          />
        </div>

        <SelectedObjectPanel
          emptyText="Select a template to inspect backend-owned Order Release metadata."
          fields={
            selectedTemplate
              ? [
                  { label: "Macro object", value: selectedTemplate.macro_object_code },
                  { label: "Version", value: selectedTemplate.version },
                  { label: "Required columns", value: selectedTemplate.required_columns.length },
                  { label: "Optional columns", value: selectedTemplate.optional_columns.length }
                ]
              : []
          }
          isLoading={templates.isLoading}
          loadingText="Loading selected template..."
          status={selectedTemplate?.status ?? "PENDING"}
          subtitle={selectedTemplate?.name}
          title={selectedTemplate?.code}
        >
          {selectedTemplate?.description ? <p className="empty-text">{selectedTemplate.description}</p> : null}
          <DetailList
            ariaLabel="Selected order release required columns"
            emptyText="No required columns defined for this template."
            items={(selectedTemplate?.required_columns ?? []).map((column) => ({
              id: `required-${column}`,
              meta: ["Required"],
              status: "REQUIRED",
              title: column
            }))}
          />
          <DetailList
            ariaLabel="Selected order release optional columns and defaults"
            emptyText="No optional columns or defaults defined for this template."
            items={[
              ...(selectedTemplate?.optional_columns ?? []).map((column) => ({
                id: `optional-${column}`,
                meta: ["Optional"],
                status: "OPTIONAL",
                title: column
              })),
              ...Object.entries(selectedTemplate?.defaults ?? {}).map(([key, value]) => ({
                id: `default-${key}`,
                meta: [`Default: ${String(value)}`],
                status: "DEFAULT",
                title: key
              }))
            ]}
          />
        </SelectedObjectPanel>
      </section>
    </>
  );
}
