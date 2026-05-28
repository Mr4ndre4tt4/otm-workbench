import { useQuery } from "@tanstack/react-query";

import { apiDelete, apiGet, apiPost } from "../api";
import type {
  IntegrationDefinition,
  IntegrationDefinitionCreatePayload,
  IntegrationArtifactsResponse,
  IntegrationEnrichedFieldsResponse,
  IntegrationEnrichmentReadiness,
  IntegrationEnrichmentStepsResponse,
  IntegrationEndpoint,
  IntegrationEndpointCreatePayload,
  IntegrationEndpointsResponse,
  IntegrationJoinCreatePayload,
  IntegrationJoinBinding,
  IntegrationJoinBindingCreatePayload,
  IntegrationJoinBindingsResponse,
  IntegrationJoinRule,
  IntegrationJoinsResponse,
  IntegrationLookupCreatePayload,
  IntegrationLookupDefinition,
  IntegrationLookupsResponse,
  IntegrationLoopCreatePayload,
  IntegrationLoopDefinition,
  IntegrationLoopsResponse,
  IntegrationMapping,
  IntegrationMappingCreatePayload,
  IntegrationMappingsBulkCreatePayload,
  IntegrationMappingsBulkCreateResponse,
  IntegrationDefinitionsResponse,
  IntegrationMappingsResponse,
  IntegrationMappingSuggestionsResponse,
  IntegrationPayloadArtifactsResponse,
  IntegrationPayloadArtifact,
  IntegrationPayloadArtifactCreatePayload,
  IntegrationPreviewResult,
  IntegrationResponseHandler,
  IntegrationResponseHandlerCreatePayload,
  IntegrationResponseHandlersResponse,
  IntegrationSchemaDocument,
  IntegrationSchemaDocumentsResponse,
  IntegrationSchemaNodesResponse,
  IntegrationSpecResult,
  IntegrationSystem,
  IntegrationSystemCreatePayload,
  IntegrationSystemsResponse,
  IntegrationTransformTypesResponse
} from "../types";

export function useIntegrationTransformTypes(token: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "transform-types"],
    queryFn: () => apiGet<IntegrationTransformTypesResponse>("/api/v1/modules/integration-mapping/transform-types", { token }),
    enabled: Boolean(token)
  });
}

export function useIntegrationDefinitions(token: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "definitions"],
    queryFn: () => apiGet<IntegrationDefinitionsResponse>("/api/v1/modules/integration-mapping/definitions", { token }),
    enabled: Boolean(token)
  });
}

export function useIntegrationSystems(token: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "systems"],
    queryFn: () => apiGet<IntegrationSystemsResponse>("/api/v1/modules/integration-mapping/systems", { token }),
    enabled: Boolean(token)
  });
}

export function createIntegrationSystem(token: string, payload: IntegrationSystemCreatePayload) {
  return apiPost<IntegrationSystem>("/api/v1/modules/integration-mapping/systems", payload, { token });
}

export function useIntegrationEndpoints(token: string | null, systemId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "systems", systemId, "endpoints"],
    queryFn: () => apiGet<IntegrationEndpointsResponse>(`/api/v1/modules/integration-mapping/systems/${systemId}/endpoints`, { token }),
    enabled: Boolean(token && systemId)
  });
}

export function createIntegrationEndpoint(token: string, systemId: string, payload: IntegrationEndpointCreatePayload) {
  return apiPost<IntegrationEndpoint>(`/api/v1/modules/integration-mapping/systems/${systemId}/endpoints`, payload, { token });
}

export function createIntegrationDefinition(token: string, payload: IntegrationDefinitionCreatePayload) {
  return apiPost<IntegrationDefinition>("/api/v1/modules/integration-mapping/definitions", payload, { token });
}

export function useIntegrationDefinitionDetail(token: string | null, definitionId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "definitions", definitionId],
    queryFn: () => apiGet<IntegrationDefinition>(`/api/v1/modules/integration-mapping/definitions/${definitionId}`, { token }),
    enabled: Boolean(token && definitionId)
  });
}

export function createIntegrationPayloadArtifact(
  token: string,
  definitionId: string,
  payload: IntegrationPayloadArtifactCreatePayload
) {
  return apiPost<IntegrationPayloadArtifact>(
    `/api/v1/modules/integration-mapping/definitions/${definitionId}/payload-artifacts`,
    payload,
    { token }
  );
}

export function createIntegrationSchemaDocument(token: string, payloadArtifactId: string) {
  return apiPost<IntegrationSchemaDocument>(
    `/api/v1/modules/integration-mapping/payload-artifacts/${payloadArtifactId}/schema-documents`,
    {},
    { token }
  );
}

export function useIntegrationPayloadArtifacts(token: string | null, definitionId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "definitions", definitionId, "payload-artifacts"],
    queryFn: () =>
      apiGet<IntegrationPayloadArtifactsResponse>(
        `/api/v1/modules/integration-mapping/definitions/${definitionId}/payload-artifacts`,
        { token }
      ),
    enabled: Boolean(token && definitionId)
  });
}

export function useIntegrationSchemaDocuments(token: string | null, definitionId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "definitions", definitionId, "schema-documents"],
    queryFn: () =>
      apiGet<IntegrationSchemaDocumentsResponse>(
        `/api/v1/modules/integration-mapping/definitions/${definitionId}/schema-documents`,
        { token }
      ),
    enabled: Boolean(token && definitionId)
  });
}

export function useIntegrationSchemaNodes(token: string | null, schemaDocumentId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "schema-documents", schemaDocumentId, "nodes"],
    queryFn: () =>
      apiGet<IntegrationSchemaNodesResponse>(
        `/api/v1/modules/integration-mapping/schema-documents/${schemaDocumentId}/nodes`,
        { token }
      ),
    enabled: Boolean(token && schemaDocumentId)
  });
}

export function useIntegrationMappings(token: string | null, definitionId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "definitions", definitionId, "mappings"],
    queryFn: () =>
      apiGet<IntegrationMappingsResponse>(`/api/v1/modules/integration-mapping/definitions/${definitionId}/mappings`, {
        token
      }),
    enabled: Boolean(token && definitionId)
  });
}

export function useIntegrationMappingSuggestions(
  token: string | null,
  definitionId: string | null,
  sourceSchemaDocumentId: string | null,
  targetSchemaDocumentId: string | null
) {
  const params =
    sourceSchemaDocumentId && targetSchemaDocumentId
      ? `?source_schema_document_id=${encodeURIComponent(sourceSchemaDocumentId)}&target_schema_document_id=${encodeURIComponent(targetSchemaDocumentId)}`
      : "";
  return useQuery({
    queryKey: [
      "modules",
      "integration-mapping",
      "definitions",
      definitionId,
      "mapping-suggestions",
      sourceSchemaDocumentId,
      targetSchemaDocumentId
    ],
    queryFn: () =>
      apiGet<IntegrationMappingSuggestionsResponse>(
        `/api/v1/modules/integration-mapping/definitions/${definitionId}/mapping-suggestions${params}`,
        { token }
      ),
    enabled: Boolean(token && definitionId && sourceSchemaDocumentId && targetSchemaDocumentId)
  });
}

export function listIntegrationMappingSuggestions(
  token: string,
  definitionId: string,
  sourceSchemaDocumentId: string,
  targetSchemaDocumentId: string
) {
  const params = `?source_schema_document_id=${encodeURIComponent(sourceSchemaDocumentId)}&target_schema_document_id=${encodeURIComponent(targetSchemaDocumentId)}`;
  return apiGet<IntegrationMappingSuggestionsResponse>(
    `/api/v1/modules/integration-mapping/definitions/${definitionId}/mapping-suggestions${params}`,
    { token }
  );
}

export function useIntegrationLoops(token: string | null, definitionId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "definitions", definitionId, "loops"],
    queryFn: () =>
      apiGet<IntegrationLoopsResponse>(`/api/v1/modules/integration-mapping/definitions/${definitionId}/loops`, {
        token
      }),
    enabled: Boolean(token && definitionId)
  });
}

export function useIntegrationJoins(token: string | null, definitionId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "definitions", definitionId, "joins"],
    queryFn: () =>
      apiGet<IntegrationJoinsResponse>(`/api/v1/modules/integration-mapping/definitions/${definitionId}/joins`, {
        token
      }),
    enabled: Boolean(token && definitionId)
  });
}

export function useIntegrationJoinBindings(token: string | null, definitionId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "definitions", definitionId, "join-bindings"],
    queryFn: () =>
      apiGet<IntegrationJoinBindingsResponse>(`/api/v1/modules/integration-mapping/definitions/${definitionId}/join-bindings`, {
        token
      }),
    enabled: Boolean(token && definitionId)
  });
}

export function useIntegrationLookups(token: string | null, definitionId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "definitions", definitionId, "lookups"],
    queryFn: () =>
      apiGet<IntegrationLookupsResponse>(`/api/v1/modules/integration-mapping/definitions/${definitionId}/lookups`, {
        token
      }),
    enabled: Boolean(token && definitionId)
  });
}

export function useIntegrationArtifacts(token: string | null, definitionId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "definitions", definitionId, "artifacts"],
    queryFn: () =>
      apiGet<IntegrationArtifactsResponse>(`/api/v1/modules/integration-mapping/definitions/${definitionId}/artifacts`, {
        token
      }),
    enabled: Boolean(token && definitionId)
  });
}

export function createIntegrationMapping(token: string, definitionId: string, payload: IntegrationMappingCreatePayload) {
  return apiPost<IntegrationMapping>(`/api/v1/modules/integration-mapping/definitions/${definitionId}/mappings`, payload, {
    token
  });
}

export function createIntegrationMappingsBulk(
  token: string,
  definitionId: string,
  payload: IntegrationMappingsBulkCreatePayload
) {
  return apiPost<IntegrationMappingsBulkCreateResponse>(
    `/api/v1/modules/integration-mapping/definitions/${definitionId}/mappings/bulk`,
    payload,
    { token }
  );
}

export function useIntegrationResponseHandlers(token: string | null, definitionId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "definitions", definitionId, "response-handlers"],
    queryFn: () =>
      apiGet<IntegrationResponseHandlersResponse>(
        `/api/v1/modules/integration-mapping/definitions/${definitionId}/response-handlers`,
        { token }
      ),
    enabled: Boolean(token && definitionId)
  });
}

export function useIntegrationEnrichmentSteps(token: string | null, definitionId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "definitions", definitionId, "enrichment-steps"],
    queryFn: () =>
      apiGet<IntegrationEnrichmentStepsResponse>(
        `/api/v1/modules/integration-mapping/definitions/${definitionId}/enrichment-steps`,
        { token }
      ),
    enabled: Boolean(token && definitionId)
  });
}

export function useIntegrationEnrichedFields(token: string | null, definitionId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "definitions", definitionId, "enriched-fields"],
    queryFn: () =>
      apiGet<IntegrationEnrichedFieldsResponse>(
        `/api/v1/modules/integration-mapping/definitions/${definitionId}/enriched-fields`,
        { token }
      ),
    enabled: Boolean(token && definitionId)
  });
}

export function useIntegrationEnrichmentReadiness(token: string | null, definitionId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "definitions", definitionId, "enrichment-readiness"],
    queryFn: () =>
      apiGet<IntegrationEnrichmentReadiness>(
        `/api/v1/modules/integration-mapping/definitions/${definitionId}/enrichment-readiness`,
        { token }
      ),
    enabled: Boolean(token && definitionId)
  });
}

export function deleteIntegrationMapping(token: string, mappingId: string) {
  return apiDelete<{ deleted: boolean; definition_id: string; id: string }>(
    `/api/v1/modules/integration-mapping/mappings/${mappingId}`,
    { token }
  );
}

export function createIntegrationLoop(token: string, definitionId: string, payload: IntegrationLoopCreatePayload) {
  return apiPost<IntegrationLoopDefinition>(`/api/v1/modules/integration-mapping/definitions/${definitionId}/loops`, payload, {
    token
  });
}

export function createIntegrationJoin(token: string, definitionId: string, payload: IntegrationJoinCreatePayload) {
  return apiPost<IntegrationJoinRule>(`/api/v1/modules/integration-mapping/definitions/${definitionId}/joins`, payload, {
    token
  });
}

export function createIntegrationJoinBinding(token: string, definitionId: string, payload: IntegrationJoinBindingCreatePayload) {
  return apiPost<IntegrationJoinBinding>(
    `/api/v1/modules/integration-mapping/definitions/${definitionId}/join-bindings`,
    payload,
    { token }
  );
}

export function createIntegrationLookup(token: string, definitionId: string, payload: IntegrationLookupCreatePayload) {
  return apiPost<IntegrationLookupDefinition>(
    `/api/v1/modules/integration-mapping/definitions/${definitionId}/lookups`,
    payload,
    { token }
  );
}

export function createIntegrationResponseHandler(
  token: string,
  definitionId: string,
  payload: IntegrationResponseHandlerCreatePayload
) {
  return apiPost<IntegrationResponseHandler>(
    `/api/v1/modules/integration-mapping/definitions/${definitionId}/response-handlers`,
    payload,
    { token }
  );
}

export function validateIntegrationDefinition(token: string, definitionId: string) {
  return apiPost<IntegrationPreviewResult["validation"]>(
    `/api/v1/modules/integration-mapping/definitions/${definitionId}/validate`,
    {},
    { token }
  );
}

export function previewIntegrationDefinition(token: string, definitionId: string) {
  return apiPost<IntegrationPreviewResult>(
    `/api/v1/modules/integration-mapping/definitions/${definitionId}/preview`,
    {},
    { token }
  );
}

export function generateIntegrationSpec(token: string, definitionId: string) {
  return apiPost<IntegrationSpecResult>(
    `/api/v1/modules/integration-mapping/definitions/${definitionId}/generate-spec`,
    {},
    { token }
  );
}
