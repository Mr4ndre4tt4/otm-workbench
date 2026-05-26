import { useQueries, useQuery } from "@tanstack/react-query";

import { apiGet, apiPost } from "../api";
import type {
  CatalogMacroObject,
  CatalogMacroObjectDataDictionaryCheck,
  CatalogMacroObjectLoadPlan,
  CatalogMacroObjectsResponse,
  CatalogMacroObjectTablesResponse,
  CatalogSchemaGuidanceReadiness,
  CatalogSchemaGuidanceRole,
  CatalogSchemaPathsResponse,
  CatalogSchemaRootsResponse,
  CatalogReferenceOptionsResponse,
  CatalogTableSummary,
  CatalogTablesResponse,
  CatalogTableColumnsResponse,
  CatalogValidateColumnPayload,
  CatalogValidateColumnResult,
  CatalogValidateReferencePayload,
  CatalogValidateReferenceResult,
  CatalogValidateTablePayload,
  CatalogValidateTableResult
} from "../types";

export function useCatalogMacroObjects(token: string | null) {
  return useQuery({
    queryKey: ["catalog", "macro-objects"],
    queryFn: () => apiGet<CatalogMacroObjectsResponse>("/api/v1/catalog/macro-objects", { token }),
    enabled: Boolean(token)
  });
}

export function useCatalogMacroObjectDetail(token: string | null, macroObjectCode: string | null) {
  return useQuery({
    queryKey: ["catalog", "macro-objects", macroObjectCode],
    queryFn: () => apiGet<CatalogMacroObject>(`/api/v1/catalog/macro-objects/${macroObjectCode}`, { token }),
    enabled: Boolean(token && macroObjectCode)
  });
}

export function useCatalogMacroObjectTables(token: string | null, macroObjectCode: string | null) {
  return useQuery({
    queryKey: ["catalog", "macro-objects", macroObjectCode, "tables"],
    queryFn: () => apiGet<CatalogMacroObjectTablesResponse>(`/api/v1/catalog/macro-objects/${macroObjectCode}/tables`, { token }),
    enabled: Boolean(token && macroObjectCode)
  });
}

export function useCatalogMacroObjectLoadPlan(token: string | null, macroObjectCode: string | null) {
  return useQuery({
    queryKey: ["catalog", "macro-objects", macroObjectCode, "load-plan"],
    queryFn: () => apiGet<CatalogMacroObjectLoadPlan>(`/api/v1/catalog/macro-objects/${macroObjectCode}/load-plan`, { token }),
    enabled: Boolean(token && macroObjectCode)
  });
}

export function useCatalogMacroObjectDataDictionaryCheck(token: string | null, macroObjectCode: string | null) {
  return useQuery({
    queryKey: ["catalog", "macro-objects", macroObjectCode, "data-dictionary-cross-check"],
    queryFn: () =>
      apiGet<CatalogMacroObjectDataDictionaryCheck>(
        `/api/v1/catalog/macro-objects/${macroObjectCode}/data-dictionary-cross-check`,
        { token }
      ),
    enabled: Boolean(token && macroObjectCode)
  });
}

export function useCatalogSchemaGuidanceReadiness(token: string | null) {
  return useQuery({
    queryKey: ["catalog", "schema-guidance", "readiness"],
    queryFn: () => apiGet<CatalogSchemaGuidanceReadiness>("/api/v1/catalog/schema-guidance/readiness", { token }),
    enabled: Boolean(token)
  });
}

export function useCatalogSchemaRootsByRole(token: string | null, schemaGuidanceRole: CatalogSchemaGuidanceRole | null) {
  const params = new URLSearchParams();
  if (schemaGuidanceRole) params.set("schema_guidance_role", schemaGuidanceRole);
  const queryString = params.toString();
  return useQuery({
    queryKey: ["catalog", "schema-roots", "role", schemaGuidanceRole],
    queryFn: () => apiGet<CatalogSchemaRootsResponse>(`/api/v1/catalog/schema-roots?${queryString}`, { token }),
    enabled: Boolean(token && schemaGuidanceRole)
  });
}

export function useCatalogSchemaRootPaths(token: string | null, schemaRootId: string | null, query = "") {
  const params = new URLSearchParams();
  if (query.trim()) params.set("query", query.trim());
  const queryString = params.toString();
  const suffix = queryString ? `?${queryString}` : "";
  return useQuery({
    queryKey: ["catalog", "schema-roots", schemaRootId, "paths", query.trim()],
    queryFn: () => apiGet<CatalogSchemaPathsResponse>(`/api/v1/catalog/schema-roots/${schemaRootId}/paths${suffix}`, { token }),
    enabled: Boolean(token && schemaRootId)
  });
}

export function useCatalogTables(token: string | null, query = "", limit = 50) {
  const params = new URLSearchParams();
  if (query.trim()) params.set("query", query.trim());
  params.set("limit", String(limit));
  const queryString = params.toString();
  return useQuery({
    queryKey: ["catalog", "tables", "search", query.trim(), limit],
    queryFn: () => apiGet<CatalogTablesResponse>(`/api/v1/catalog/tables?${queryString}`, { token }),
    enabled: Boolean(token)
  });
}

export function useCatalogTableDetail(token: string | null, tableName: string | null) {
  return useQuery({
    queryKey: ["catalog", "tables", tableName, "detail"],
    queryFn: () => apiGet<CatalogTableSummary>(`/api/v1/catalog/tables/${tableName}`, { token }),
    enabled: Boolean(token && tableName)
  });
}

export function useCatalogTableColumns(token: string | null, tableName: string | null) {
  return useQuery({
    queryKey: ["catalog", "tables", tableName, "columns"],
    queryFn: () => apiGet<CatalogTableColumnsResponse>(`/api/v1/catalog/tables/${tableName}/columns`, { token }),
    enabled: Boolean(token && tableName)
  });
}

export function useCatalogReferenceOptions(token: string | null, objectType: string, domainName: string) {
  const params = new URLSearchParams();
  params.set("object_type", objectType.trim() || "CURRENCY");
  if (domainName.trim()) params.set("domain_name", domainName.trim());
  const queryString = params.toString();
  return useQuery({
    queryKey: ["catalog", "reference-options", objectType.trim(), domainName.trim()],
    queryFn: () => apiGet<CatalogReferenceOptionsResponse>(`/api/v1/catalog/reference/options?${queryString}`, { token }),
    enabled: Boolean(token)
  });
}

export function useCatalogColumnsByTable(token: string | null, tableNames: string[]) {
  const uniqueTableNames = Array.from(new Set(tableNames.filter(Boolean)));
  return useQueries({
    queries: uniqueTableNames.map((tableName) => ({
      queryKey: ["catalog", "tables", tableName, "columns"],
      queryFn: () => apiGet<CatalogTableColumnsResponse>(`/api/v1/catalog/tables/${tableName}/columns`, { token }),
      enabled: Boolean(token && tableName)
    })),
    combine: (results) => ({
      byTable: Object.fromEntries(
        results.map((result, index) => [uniqueTableNames[index], result.data?.items ?? []])
      ),
      isLoading: results.some((result) => result.isLoading)
    })
  });
}

export function validateCatalogTable(token: string, payload: CatalogValidateTablePayload) {
  return apiPost<CatalogValidateTableResult>("/api/v1/catalog/validate/table", payload, { token });
}

export function validateCatalogColumn(token: string, payload: CatalogValidateColumnPayload) {
  return apiPost<CatalogValidateColumnResult>("/api/v1/catalog/validate/column", payload, { token });
}

export function validateCatalogReference(token: string, payload: CatalogValidateReferencePayload) {
  return apiPost<CatalogValidateReferenceResult>("/api/v1/catalog/validate/reference", payload, { token });
}
