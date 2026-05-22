import { useQuery } from "@tanstack/react-query";

import { apiGet, apiPatch, apiPost } from "../api";
import type {
  CsvutilBuild,
  CutoverChecklist,
  CutoverChecklistReadiness,
  CutoverHandoffEligibility,
  LoadPlanPackage,
  LoadPlanPackagesResponse,
  LoadPlanSummary
} from "../types";

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

export function createCutoverChecklistFromPackage(token: string, packageId: string) {
  return apiPost<CutoverChecklist>(`/api/v1/modules/load-plan/cutover-checklists/from-package/${packageId}`, {}, { token });
}

export function updateCutoverChecklistItem(
  token: string,
  itemId: string,
  payload: { evidence_id?: string | null; method?: string; status?: string }
) {
  return apiPatch<CutoverChecklist>(`/api/v1/modules/load-plan/cutover-checklists/items/${itemId}`, payload, { token });
}

export function generateCutoverChecklistReadiness(token: string, checklistId: string) {
  return apiPost<CutoverChecklistReadiness>(
    `/api/v1/modules/load-plan/cutover-checklists/${checklistId}/readiness`,
    {},
    { token }
  );
}

export function buildCsvutilFromCutoverChecklist(token: string, checklistId: string) {
  return apiPost<CsvutilBuild>(
    `/api/v1/modules/load-plan/csvutil/build/from-cutover-checklist/${checklistId}`,
    {
      parameter_set: {
        date_format: "YYYY-MM-DD HH24:MI:SS",
        delimiter: "COMMA",
        encoding: "UTF-8",
        mode: "INSERT"
      }
    },
    { token }
  );
}

export function useCutoverHandoffEligibility(token: string | null, packageId: string | null) {
  return useQuery({
    queryKey: ["modules", "load-plan", "cutover-handoff", "eligibility", packageId],
    queryFn: () =>
      apiGet<CutoverHandoffEligibility>(`/api/v1/modules/load-plan/cutover-handoff/eligibility?package_id=${packageId}`, {
        token
      }),
    enabled: Boolean(token && packageId)
  });
}
