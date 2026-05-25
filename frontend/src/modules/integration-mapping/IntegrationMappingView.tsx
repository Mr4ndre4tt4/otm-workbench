import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import {
  createIntegrationDefinition,
  createIntegrationEndpoint,
  createIntegrationJoin,
  createIntegrationJoinBinding,
  createIntegrationLookup,
  createIntegrationLoop,
  createIntegrationMapping,
  createIntegrationPayloadArtifact,
  createIntegrationSchemaDocument,
  createIntegrationSystem,
  downloadBackendArtifact,
  generateIntegrationSpec,
  previewIntegrationDefinition,
  useIntegrationArtifacts,
  useIntegrationDefinitionDetail,
  useIntegrationDefinitions,
  useIntegrationJoinBindings,
  useIntegrationJoins,
  useIntegrationLookups,
  useIntegrationLoops,
  useIntegrationMappings,
  useIntegrationPayloadArtifacts,
  useIntegrationSchemaDocuments,
  useIntegrationSchemaNodes,
  useIntegrationEndpoints,
  useIntegrationSystems,
  useIntegrationTransformTypes,
  validateIntegrationDefinition
} from '../../platform/hooks';
import { ApiError } from '../../platform/api';
import type { IntegrationDefinition, IntegrationSchemaNode, IntegrationValidationResult } from '../../platform/types';
import { MODULE_DESCRIPTIONS } from '../../app/routes/moduleDescriptions';
import { PageHeader } from '../../app/shell';
import {
  ArtifactList,
  Button,
  DetailList,
  FeedbackMessage,
  MetricGrid,
  ModuleObjectList,
  ModuleWorkspaceLayout,
  OperationalPanel,
  SelectedObjectPanel,
  StatePanel,
  StatusChip
} from '../../ui/components';
import { booleanStatus } from '../moduleStatus';

function integrationDefinitionMeta(item: IntegrationDefinition) {
  return [item.source_system, `${item.source_format} -> ${item.target_format}`, item.target_system];
}

function readinessStatus(value?: boolean) {
  if (value === undefined) return "UNKNOWN";
  return value ? "READY" : "BLOCKED";
}

const integrationWorkflowStages = [
  { id: "systems", title: "Systems & endpoints", status: "1" },
  { id: "definition", title: "Definition", status: "2" },
  { id: "payloads", title: "Payloads & schemas", status: "3" },
  { id: "rules", title: "Mapping rules", status: "4" },
  { id: "definitions", title: "Definitions list", status: "5" }
] as const;

type IntegrationWorkflowStage = (typeof integrationWorkflowStages)[number]["id"];
type IntegrationReviewRow = {
  blocker?: string;
  group: string;
  id: string;
  policy: string;
  source: string;
  status: string;
  target: string;
  transform: string;
};

type IntegrationJoinBindingReview = {
  hops: Array<{ result_alias: string }>;
  id: string;
  name: string;
  root_collection_path: string;
  status: string;
  target_collection_path: string;
};

function mappingReviewGroup(targetPath: string) {
  const normalized = targetPath.toLowerCase();
  if (normalized.includes("entregas") || normalized.includes("deliveries") || normalized.includes("delivery")) {
    return "Entregas loop";
  }
  return "Header";
}

function buildIntegrationReviewRows({
  joins,
  joinBindings,
  lookups,
  loops,
  mappings,
  validationResult
}: {
  joins: Array<{ id: string; left_path: string; name: string; operator: string; right_path: string; status: string }>;
  joinBindings: IntegrationJoinBindingReview[];
  lookups: Array<{ id: string; input_path: string; lookup_type: string; name: string; output_path: string; status: string }>;
  loops: Array<{ id: string; name: string; source_collection_path: string; status: string; target_collection_path: string }>;
  mappings: Array<{ id: string; source_path: string; status: string; target_path: string; transform_type: string }>;
  validationResult: IntegrationValidationResult | null;
}) {
  const validationStatus = validationResult
    ? validationResult.readiness?.preview_executable
      ? "EXECUTABLE"
      : "BLOCKED"
    : "NEEDS_VALIDATION";
  const rows: IntegrationReviewRow[] = [
    ...mappings.map((mapping) => ({
      group: mappingReviewGroup(mapping.target_path),
      id: `mapping-${mapping.id}`,
      policy: validationResult ? "Validation checked" : "Run validation",
      source: mapping.source_path,
      status: validationStatus === "BLOCKED" ? "BLOCKED" : mapping.status === "ACTIVE" ? validationStatus : mapping.status,
      target: mapping.target_path,
      transform: mapping.transform_type
    })),
    ...loops.map((loop) => ({
      group: "Entregas loop",
      id: `loop-${loop.id}`,
      policy: "Loop scope",
      source: loop.source_collection_path,
      status: loop.status,
      target: loop.target_collection_path,
      transform: loop.name
    })),
    ...joins.map((join) => ({
      blocker: join.left_path === join.right_path ? "JOIN_PATHS_MUST_DIFFER" : undefined,
      group: "Joins",
      id: `join-${join.id}`,
      policy: join.operator,
      source: join.left_path,
      status: join.left_path === join.right_path ? "BLOCKED" : join.status,
      target: join.right_path,
      transform: join.name
    })),
    ...joinBindings.map((binding) => ({
      group: "Join bindings",
      id: `join-binding-${binding.id}`,
      policy: `${binding.hops.map((hop) => hop.result_alias).filter(Boolean).join(", ")} · ${binding.hops.length} hop(s)`,
      source: binding.root_collection_path,
      status: binding.status,
      target: binding.target_collection_path,
      transform: binding.name
    })),
    ...lookups.map((lookup) => ({
      group: "Lookups",
      id: `lookup-${lookup.id}`,
      policy: lookup.lookup_type,
      source: lookup.input_path,
      status: lookup.status,
      target: lookup.output_path,
      transform: lookup.name
    })),
    ...mappings.map((mapping) => ({
      group: "Transforms",
      id: `transform-${mapping.id}`,
      policy: mapping.transform_type === "DIRECT" ? "No config required" : "Config required",
      source: mapping.source_path,
      status: mapping.status,
      target: mapping.target_path,
      transform: mapping.transform_type
    })),
    {
      blocker: "COUNT_DISTINCT_AND_FILTERED_AGGREGATIONS_PENDING_OTM_145",
      group: "Aggregations",
      id: "aggregation-future-scope",
      policy: "Future scope",
      source: "No aggregation rules defined.",
      status: "FUTURE_SCOPE",
      target: "QtdNFe / QtdCTe style fields",
      transform: "COUNT_DISTINCT"
    },
    {
      blocker: "RESPONSE_HANDLING_MODEL_PENDING",
      group: "Response Handling",
      id: "response-handling-future-scope",
      policy: "Future scope",
      source: "No response handling rules defined.",
      status: "FUTURE_SCOPE",
      target: "Success/error response paths",
      transform: "RESPONSE_POLICY"
    }
  ];

  return rows;
}

function IntegrationGroupedReview({ rows }: { rows: IntegrationReviewRow[] }) {
  const groups = ["Header", "Entregas loop", "Lookups", "Joins", "Join bindings", "Transforms", "Aggregations", "Response Handling"];

  return (
    <section className="integration-review-panel" aria-label="Integration mapping grouped executable review">
      <div className="panel-header">
        <h3>Grouped executable review</h3>
        <StatusChip status={rows.some((row) => row.status === "BLOCKED") ? "BLOCKED" : "REVIEW"} />
      </div>
      <div className="integration-review-grid">
        {groups.map((group) => {
          const groupRows = rows.filter((row) => row.group === group);
          return (
            <div className="integration-review-group" key={group}>
              <div className="integration-review-group-header">
                <strong>{group}</strong>
                <StatusChip status={groupRows.some((row) => row.status === "BLOCKED") ? "BLOCKED" : groupRows.length ? "READY" : "EMPTY"} />
              </div>
              {groupRows.length ? (
                <div className="integration-review-rows">
                  {groupRows.map((row) => (
                    <div className="integration-review-row" key={row.id}>
                      <div>
                        <strong>{row.transform}</strong>
                        <span>{row.policy}</span>
                      </div>
                      <span>{row.source}</span>
                      <span>{row.target}</span>
                      <span>{row.blocker ?? "No blocker"}</span>
                      <StatusChip status={row.status} />
                    </div>
                  ))}
                </div>
              ) : (
                <p className="empty-text">No rows in this group.</p>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}

function SchemaNodeSelect({
  label,
  nodes,
  onSelect
}: {
  label: string;
  nodes: IntegrationSchemaNode[];
  onSelect: (path: string) => void;
}) {
  return (
    <label>
      {label}
      <select disabled={!nodes.length} onChange={(event) => onSelect(event.target.value)} value="">
        <option value="">Select schema node</option>
        {nodes.map((node) => (
          <option key={node.id} value={node.path}>
            {node.path}
          </option>
        ))}
      </select>
    </label>
  );
}

function collectionNodes(nodes: IntegrationSchemaNode[]) {
  return nodes.filter((node) => ["array", "object"].includes(node.node_type.toLowerCase()));
}

export function IntegrationMappingView({ token }: { token: string }) {
  const queryClient = useQueryClient();
  const definitions = useIntegrationDefinitions(token);
  const systems = useIntegrationSystems(token);
  const transformTypes = useIntegrationTransformTypes(token);
  const [selectedDefinitionId, setSelectedDefinitionId] = useState<string | null>(null);
  const [activeStage, setActiveStage] = useState<IntegrationWorkflowStage>("systems");
  const [operationMessage, setOperationMessage] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<IntegrationValidationResult | null>(null);
  const [isMutating, setIsMutating] = useState(false);
  const [downloadingArtifactId, setDownloadingArtifactId] = useState<string | null>(null);
  const [definitionCode, setDefinitionCode] = useState('');
  const [definitionName, setDefinitionName] = useState('');
  const [definitionDescription, setDefinitionDescription] = useState('');
  const [sourceSystem, setSourceSystem] = useState('');
  const [targetSystem, setTargetSystem] = useState('');
  const [sourceFormat, setSourceFormat] = useState('XML');
  const [targetFormat, setTargetFormat] = useState('JSON');
  const [sourceSchemaId, setSourceSchemaId] = useState('');
  const [targetSchemaId, setTargetSchemaId] = useState('');
  const [sourcePath, setSourcePath] = useState('');
  const [targetPath, setTargetPath] = useState('');
  const [transformType, setTransformType] = useState('DIRECT');
  const [mappingSourceAlias, setMappingSourceAlias] = useState('');
  const [mappingDescription, setMappingDescription] = useState('');
  const [systemCode, setSystemCode] = useState('');
  const [systemName, setSystemName] = useState('');
  const [systemType, setSystemType] = useState('EXTERNAL_API');
  const [systemBaseUrl, setSystemBaseUrl] = useState('');
  const [systemDescription, setSystemDescription] = useState('');
  const [endpointSystemId, setEndpointSystemId] = useState('');
  const [endpointCode, setEndpointCode] = useState('');
  const [endpointName, setEndpointName] = useState('');
  const [endpointPath, setEndpointPath] = useState('');
  const [endpointMethod, setEndpointMethod] = useState('POST');
  const [endpointPayloadFormat, setEndpointPayloadFormat] = useState('JSON');
  const [endpointDescription, setEndpointDescription] = useState('');
  const [payloadRole, setPayloadRole] = useState('SOURCE_SAMPLE');
  const [payloadFormat, setPayloadFormat] = useState('XML');
  const [payloadFileName, setPayloadFileName] = useState('');
  const [payloadDescription, setPayloadDescription] = useState('');
  const [payloadContent, setPayloadContent] = useState('');
  const [loopSourceSchemaId, setLoopSourceSchemaId] = useState('');
  const [loopTargetSchemaId, setLoopTargetSchemaId] = useState('');
  const [loopName, setLoopName] = useState('');
  const [loopSourceCollectionPath, setLoopSourceCollectionPath] = useState('');
  const [loopTargetCollectionPath, setLoopTargetCollectionPath] = useState('');
  const [loopDescription, setLoopDescription] = useState('');
  const [joinSourceSchemaId, setJoinSourceSchemaId] = useState('');
  const [joinName, setJoinName] = useState('');
  const [joinLeftPath, setJoinLeftPath] = useState('');
  const [joinRightPath, setJoinRightPath] = useState('');
  const [joinOperator, setJoinOperator] = useState('EQ');
  const [joinDescription, setJoinDescription] = useState('');
  const [joinBindingSourceSchemaId, setJoinBindingSourceSchemaId] = useState('');
  const [joinBindingName, setJoinBindingName] = useState('');
  const [joinBindingRootCollectionPath, setJoinBindingRootCollectionPath] = useState('');
  const [joinBindingTargetCollectionPath, setJoinBindingTargetCollectionPath] = useState('');
  const [joinBindingHop1LeftCollectionPath, setJoinBindingHop1LeftCollectionPath] = useState('');
  const [joinBindingHop1LeftValuePath, setJoinBindingHop1LeftValuePath] = useState('');
  const [joinBindingHop1RightCollectionPath, setJoinBindingHop1RightCollectionPath] = useState('');
  const [joinBindingHop1RightValuePath, setJoinBindingHop1RightValuePath] = useState('');
  const [joinBindingHop1Alias, setJoinBindingHop1Alias] = useState('');
  const [joinBindingHop2LeftCollectionPath, setJoinBindingHop2LeftCollectionPath] = useState('');
  const [joinBindingHop2LeftValuePath, setJoinBindingHop2LeftValuePath] = useState('');
  const [joinBindingHop2RightCollectionPath, setJoinBindingHop2RightCollectionPath] = useState('');
  const [joinBindingHop2RightValuePath, setJoinBindingHop2RightValuePath] = useState('');
  const [joinBindingHop2Alias, setJoinBindingHop2Alias] = useState('');
  const [joinBindingDescription, setJoinBindingDescription] = useState('');
  const [lookupSourceSchemaId, setLookupSourceSchemaId] = useState('');
  const [lookupTargetSchemaId, setLookupTargetSchemaId] = useState('');
  const [lookupName, setLookupName] = useState('');
  const [lookupInputPath, setLookupInputPath] = useState('');
  const [lookupOutputPath, setLookupOutputPath] = useState('');
  const [lookupType, setLookupType] = useState('MOCK');
  const [lookupDescription, setLookupDescription] = useState('');
  const [lookupMockResponseJson, setLookupMockResponseJson] = useState('');
  const definitionItems = definitions.data?.items ?? [];
  const systemItems = systems.data?.items ?? [];
  const selectedEndpointSystemId = endpointSystemId || systemItems[0]?.id || null;
  const endpoints = useIntegrationEndpoints(token, selectedEndpointSystemId);
  const effectiveDefinitionId = selectedDefinitionId ?? definitionItems[0]?.id ?? null;
  const definitionDetail = useIntegrationDefinitionDetail(token, effectiveDefinitionId);
  const payloadArtifacts = useIntegrationPayloadArtifacts(token, effectiveDefinitionId);
  const schemaDocuments = useIntegrationSchemaDocuments(token, effectiveDefinitionId);
  const sourceSchemaNodes = useIntegrationSchemaNodes(token, sourceSchemaId || null);
  const targetSchemaNodes = useIntegrationSchemaNodes(token, targetSchemaId || null);
  const loopSourceSchemaNodes = useIntegrationSchemaNodes(token, loopSourceSchemaId || null);
  const loopTargetSchemaNodes = useIntegrationSchemaNodes(token, loopTargetSchemaId || null);
  const joinSourceSchemaNodes = useIntegrationSchemaNodes(token, joinSourceSchemaId || null);
  const joinBindingSourceSchemaNodes = useIntegrationSchemaNodes(token, joinBindingSourceSchemaId || null);
  const lookupSourceSchemaNodes = useIntegrationSchemaNodes(token, lookupSourceSchemaId || null);
  const lookupTargetSchemaNodes = useIntegrationSchemaNodes(token, lookupTargetSchemaId || null);
  const mappings = useIntegrationMappings(token, effectiveDefinitionId);
  const loops = useIntegrationLoops(token, effectiveDefinitionId);
  const joins = useIntegrationJoins(token, effectiveDefinitionId);
  const joinBindings = useIntegrationJoinBindings(token, effectiveDefinitionId);
  const lookups = useIntegrationLookups(token, effectiveDefinitionId);
  const artifacts = useIntegrationArtifacts(token, effectiveDefinitionId);
  const selectedDefinition =
    definitionDetail.data ?? definitionItems.find((item) => item.id === effectiveDefinitionId) ?? null;
  const integrationReviewRows = buildIntegrationReviewRows({
    joins: joins.data?.items ?? [],
    joinBindings: joinBindings.data?.items ?? [],
    lookups: lookups.data?.items ?? [],
    loops: loops.data?.items ?? [],
    mappings: mappings.data?.items ?? [],
    validationResult
  });

  const refreshDefinitionData = async (definitionId = effectiveDefinitionId) => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["modules", "integration-mapping", "definitions"] }),
      queryClient.invalidateQueries({ queryKey: ["modules", "integration-mapping", "definitions", definitionId] }),
      queryClient.invalidateQueries({ queryKey: ["modules", "integration-mapping", "definitions", definitionId, "payload-artifacts"] }),
      queryClient.invalidateQueries({ queryKey: ["modules", "integration-mapping", "definitions", definitionId, "schema-documents"] }),
      queryClient.invalidateQueries({ queryKey: ["modules", "integration-mapping", "definitions", definitionId, "mappings"] }),
      queryClient.invalidateQueries({ queryKey: ["modules", "integration-mapping", "definitions", definitionId, "loops"] }),
      queryClient.invalidateQueries({ queryKey: ["modules", "integration-mapping", "definitions", definitionId, "joins"] }),
      queryClient.invalidateQueries({ queryKey: ["modules", "integration-mapping", "definitions", definitionId, "join-bindings"] }),
      queryClient.invalidateQueries({ queryKey: ["modules", "integration-mapping", "definitions", definitionId, "lookups"] }),
      queryClient.invalidateQueries({ queryKey: ["modules", "integration-mapping", "definitions", definitionId, "artifacts"] })
    ]);
  };

  const refreshSystemData = async (systemId = selectedEndpointSystemId) => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["modules", "integration-mapping", "systems"] }),
      queryClient.invalidateQueries({ queryKey: ["modules", "integration-mapping", "systems", systemId, "endpoints"] })
    ]);
  };

  const resetMappingRuleDrafts = () => {
    setSourceSchemaId('');
    setTargetSchemaId('');
    setSourcePath('');
    setTargetPath('');
    setTransformType('DIRECT');
    setMappingSourceAlias('');
    setMappingDescription('');
    setLoopSourceSchemaId('');
    setLoopTargetSchemaId('');
    setLoopName('');
    setLoopSourceCollectionPath('');
    setLoopTargetCollectionPath('');
    setLoopDescription('');
    setJoinSourceSchemaId('');
    setJoinName('');
    setJoinLeftPath('');
    setJoinRightPath('');
    setJoinOperator('EQ');
    setJoinDescription('');
    setJoinBindingSourceSchemaId('');
    setJoinBindingName('');
    setJoinBindingRootCollectionPath('');
    setJoinBindingTargetCollectionPath('');
    setJoinBindingHop1LeftCollectionPath('');
    setJoinBindingHop1LeftValuePath('');
    setJoinBindingHop1RightCollectionPath('');
    setJoinBindingHop1RightValuePath('');
    setJoinBindingHop1Alias('');
    setJoinBindingHop2LeftCollectionPath('');
    setJoinBindingHop2LeftValuePath('');
    setJoinBindingHop2RightCollectionPath('');
    setJoinBindingHop2RightValuePath('');
    setJoinBindingHop2Alias('');
    setJoinBindingDescription('');
    setLookupSourceSchemaId('');
    setLookupTargetSchemaId('');
    setLookupName('');
    setLookupInputPath('');
    setLookupOutputPath('');
    setLookupType('MOCK');
    setLookupDescription('');
    setLookupMockResponseJson('');
    setOperationMessage(null);
    setOperationError(null);
    setValidationResult(null);
  };

  const clearDefinitionWorkspaceState = () => {
    setPayloadRole('SOURCE_SAMPLE');
    setPayloadFormat('XML');
    setPayloadFileName('');
    setPayloadDescription('');
    setPayloadContent('');
    setDownloadingArtifactId(null);
    resetMappingRuleDrafts();
  };

  const handleSelectDefinition = (definitionId: string) => {
    if (definitionId === effectiveDefinitionId) return;
    setSelectedDefinitionId(definitionId);
    clearDefinitionWorkspaceState();
  };

  const handleCreateSystem = async () => {
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const system = await createIntegrationSystem(token, {
        base_url: systemBaseUrl.trim(),
        code: systemCode.trim(),
        description: systemDescription.trim(),
        name: systemName.trim(),
        system_type: systemType
      });
      setEndpointSystemId(system.id);
      setSystemCode('');
      setSystemName('');
      setSystemBaseUrl('');
      setSystemDescription('');
      setOperationMessage(`Created system ${system.code}.`);
      await refreshSystemData(system.id);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create system.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateEndpoint = async () => {
    if (!selectedEndpointSystemId) {
      setOperationError("Select a system before creating an endpoint.");
      return;
    }
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const endpoint = await createIntegrationEndpoint(token, selectedEndpointSystemId, {
        code: endpointCode.trim(),
        description: endpointDescription.trim(),
        method: endpointMethod,
        name: endpointName.trim(),
        path: endpointPath.trim(),
        payload_format: endpointPayloadFormat
      });
      setEndpointCode('');
      setEndpointName('');
      setEndpointPath('');
      setEndpointDescription('');
      setOperationMessage(`Created endpoint ${endpoint.code}.`);
      await refreshSystemData(selectedEndpointSystemId);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create endpoint.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateDefinition = async () => {
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const definition = await createIntegrationDefinition(token, {
        code: definitionCode.trim(),
        description: definitionDescription.trim(),
        name: definitionName.trim(),
        source_format: sourceFormat,
        source_system: sourceSystem.trim(),
        target_format: targetFormat,
        target_system: targetSystem.trim()
      });
      setSelectedDefinitionId(definition.id);
      setDefinitionCode('');
      setDefinitionName('');
      setDefinitionDescription('');
      setSourceSystem('');
      setTargetSystem('');
      setOperationMessage(`Created definition ${definition.code}.`);
      await refreshDefinitionData(definition.id);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create definition.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateSyntheticPayloadSamples = async () => {
    if (!effectiveDefinitionId) {
      setOperationError("Select a definition before creating payload samples.");
      return;
    }
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const source = await createIntegrationPayloadArtifact(token, effectiveDefinitionId, {
        content:
          "<Transmission><Shipment><ShipmentGid>DEMO.SHIPMENT_001</ShipmentGid><ShipmentStop><StopSequence>1</StopSequence></ShipmentStop></Shipment></Transmission>",
        description: "Synthetic OTM PlannedShipment source sample.",
        file_name: "planned_shipment_synthetic.xml",
        payload_format: "XML",
        payload_role: "SOURCE_SAMPLE"
      });
      const target = await createIntegrationPayloadArtifact(token, effectiveDefinitionId, {
        content: '{"header":{"shipmentId":"DEMO"},"deliveries":[{"sequence":1}]}',
        description: "Synthetic external delivery target sample.",
        file_name: "external_delivery_synthetic.json",
        payload_format: "JSON",
        payload_role: "TARGET_SAMPLE"
      });
      const sourceSchema = await createIntegrationSchemaDocument(token, source.id);
      const targetSchema = await createIntegrationSchemaDocument(token, target.id);
      setSourceSchemaId(sourceSchema.id);
      setTargetSchemaId(targetSchema.id);
      setOperationMessage("Synthetic payload samples and schema documents created.");
      await refreshDefinitionData(effectiveDefinitionId);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create synthetic payload samples.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateManualPayloadAndSchema = async () => {
    if (!effectiveDefinitionId) {
      setOperationError("Select a definition before creating payload artifacts.");
      return;
    }
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const payloadArtifact = await createIntegrationPayloadArtifact(token, effectiveDefinitionId, {
        content: payloadContent,
        description: payloadDescription.trim(),
        file_name: payloadFileName.trim(),
        payload_format: payloadFormat,
        payload_role: payloadRole
      });
      const schema = await createIntegrationSchemaDocument(token, payloadArtifact.id);
      if (payloadRole === "SOURCE_SAMPLE") {
        setSourceSchemaId(schema.id);
      }
      if (payloadRole === "TARGET_SAMPLE") {
        setTargetSchemaId(schema.id);
      }
      setPayloadFileName('');
      setPayloadDescription('');
      setPayloadContent('');
      setOperationMessage(`Payload ${payloadArtifact.file_name} and schema ${schema.root_name} created.`);
      await refreshDefinitionData(effectiveDefinitionId);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create payload and schema.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateMapping = async () => {
    if (!effectiveDefinitionId) {
      setOperationError("Select a definition before creating a mapping.");
      return;
    }
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const mapping = await createIntegrationMapping(token, effectiveDefinitionId, {
        description: mappingDescription.trim(),
        sequence_index: 10,
        source_path: sourcePath.trim(),
        source_schema_document_id: sourceSchemaId,
        target_path: targetPath.trim(),
        target_schema_document_id: targetSchemaId,
        transform_config: mappingSourceAlias ? { source_alias: mappingSourceAlias } : {},
        transform_type: transformType
      });
      setOperationMessage(`Created mapping ${mapping.target_path}.`);
      setSourcePath('');
      setTargetPath('');
      setMappingSourceAlias('');
      setMappingDescription('');
      await refreshDefinitionData(effectiveDefinitionId);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create mapping.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateLoop = async () => {
    if (!effectiveDefinitionId) {
      setOperationError("Select a definition before creating a loop.");
      return;
    }
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const loop = await createIntegrationLoop(token, effectiveDefinitionId, {
        description: loopDescription.trim(),
        name: loopName.trim(),
        sequence_index: 20,
        source_collection_path: loopSourceCollectionPath.trim(),
        source_schema_document_id: loopSourceSchemaId,
        target_collection_path: loopTargetCollectionPath.trim(),
        target_schema_document_id: loopTargetSchemaId
      });
      setOperationMessage(`Created loop ${loop.name}.`);
      setLoopName('');
      setLoopSourceCollectionPath('');
      setLoopTargetCollectionPath('');
      setLoopDescription('');
      await refreshDefinitionData(effectiveDefinitionId);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create loop.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateJoin = async () => {
    if (!effectiveDefinitionId) {
      setOperationError("Select a definition before creating a join.");
      return;
    }
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const join = await createIntegrationJoin(token, effectiveDefinitionId, {
        description: joinDescription.trim(),
        left_path: joinLeftPath.trim(),
        name: joinName.trim(),
        operator: joinOperator,
        right_path: joinRightPath.trim(),
        sequence_index: 30,
        source_schema_document_id: joinSourceSchemaId
      });
      setOperationMessage(`Created join ${join.name}.`);
      setJoinName('');
      setJoinLeftPath('');
      setJoinRightPath('');
      setJoinDescription('');
      await refreshDefinitionData(effectiveDefinitionId);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create join.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateJoinBinding = async () => {
    if (!effectiveDefinitionId) {
      setOperationError("Select a definition before creating a join binding.");
      return;
    }
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const binding = await createIntegrationJoinBinding(token, effectiveDefinitionId, {
        description: joinBindingDescription.trim(),
        hops: [
          {
            hop_sequence: 1,
            left_collection_path: joinBindingHop1LeftCollectionPath.trim(),
            left_value_path: joinBindingHop1LeftValuePath.trim(),
            operator: "EQ",
            result_alias: joinBindingHop1Alias.trim(),
            right_collection_path: joinBindingHop1RightCollectionPath.trim(),
            right_value_path: joinBindingHop1RightValuePath.trim()
          },
          {
            hop_sequence: 2,
            left_collection_path: joinBindingHop2LeftCollectionPath.trim(),
            left_value_path: joinBindingHop2LeftValuePath.trim(),
            operator: "EQ",
            result_alias: joinBindingHop2Alias.trim(),
            right_collection_path: joinBindingHop2RightCollectionPath.trim(),
            right_value_path: joinBindingHop2RightValuePath.trim()
          }
        ],
        name: joinBindingName.trim(),
        root_collection_path: joinBindingRootCollectionPath.trim(),
        sequence_index: 35,
        source_schema_document_id: joinBindingSourceSchemaId,
        target_collection_path: joinBindingTargetCollectionPath.trim()
      });
      setOperationMessage(`Created join binding ${binding.name}.`);
      setJoinBindingName('');
      setJoinBindingRootCollectionPath('');
      setJoinBindingTargetCollectionPath('');
      setJoinBindingHop1LeftCollectionPath('');
      setJoinBindingHop1LeftValuePath('');
      setJoinBindingHop1RightCollectionPath('');
      setJoinBindingHop1RightValuePath('');
      setJoinBindingHop1Alias('');
      setJoinBindingHop2LeftCollectionPath('');
      setJoinBindingHop2LeftValuePath('');
      setJoinBindingHop2RightCollectionPath('');
      setJoinBindingHop2RightValuePath('');
      setJoinBindingHop2Alias('');
      setJoinBindingDescription('');
      await refreshDefinitionData(effectiveDefinitionId);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create join binding.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateLookup = async () => {
    if (!effectiveDefinitionId) {
      setOperationError("Select a definition before creating a lookup.");
      return;
    }
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const lookup = await createIntegrationLookup(token, effectiveDefinitionId, {
        description: lookupDescription.trim(),
        input_path: lookupInputPath.trim(),
        lookup_type: lookupType,
        mock_response_json: lookupMockResponseJson,
        name: lookupName.trim(),
        output_path: lookupOutputPath.trim(),
        sequence_index: 40,
        source_schema_document_id: lookupSourceSchemaId,
        target_schema_document_id: lookupTargetSchemaId
      });
      setOperationMessage(`Created lookup ${lookup.name}.`);
      setLookupName('');
      setLookupInputPath('');
      setLookupOutputPath('');
      setLookupDescription('');
      setLookupMockResponseJson('');
      await refreshDefinitionData(effectiveDefinitionId);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create lookup.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleValidateDefinition = async () => {
    if (!effectiveDefinitionId) return;
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const validation = await validateIntegrationDefinition(token, effectiveDefinitionId);
      setValidationResult(validation);
      setOperationMessage(`Validation ${validation.is_valid ? "passed" : "failed"} with ${validation.issue_count} issue(s).`);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not validate definition.");
    } finally {
      setIsMutating(false);
    }
  };

  const handlePreviewDefinition = async () => {
    if (!effectiveDefinitionId) return;
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const preview = await previewIntegrationDefinition(token, effectiveDefinitionId);
      setValidationResult(preview.validation);
      setOperationMessage(`Preview artifact ${preview.artifact_id} generated by job ${preview.job_id}.`);
      await refreshDefinitionData(effectiveDefinitionId);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not preview definition.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleGenerateSpec = async () => {
    if (!effectiveDefinitionId) return;
    setIsMutating(true);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const spec = await generateIntegrationSpec(token, effectiveDefinitionId);
      if (spec.validation) {
        setValidationResult(spec.validation);
      }
      setOperationMessage(`Spec artifact ${spec.artifact_id} generated by job ${spec.job_id}.`);
      await refreshDefinitionData(effectiveDefinitionId);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not generate spec.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleDownloadArtifact = async (artifactId: string, href: string, fallbackName: string) => {
    setIsMutating(true);
    setDownloadingArtifactId(artifactId);
    setOperationMessage(null);
    setOperationError(null);
    try {
      const result = await downloadBackendArtifact(token, href);
      const objectUrl = URL.createObjectURL(result.blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = result.filename ?? fallbackName;
      link.click();
      URL.revokeObjectURL(objectUrl);
      setOperationMessage(`Download started: ${result.filename ?? fallbackName}.`);
    } catch (error) {
      if (error instanceof ApiError) {
        setOperationError(error.message);
      } else {
        setOperationError("Could not download artifact.");
      }
    } finally {
      setDownloadingArtifactId(null);
      setIsMutating(false);
    }
  };

  if (definitions.isLoading || systems.isLoading || transformTypes.isLoading) {
    return <StatePanel>Loading Integration Mapping Studio...</StatePanel>;
  }

  if (definitions.isError || systems.isError || transformTypes.isError || !definitions.data || !systems.data || !transformTypes.data) {
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
            label: "Systems",
            status: booleanStatus(systems.data.total),
            value: systems.data.total
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

      {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
      {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

      <ModuleWorkspaceLayout
        ariaLabel="Integration Mapping Studio workspace"
        side={
          <SelectedObjectPanel
            ariaLabel="Selected integration mapping definition"
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
            <div className="integration-action-bar">
              <Button disabled={!effectiveDefinitionId || isMutating} onClick={handleCreateSyntheticPayloadSamples} variant="primary">
                Create synthetic payload samples
              </Button>
              <Button disabled={!effectiveDefinitionId || isMutating} onClick={handleValidateDefinition}>
                Validate definition
              </Button>
              <Button disabled={!effectiveDefinitionId || isMutating} onClick={handlePreviewDefinition}>
                Preview definition
              </Button>
              <Button disabled={!effectiveDefinitionId || isMutating} onClick={handleGenerateSpec}>
                Generate spec
              </Button>
            </div>
            <DetailList
              ariaLabel="Integration mapping readiness"
              emptyText="Run backend validation to see specification and preview readiness."
              items={
                validationResult
                  ? [
                      {
                        id: "specification-ready",
                        meta: validationResult.readiness?.specification_blockers.length
                          ? validationResult.readiness.specification_blockers
                          : ["No specification blockers reported"],
                        status: readinessStatus(validationResult.readiness?.specification_ready),
                        title: "Specification readiness"
                      },
                      {
                        id: "preview-executable",
                        meta: validationResult.readiness?.preview_blockers.length
                          ? validationResult.readiness.preview_blockers
                          : [`${validationResult.issue_count} validation issue(s)`],
                        status: readinessStatus(validationResult.readiness?.preview_executable),
                        title: "Preview executable"
                      }
                    ]
                  : []
              }
            />
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
            <DetailList
              ariaLabel="Selected definition loops"
              emptyText="No loops defined for this definition."
              items={(loops.data?.items ?? []).map((loop) => ({
                id: loop.id,
                meta: [loop.source_collection_path, loop.target_collection_path],
                status: loop.status,
                title: loop.name
              }))}
            />
            <DetailList
              ariaLabel="Selected definition joins"
              emptyText="No joins defined for this definition."
              items={(joins.data?.items ?? []).map((join) => ({
                id: join.id,
                meta: [join.left_path, join.operator, join.right_path],
                status: join.status,
                title: join.name
              }))}
            />
            <DetailList
              ariaLabel="Selected definition join bindings"
              emptyText="No join bindings defined for this definition."
              items={(joinBindings.data?.items ?? []).map((binding) => ({
                id: binding.id,
                meta: [
                  binding.root_collection_path,
                  binding.target_collection_path,
                  binding.hops.map((hop) => hop.result_alias).join(", ")
                ],
                status: binding.status,
                title: binding.name
              }))}
            />
            <DetailList
              ariaLabel="Selected definition lookups"
              emptyText="No lookups defined for this definition."
              items={(lookups.data?.items ?? []).map((lookup) => ({
                id: lookup.id,
                meta: [lookup.input_path, lookup.lookup_type, lookup.output_path],
                status: lookup.status,
                title: lookup.name
              }))}
            />
            <section aria-label="Integration mapping generated artifacts" className="integration-generated-artifacts">
              <h3>Generated artifacts</h3>
              {artifacts.isLoading && effectiveDefinitionId ? <p className="empty-text">Loading generated artifacts...</p> : null}
              {!artifacts.isLoading && !(artifacts.data?.items.length ?? 0) ? (
                <p className="empty-text">No generated artifacts for this definition.</p>
              ) : null}
              <ArtifactList
                items={(artifacts.data?.items ?? []).map((artifact) => ({
                  action: artifact.download_url ? (
                    <Button
                      disabled={downloadingArtifactId === artifact.id}
                      onClick={() => void handleDownloadArtifact(artifact.id, artifact.download_url!, artifact.file_name)}
                    >
                      {downloadingArtifactId === artifact.id ? "Downloading..." : "Download"}
                    </Button>
                  ) : undefined,
                  id: artifact.id,
                  meta: [artifact.content_type, `${artifact.size_bytes} bytes`],
                  status: artifact.download_url ? undefined : artifact.sensitivity_level,
                  subtitle: artifact.artifact_type,
                  title: artifact.file_name
                }))}
              />
            </section>
          </SelectedObjectPanel>
        }
        status={definitionItems.length ? "ACTIVE" : "EMPTY"}
        title="Definitions"
      >
        <div className="integration-workflow" aria-label="Integration Mapping workflow">
          {integrationWorkflowStages.map((stage) => (
            <button
              aria-current={activeStage === stage.id ? "step" : undefined}
              className={`integration-workflow-step${activeStage === stage.id ? " integration-workflow-step-active" : ""}`}
              key={stage.id}
              onClick={() => setActiveStage(stage.id)}
              type="button"
            >
              <span>{stage.status}</span>
              <strong>{stage.title}</strong>
            </button>
          ))}
        </div>

        {activeStage === "systems" ? (
        <OperationalPanel
          ariaLabel="Integration system authoring"
          emptyText="Create non-secret system and endpoint metadata."
          hasItems
          status="ACTIVE"
          title="System authoring"
        >
          <form
            className="integration-system-form"
            onSubmit={(event) => {
              event.preventDefault();
              void handleCreateSystem();
            }}
          >
            <label>
              System code
              <input onChange={(event) => setSystemCode(event.target.value)} value={systemCode} />
            </label>
            <label>
              System name
              <input onChange={(event) => setSystemName(event.target.value)} value={systemName} />
            </label>
            <label>
              System type
              <select onChange={(event) => setSystemType(event.target.value)} value={systemType}>
                <option value="EXTERNAL_API">EXTERNAL_API</option>
                <option value="OTM">OTM</option>
                <option value="FILE">FILE</option>
              </select>
            </label>
            <label>
              System base URL
              <input onChange={(event) => setSystemBaseUrl(event.target.value)} value={systemBaseUrl} />
            </label>
            <label className="integration-form-wide">
              System description
              <input onChange={(event) => setSystemDescription(event.target.value)} value={systemDescription} />
            </label>
            <Button disabled={isMutating} type="submit" variant="primary">
              Create system
            </Button>
          </form>
          <DetailList
            ariaLabel="Integration systems"
            emptyText="No integration systems registered."
            items={systemItems.map((system) => ({
              id: system.id,
              meta: [system.name, system.system_type, system.base_url || "No URL"],
              status: system.status,
              title: system.code
            }))}
          />
          <form
            className="integration-endpoint-form"
            onSubmit={(event) => {
              event.preventDefault();
              void handleCreateEndpoint();
            }}
          >
            <label>
              Endpoint system
              <select onChange={(event) => setEndpointSystemId(event.target.value)} value={selectedEndpointSystemId ?? ""}>
                <option value="">Select system</option>
                {systemItems.map((system) => (
                  <option key={system.id} value={system.id}>
                    {system.code}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Endpoint code
              <input onChange={(event) => setEndpointCode(event.target.value)} value={endpointCode} />
            </label>
            <label>
              Endpoint name
              <input onChange={(event) => setEndpointName(event.target.value)} value={endpointName} />
            </label>
            <label>
              Endpoint path
              <input onChange={(event) => setEndpointPath(event.target.value)} value={endpointPath} />
            </label>
            <label>
              Endpoint method
              <select onChange={(event) => setEndpointMethod(event.target.value)} value={endpointMethod}>
                <option value="POST">POST</option>
                <option value="GET">GET</option>
                <option value="PUT">PUT</option>
                <option value="PATCH">PATCH</option>
              </select>
            </label>
            <label>
              Endpoint payload format
              <select onChange={(event) => setEndpointPayloadFormat(event.target.value)} value={endpointPayloadFormat}>
                <option value="JSON">JSON</option>
                <option value="XML">XML</option>
              </select>
            </label>
            <label className="integration-form-wide">
              Endpoint description
              <input onChange={(event) => setEndpointDescription(event.target.value)} value={endpointDescription} />
            </label>
            <Button disabled={!selectedEndpointSystemId || isMutating} type="submit" variant="primary">
              Create endpoint
            </Button>
          </form>
          <DetailList
            ariaLabel="Integration endpoints"
            emptyText="No endpoints registered for the selected system."
            items={(endpoints.data?.items ?? []).map((endpoint) => ({
              id: endpoint.id,
              meta: [endpoint.name, endpoint.method, endpoint.path],
              status: endpoint.payload_format,
              title: endpoint.code
            }))}
          />
        </OperationalPanel>
        ) : null}

        {activeStage === "definition" ? (
        <OperationalPanel
          ariaLabel="Integration definition authoring"
          emptyText="Create a backend-owned integration definition."
          hasItems
          status="ACTIVE"
          title="Definition authoring"
        >
          <form
            className="integration-definition-form"
            onSubmit={(event) => {
              event.preventDefault();
              void handleCreateDefinition();
            }}
          >
            <label>
              Definition code
              <input onChange={(event) => setDefinitionCode(event.target.value)} value={definitionCode} />
            </label>
            <label>
              Definition name
              <input onChange={(event) => setDefinitionName(event.target.value)} value={definitionName} />
            </label>
            <label>
              Source system
              <input onChange={(event) => setSourceSystem(event.target.value)} value={sourceSystem} />
            </label>
            <label>
              Target system
              <input onChange={(event) => setTargetSystem(event.target.value)} value={targetSystem} />
            </label>
            <label>
              Source format
              <select onChange={(event) => setSourceFormat(event.target.value)} value={sourceFormat}>
                <option value="XML">XML</option>
                <option value="JSON">JSON</option>
              </select>
            </label>
            <label>
              Target format
              <select onChange={(event) => setTargetFormat(event.target.value)} value={targetFormat}>
                <option value="JSON">JSON</option>
                <option value="XML">XML</option>
              </select>
            </label>
            <label className="integration-form-wide">
              Definition description
              <input onChange={(event) => setDefinitionDescription(event.target.value)} value={definitionDescription} />
            </label>
            <Button disabled={isMutating} type="submit" variant="primary">
              Create definition
            </Button>
          </form>
        </OperationalPanel>
        ) : null}

        {activeStage === "payloads" ? (
        <OperationalPanel
          ariaLabel="Integration payload and schema authoring"
          emptyText="Create schema documents before adding mappings."
          hasItems
          status={(schemaDocuments.data?.items ?? []).length >= 2 ? "ACTIVE" : "EMPTY"}
          title="Payloads & schemas"
        >
          <form
            className="integration-payload-form"
            onSubmit={(event) => {
              event.preventDefault();
              void handleCreateManualPayloadAndSchema();
            }}
          >
            <label>
              Payload role
              <select onChange={(event) => setPayloadRole(event.target.value)} value={payloadRole}>
                <option value="SOURCE_SAMPLE">SOURCE_SAMPLE</option>
                <option value="TARGET_SAMPLE">TARGET_SAMPLE</option>
              </select>
            </label>
            <label>
              Payload format
              <select onChange={(event) => setPayloadFormat(event.target.value)} value={payloadFormat}>
                <option value="XML">XML</option>
                <option value="JSON">JSON</option>
              </select>
            </label>
            <label>
              Payload file name
              <input onChange={(event) => setPayloadFileName(event.target.value)} value={payloadFileName} />
            </label>
            <label className="integration-form-wide">
              Payload description
              <input onChange={(event) => setPayloadDescription(event.target.value)} value={payloadDescription} />
            </label>
            <label className="integration-form-full">
              Payload content
              <textarea onChange={(event) => setPayloadContent(event.target.value)} value={payloadContent} />
            </label>
            <Button disabled={!effectiveDefinitionId || !payloadFileName.trim() || !payloadContent.trim() || isMutating} type="submit" variant="primary">
              Create payload and schema
            </Button>
          </form>
        </OperationalPanel>
        ) : null}

        {activeStage === "rules" ? (
        <OperationalPanel
          ariaLabel="Integration mapping authoring"
          emptyText="Create schema documents before adding mappings."
          hasItems
          status={(schemaDocuments.data?.items ?? []).length >= 2 ? "ACTIVE" : "EMPTY"}
          title="Mapping rules"
        >
          <div className="integration-action-bar">
            <Button disabled={isMutating} onClick={resetMappingRuleDrafts} type="button">
              Reset mapping rule drafts
            </Button>
          </div>
          <IntegrationGroupedReview rows={integrationReviewRows} />
          <form
            className="integration-mapping-form"
            onSubmit={(event) => {
              event.preventDefault();
              void handleCreateMapping();
            }}
          >
            <label>
              Source schema
              <select onChange={(event) => setSourceSchemaId(event.target.value)} value={sourceSchemaId}>
                <option value="">Select source schema</option>
                {(schemaDocuments.data?.items ?? []).map((schema) => (
                  <option key={schema.id} value={schema.id}>
                    {schema.root_name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Target schema
              <select onChange={(event) => setTargetSchemaId(event.target.value)} value={targetSchemaId}>
                <option value="">Select target schema</option>
                {(schemaDocuments.data?.items ?? []).map((schema) => (
                  <option key={schema.id} value={schema.id}>
                    {schema.root_name}
                  </option>
                ))}
              </select>
            </label>
            <SchemaNodeSelect
              label="Mapping source node"
              nodes={sourceSchemaNodes.data?.items ?? []}
              onSelect={setSourcePath}
            />
            <SchemaNodeSelect
              label="Mapping target node"
              nodes={targetSchemaNodes.data?.items ?? []}
              onSelect={setTargetPath}
            />
            <label>
              Source path
              <input onChange={(event) => setSourcePath(event.target.value)} value={sourcePath} />
            </label>
            <label>
              Target path
              <input onChange={(event) => setTargetPath(event.target.value)} value={targetPath} />
            </label>
            <label>
              Transform type
              <select onChange={(event) => setTransformType(event.target.value)} value={transformType}>
                {transformTypes.data.items.map((item) => (
                  <option key={item.id} value={item.code}>
                    {item.code}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Alias source context
              <select onChange={(event) => setMappingSourceAlias(event.target.value)} value={mappingSourceAlias}>
                <option value="">No join alias</option>
                {(joinBindings.data?.items ?? []).flatMap((binding) =>
                  binding.hops.map((hop) => (
                    <option key={`${binding.id}-${hop.result_alias}`} value={hop.result_alias}>
                      {hop.result_alias}
                    </option>
                  ))
                )}
              </select>
            </label>
            <label className="integration-form-wide">
              Mapping description
              <input onChange={(event) => setMappingDescription(event.target.value)} value={mappingDescription} />
            </label>
            <Button disabled={!effectiveDefinitionId || !sourceSchemaId || !targetSchemaId || isMutating} type="submit" variant="primary">
              Create mapping
            </Button>
          </form>

          <form
            className="integration-loop-form"
            onSubmit={(event) => {
              event.preventDefault();
              void handleCreateLoop();
            }}
          >
            <label>
              Loop source schema
              <select onChange={(event) => setLoopSourceSchemaId(event.target.value)} value={loopSourceSchemaId}>
                <option value="">Select source schema</option>
                {(schemaDocuments.data?.items ?? []).map((schema) => (
                  <option key={schema.id} value={schema.id}>
                    {schema.root_name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Loop target schema
              <select onChange={(event) => setLoopTargetSchemaId(event.target.value)} value={loopTargetSchemaId}>
                <option value="">Select target schema</option>
                {(schemaDocuments.data?.items ?? []).map((schema) => (
                  <option key={schema.id} value={schema.id}>
                    {schema.root_name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Loop name
              <input onChange={(event) => setLoopName(event.target.value)} value={loopName} />
            </label>
            <SchemaNodeSelect
              label="Loop source node"
              nodes={loopSourceSchemaNodes.data?.items ?? []}
              onSelect={setLoopSourceCollectionPath}
            />
            <SchemaNodeSelect
              label="Loop target node"
              nodes={loopTargetSchemaNodes.data?.items ?? []}
              onSelect={setLoopTargetCollectionPath}
            />
            <label>
              Loop source collection path
              <input onChange={(event) => setLoopSourceCollectionPath(event.target.value)} value={loopSourceCollectionPath} />
            </label>
            <label>
              Loop target collection path
              <input onChange={(event) => setLoopTargetCollectionPath(event.target.value)} value={loopTargetCollectionPath} />
            </label>
            <label className="integration-form-wide">
              Loop description
              <input onChange={(event) => setLoopDescription(event.target.value)} value={loopDescription} />
            </label>
            <Button disabled={!effectiveDefinitionId || !loopSourceSchemaId || !loopTargetSchemaId || isMutating} type="submit" variant="primary">
              Create loop
            </Button>
          </form>

          <form
            className="integration-join-form"
            onSubmit={(event) => {
              event.preventDefault();
              void handleCreateJoin();
            }}
          >
            <label>
              Join source schema
              <select onChange={(event) => setJoinSourceSchemaId(event.target.value)} value={joinSourceSchemaId}>
                <option value="">Select source schema</option>
                {(schemaDocuments.data?.items ?? []).map((schema) => (
                  <option key={schema.id} value={schema.id}>
                    {schema.root_name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Join name
              <input onChange={(event) => setJoinName(event.target.value)} value={joinName} />
            </label>
            <SchemaNodeSelect
              label="Join left node"
              nodes={joinSourceSchemaNodes.data?.items ?? []}
              onSelect={setJoinLeftPath}
            />
            <SchemaNodeSelect
              label="Join right node"
              nodes={joinSourceSchemaNodes.data?.items ?? []}
              onSelect={setJoinRightPath}
            />
            <label>
              Join left path
              <input onChange={(event) => setJoinLeftPath(event.target.value)} value={joinLeftPath} />
            </label>
            <label>
              Join right path
              <input onChange={(event) => setJoinRightPath(event.target.value)} value={joinRightPath} />
            </label>
            <label>
              Join operator
              <select onChange={(event) => setJoinOperator(event.target.value)} value={joinOperator}>
                <option value="EQ">EQ</option>
                <option value="NE">NE</option>
              </select>
            </label>
            <label className="integration-form-wide">
              Join description
              <input onChange={(event) => setJoinDescription(event.target.value)} value={joinDescription} />
            </label>
            <Button disabled={!effectiveDefinitionId || !joinSourceSchemaId || isMutating} type="submit" variant="primary">
              Create join
            </Button>
          </form>

          <form
            className="integration-join-binding-form"
            onSubmit={(event) => {
              event.preventDefault();
              void handleCreateJoinBinding();
            }}
          >
            <label>
              Join binding source schema
              <select onChange={(event) => setJoinBindingSourceSchemaId(event.target.value)} value={joinBindingSourceSchemaId}>
                <option value="">Select source schema</option>
                {(schemaDocuments.data?.items ?? []).map((schema) => (
                  <option key={schema.id} value={schema.id}>
                    {schema.root_name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Join binding name
              <input onChange={(event) => setJoinBindingName(event.target.value)} value={joinBindingName} />
            </label>
            <SchemaNodeSelect
              label="Join binding root collection"
              nodes={collectionNodes(joinBindingSourceSchemaNodes.data?.items ?? [])}
              onSelect={setJoinBindingRootCollectionPath}
            />
            <SchemaNodeSelect
              label="Join binding target collection"
              nodes={collectionNodes(joinBindingSourceSchemaNodes.data?.items ?? [])}
              onSelect={setJoinBindingTargetCollectionPath}
            />
            <label>
              Join binding root collection path
              <input onChange={(event) => setJoinBindingRootCollectionPath(event.target.value)} value={joinBindingRootCollectionPath} />
            </label>
            <label>
              Join binding target collection path
              <input onChange={(event) => setJoinBindingTargetCollectionPath(event.target.value)} value={joinBindingTargetCollectionPath} />
            </label>
            <SchemaNodeSelect
              label="Hop 1 left collection"
              nodes={collectionNodes(joinBindingSourceSchemaNodes.data?.items ?? [])}
              onSelect={setJoinBindingHop1LeftCollectionPath}
            />
            <label>
              Hop 1 left value path
              <input onChange={(event) => setJoinBindingHop1LeftValuePath(event.target.value)} value={joinBindingHop1LeftValuePath} />
            </label>
            <SchemaNodeSelect
              label="Hop 1 right collection"
              nodes={collectionNodes(joinBindingSourceSchemaNodes.data?.items ?? [])}
              onSelect={setJoinBindingHop1RightCollectionPath}
            />
            <label>
              Hop 1 right value path
              <input onChange={(event) => setJoinBindingHop1RightValuePath(event.target.value)} value={joinBindingHop1RightValuePath} />
            </label>
            <label>
              Hop 1 result alias
              <input onChange={(event) => setJoinBindingHop1Alias(event.target.value)} value={joinBindingHop1Alias} />
            </label>
            <SchemaNodeSelect
              label="Hop 2 left collection"
              nodes={collectionNodes(joinBindingSourceSchemaNodes.data?.items ?? [])}
              onSelect={setJoinBindingHop2LeftCollectionPath}
            />
            <label>
              Hop 2 left value path
              <input onChange={(event) => setJoinBindingHop2LeftValuePath(event.target.value)} value={joinBindingHop2LeftValuePath} />
            </label>
            <SchemaNodeSelect
              label="Hop 2 right collection"
              nodes={collectionNodes(joinBindingSourceSchemaNodes.data?.items ?? [])}
              onSelect={setJoinBindingHop2RightCollectionPath}
            />
            <label>
              Hop 2 right value path
              <input onChange={(event) => setJoinBindingHop2RightValuePath(event.target.value)} value={joinBindingHop2RightValuePath} />
            </label>
            <label>
              Hop 2 result alias
              <input onChange={(event) => setJoinBindingHop2Alias(event.target.value)} value={joinBindingHop2Alias} />
            </label>
            <label className="integration-form-wide">
              Join binding description
              <input onChange={(event) => setJoinBindingDescription(event.target.value)} value={joinBindingDescription} />
            </label>
            <Button
              disabled={!effectiveDefinitionId || !joinBindingSourceSchemaId || !joinBindingName.trim() || isMutating}
              type="submit"
              variant="primary"
            >
              Create join binding
            </Button>
          </form>

          <form
            className="integration-lookup-form"
            onSubmit={(event) => {
              event.preventDefault();
              void handleCreateLookup();
            }}
          >
            <label>
              Lookup source schema
              <select onChange={(event) => setLookupSourceSchemaId(event.target.value)} value={lookupSourceSchemaId}>
                <option value="">Select source schema</option>
                {(schemaDocuments.data?.items ?? []).map((schema) => (
                  <option key={schema.id} value={schema.id}>
                    {schema.root_name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Lookup target schema
              <select onChange={(event) => setLookupTargetSchemaId(event.target.value)} value={lookupTargetSchemaId}>
                <option value="">Select target schema</option>
                {(schemaDocuments.data?.items ?? []).map((schema) => (
                  <option key={schema.id} value={schema.id}>
                    {schema.root_name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Lookup name
              <input onChange={(event) => setLookupName(event.target.value)} value={lookupName} />
            </label>
            <SchemaNodeSelect
              label="Lookup input node"
              nodes={lookupSourceSchemaNodes.data?.items ?? []}
              onSelect={setLookupInputPath}
            />
            <SchemaNodeSelect
              label="Lookup output node"
              nodes={lookupTargetSchemaNodes.data?.items ?? []}
              onSelect={setLookupOutputPath}
            />
            <label>
              Lookup input path
              <input onChange={(event) => setLookupInputPath(event.target.value)} value={lookupInputPath} />
            </label>
            <label>
              Lookup output path
              <input onChange={(event) => setLookupOutputPath(event.target.value)} value={lookupOutputPath} />
            </label>
            <label>
              Lookup type
              <select onChange={(event) => setLookupType(event.target.value)} value={lookupType}>
                <option value="MOCK">MOCK</option>
              </select>
            </label>
            <label className="integration-form-wide">
              Lookup description
              <input onChange={(event) => setLookupDescription(event.target.value)} value={lookupDescription} />
            </label>
            <label className="integration-form-full">
              Lookup mock response JSON
              <textarea onChange={(event) => setLookupMockResponseJson(event.target.value)} value={lookupMockResponseJson} />
            </label>
            <Button disabled={!effectiveDefinitionId || !lookupSourceSchemaId || !lookupTargetSchemaId || isMutating} type="submit" variant="primary">
              Create lookup
            </Button>
          </form>
        </OperationalPanel>
        ) : null}

        {activeStage === "definitions" ? (
        <ModuleObjectList
          ariaLabel="Integration mapping definitions"
          emptyText="No Integration Mapping definitions available for the current context."
          items={definitionItems.map((item) => ({
            id: item.id,
            meta: integrationDefinitionMeta(item),
            status: item.status,
            subtitle: item.name,
            title: item.code
          }))}
          onSelect={handleSelectDefinition}
          selectedId={effectiveDefinitionId}
        />
        ) : null}
      </ModuleWorkspaceLayout>
    </>
  );
}
