import { useState } from 'react';

import { useIntegrationDefinitionDetail, useIntegrationDefinitions, useIntegrationMappings, useIntegrationPayloadArtifacts, useIntegrationSchemaDocuments, useIntegrationTransformTypes } from '../../platform/hooks';
import type { IntegrationDefinition } from '../../platform/types';
import { MODULE_DESCRIPTIONS } from '../../app/routes/moduleDescriptions';
import { PageHeader } from '../../app/shell';
import { DetailList, MetricGrid, ModuleObjectList, SelectedObjectPanel, StatePanel, StatusChip } from '../../ui/components';
import { booleanStatus } from '../moduleStatus';

function integrationDefinitionMeta(item: IntegrationDefinition) {
  return [item.source_system, `${item.source_format} -> ${item.target_format}`, item.target_system];
}

export function IntegrationMappingView({ token }: { token: string }) {
  const definitions = useIntegrationDefinitions(token);
  const transformTypes = useIntegrationTransformTypes(token);
  const [selectedDefinitionId, setSelectedDefinitionId] = useState<string | null>(null);
  const definitionItems = definitions.data?.items ?? [];
  const effectiveDefinitionId = selectedDefinitionId ?? definitionItems[0]?.id ?? null;
  const definitionDetail = useIntegrationDefinitionDetail(token, effectiveDefinitionId);
  const payloadArtifacts = useIntegrationPayloadArtifacts(token, effectiveDefinitionId);
  const schemaDocuments = useIntegrationSchemaDocuments(token, effectiveDefinitionId);
  const mappings = useIntegrationMappings(token, effectiveDefinitionId);
  const selectedDefinition =
    definitionDetail.data ?? definitionItems.find((item) => item.id === effectiveDefinitionId) ?? null;

  if (definitions.isLoading || transformTypes.isLoading) {
    return <StatePanel>Loading Integration Mapping Studio...</StatePanel>;
  }

  if (definitions.isError || transformTypes.isError || !definitions.data || !transformTypes.data) {
    return <StatePanel tone="error">Integration Mapping Studio is unavailable.</StatePanel>;
  }

  return (
    <>
      <PageHeader
        description={MODULE_DESCRIPTIONS.integration_mapping}
        label="Module workspace"
        title="Integration Mapping Studio"
      />

      <MetricGrid
        ariaLabel="Integration Mapping Studio metrics"
        items={[
          { key: "definitions", label: "Definitions", status: booleanStatus(definitions.data.total), value: definitions.data.total },
          {
            key: "transform_types",
            label: "Transform types",
            status: booleanStatus(transformTypes.data.total),
            value: transformTypes.data.total
          },
          {
            key: "payloads",
            label: "Payloads",
            status: booleanStatus(payloadArtifacts.data?.total ?? 0),
            value: payloadArtifacts.data?.total ?? 0
          },
          {
            key: "mappings",
            label: "Mappings",
            status: booleanStatus(mappings.data?.total ?? 0),
            value: mappings.data?.total ?? 0
          }
        ]}
      />

      <section className="module-template" aria-label="Integration Mapping Studio workspace">
        <div className="module-template-main">
          <div className="panel-header">
            <h2>Definitions</h2>
            <StatusChip status={definitionItems.length ? "ACTIVE" : "EMPTY"} />
          </div>
          <ModuleObjectList
            emptyText="No Integration Mapping definitions available for the current context."
            items={definitionItems.map((item) => ({
              id: item.id,
              meta: integrationDefinitionMeta(item),
              status: item.status,
              subtitle: item.name,
              title: item.code
            }))}
            onSelect={setSelectedDefinitionId}
            selectedId={effectiveDefinitionId}
          />
        </div>

        <SelectedObjectPanel
          emptyText="Select a definition to inspect backend-owned mapping metadata."
          fields={
            selectedDefinition
              ? [
                  { label: "Source system", value: selectedDefinition.source_system },
                  { label: "Target system", value: selectedDefinition.target_system },
                  { label: "Source format", value: selectedDefinition.source_format },
                  { label: "Target format", value: selectedDefinition.target_format }
                ]
              : []
          }
          isLoading={definitionDetail.isLoading && Boolean(effectiveDefinitionId)}
          loadingText="Loading selected definition..."
          status={selectedDefinition?.status ?? "PENDING"}
          subtitle={selectedDefinition?.name}
          title={selectedDefinition?.code}
        >
          {selectedDefinition?.description ? <p className="empty-text">{selectedDefinition.description}</p> : null}
          <DetailList
            ariaLabel="Selected definition payload artifacts"
            emptyText="No payload artifacts linked to this definition."
            items={(payloadArtifacts.data?.items ?? []).map((artifact) => ({
              id: artifact.id,
              meta: [artifact.payload_role, artifact.payload_format, `${artifact.size_bytes} bytes`],
              status: artifact.content_type,
              title: artifact.file_name
            }))}
          />
          <DetailList
            ariaLabel="Selected definition schema documents"
            emptyText="No schema documents parsed for this definition."
            items={(schemaDocuments.data?.items ?? []).map((schema) => ({
              id: schema.id,
              meta: [schema.payload_format, `${schema.node_count} node(s)`],
              status: schema.status,
              title: schema.root_name
            }))}
          />
          <DetailList
            ariaLabel="Selected definition mappings"
            emptyText="No mappings defined for this definition."
            items={(mappings.data?.items ?? []).map((mapping) => ({
              id: mapping.id,
              meta: [mapping.source_path, mapping.transform_type],
              status: mapping.status,
              title: mapping.target_path
            }))}
          />
        </SelectedObjectPanel>
      </section>
    </>
  );
}
