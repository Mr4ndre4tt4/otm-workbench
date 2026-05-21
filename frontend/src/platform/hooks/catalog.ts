import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../api";
import type {
  CatalogMacroObject,
  CatalogMacroObjectLoadPlan,
  CatalogMacroObjectsResponse,
  CatalogMacroObjectTablesResponse
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
