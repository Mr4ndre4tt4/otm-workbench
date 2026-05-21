import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../api";
import type {
  IntegrationDefinition,
  IntegrationDefinitionsResponse,
  IntegrationMappingsResponse,
  IntegrationPayloadArtifactsResponse,
  IntegrationSchemaDocumentsResponse,
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

export function useIntegrationDefinitionDetail(token: string | null, definitionId: string | null) {
  return useQuery({
    queryKey: ["modules", "integration-mapping", "definitions", definitionId],
    queryFn: () => apiGet<IntegrationDefinition>(`/api/v1/modules/integration-mapping/definitions/${definitionId}`, { token }),
    enabled: Boolean(token && definitionId)
  });
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
