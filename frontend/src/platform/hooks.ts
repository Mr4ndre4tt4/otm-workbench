import { useQuery } from "@tanstack/react-query";

import { apiDownload, apiGet, apiPost, apiPut } from "./api";
import type {
  ActiveContextResponse,
  ActiveContextUpdate,
  AssetItem,
  AssetsResponse,
  AssetVersionsResponse,
  CatalogMacroObject,
  CatalogMacroObjectLoadPlan,
  CatalogMacroObjectsResponse,
  CatalogMacroObjectTablesResponse,
  CockpitSummary,
  EvidenceHubResponse,
  EvidenceItem,
  IdNameResponse,
  LoadPlanPackage,
  LoadPlanPackagesResponse,
  LoadPlanSummary,
  LoginResponse,
  NavigationResponse,
  RateBatchArtifactsResponse,
  RateBatchDetail,
  RateBatchEvidenceResponse,
  RatesSummary,
  UserPreferences
} from "./types";

export function login(email: string, password: string) {
  return apiPost<LoginResponse>("/api/v1/platform/session/login", { email, password });
}

export function useNavigation(token: string | null) {
  return useQuery({
    queryKey: ["platform", "navigation"],
    queryFn: () => apiGet<NavigationResponse>("/api/v1/platform/navigation", { token }),
    enabled: Boolean(token)
  });
}

export function useProjects(token: string | null) {
  return useQuery({
    queryKey: ["platform", "projects"],
    queryFn: () => apiGet<IdNameResponse>("/api/v1/platform/projects", { token }),
    enabled: Boolean(token)
  });
}

export function useProfiles(token: string | null, projectId: string | null) {
  return useQuery({
    queryKey: ["platform", "profiles", projectId],
    queryFn: () => apiGet<IdNameResponse>(`/api/v1/platform/profiles?project_id=${projectId}`, { token }),
    enabled: Boolean(token && projectId)
  });
}

export function useEnvironments(token: string | null, projectId: string | null) {
  return useQuery({
    queryKey: ["platform", "environments", projectId],
    queryFn: () => apiGet<IdNameResponse>(`/api/v1/platform/environments?project_id=${projectId}`, { token }),
    enabled: Boolean(token && projectId)
  });
}

export function updateActiveContext(token: string, payload: ActiveContextUpdate) {
  return apiPost<ActiveContextResponse>("/api/v1/platform/active-context", payload, { token });
}

export function executeBackendAction<T = Record<string, unknown>>(token: string, href: string) {
  return apiPost<T>(href, {}, { token });
}

export function downloadBackendArtifact(token: string, href: string) {
  return apiDownload(href, { token });
}

export function useCockpitSummary(token: string | null) {
  return useQuery({
    queryKey: ["platform", "project-cockpit", "summary"],
    queryFn: () => apiGet<CockpitSummary>("/api/v1/platform/project-cockpit/summary", { token }),
    enabled: Boolean(token)
  });
}

export function useRatesSummary(token: string | null) {
  return useQuery({
    queryKey: ["modules", "rates", "summary"],
    queryFn: () => apiGet<RatesSummary>("/api/v1/modules/rates/summary", { token }),
    enabled: Boolean(token)
  });
}

export function useRateBatchDetail(token: string | null, batchId: string | null) {
  return useQuery({
    queryKey: ["modules", "rates", "batches", batchId],
    queryFn: () => apiGet<RateBatchDetail>(`/api/v1/modules/rates/batches/${batchId}`, { token }),
    enabled: Boolean(token && batchId)
  });
}

export function useRateBatchArtifacts(token: string | null, batchId: string | null) {
  return useQuery({
    queryKey: ["modules", "rates", "batches", batchId, "artifacts"],
    queryFn: () => apiGet<RateBatchArtifactsResponse>(`/api/v1/modules/rates/batches/${batchId}/artifacts`, { token }),
    enabled: Boolean(token && batchId)
  });
}

export function useRateBatchEvidence(token: string | null, batchId: string | null) {
  return useQuery({
    queryKey: ["modules", "rates", "batches", batchId, "evidence"],
    queryFn: () => apiGet<RateBatchEvidenceResponse>(`/api/v1/modules/rates/batches/${batchId}/evidence`, { token }),
    enabled: Boolean(token && batchId)
  });
}

export function useAssets(token: string | null) {
  return useQuery({
    queryKey: ["modules", "assets", "assets"],
    queryFn: () => apiGet<AssetsResponse>("/api/v1/modules/assets/assets", { token }),
    enabled: Boolean(token)
  });
}

export function useAssetDetail(token: string | null, assetId: string | null) {
  return useQuery({
    queryKey: ["modules", "assets", "assets", assetId],
    queryFn: () => apiGet<AssetItem>(`/api/v1/modules/assets/assets/${assetId}`, { token }),
    enabled: Boolean(token && assetId)
  });
}

export function useAssetVersions(token: string | null, assetId: string | null) {
  return useQuery({
    queryKey: ["modules", "assets", "assets", assetId, "versions"],
    queryFn: () => apiGet<AssetVersionsResponse>(`/api/v1/modules/assets/assets/${assetId}/versions`, { token }),
    enabled: Boolean(token && assetId)
  });
}

export function useEvidenceHub(token: string | null) {
  return useQuery({
    queryKey: ["evidence-hub", "evidence"],
    queryFn: () => apiGet<EvidenceHubResponse>("/api/v1/evidence-hub/evidence", { token }),
    enabled: Boolean(token)
  });
}

export function useEvidenceDetail(token: string | null, evidenceId: string | null) {
  return useQuery({
    queryKey: ["evidence-hub", "evidence", evidenceId],
    queryFn: () => apiGet<EvidenceItem>(`/api/v1/evidence-hub/evidence/${evidenceId}`, { token }),
    enabled: Boolean(token && evidenceId)
  });
}

export function useLoadPlanSummary(token: string | null) {
  return useQuery({
    queryKey: ["modules", "load-plan", "summary"],
    queryFn: () => apiGet<LoadPlanSummary>("/api/v1/modules/load-plan/summary", { token }),
    enabled: Boolean(token)
  });
}

export function useLoadPlanPackages(token: string | null) {
  return useQuery({
    queryKey: ["modules", "load-plan", "packages"],
    queryFn: () => apiGet<LoadPlanPackagesResponse>("/api/v1/modules/load-plan/packages", { token }),
    enabled: Boolean(token)
  });
}

export function useLoadPlanPackageDetail(token: string | null, packageId: string | null) {
  return useQuery({
    queryKey: ["modules", "load-plan", "packages", packageId],
    queryFn: () => apiGet<LoadPlanPackage>(`/api/v1/modules/load-plan/packages/${packageId}`, { token }),
    enabled: Boolean(token && packageId)
  });
}

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

export function useUserPreferences(token: string | null) {
  return useQuery({
    queryKey: ["platform", "user-preferences"],
    queryFn: () => apiGet<UserPreferences>("/api/v1/platform/user-preferences", { token }),
    enabled: Boolean(token)
  });
}

export function updateUserPreferences(token: string, payload: UserPreferences) {
  return apiPut<UserPreferences>("/api/v1/platform/user-preferences", payload, { token });
}
