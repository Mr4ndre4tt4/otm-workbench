import { useQuery } from "@tanstack/react-query";

import { apiGet, apiPost } from "../api";
import type {
  CatalogMacroObject,
  CatalogMacroObjectLoadPlan,
  CatalogMacroObjectsResponse,
  CatalogMacroObjectTablesResponse,
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

export function useCatalogTableColumns(token: string | null, tableName: string | null) {
  return useQuery({
    queryKey: ["catalog", "tables", tableName, "columns"],
    queryFn: () => apiGet<CatalogTableColumnsResponse>(`/api/v1/catalog/tables/${tableName}/columns`, { token }),
    enabled: Boolean(token && tableName)
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
