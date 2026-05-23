import { useQuery } from "@tanstack/react-query";

import { apiGet, apiPatch, apiPost } from "../api";
import type {
  CsvutilBuild,
  CutoverGoNoGoDecision,
  CutoverHandoffCommit,
  CutoverPackageExport,
  CutoverChecklist,
  CutoverChecklistReadiness,
  CutoverHandoffEligibility,
  LoadPlanCutoverReadinessGeneration,
  LoadPlanReadinessExport,
  LoadPlanReviewDecision,
  LoadPlanReviewQueueGeneration,
  LoadPlanReviewQueueResponse,
  LoadPlanSequenceSnapshot,
  LoadPlanPackage,
  LoadPlanPackagesResponse,
  LoadPlanSummary,
  LoadPlanZipAnalysis
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

export function registerMasterDataPackageForLoadPlan(token: string, batchId: string) {
  return apiPost<LoadPlanPackage>(`/api/v1/modules/load-plan/packages/from-master-data/${batchId}`, {}, { token });
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

export function generateLoadPlanCutoverReadiness(token: string, packageId: string) {
  return apiPost<LoadPlanCutoverReadinessGeneration>(
    "/api/v1/modules/load-plan/cutover-readiness/generate",
    { package_id: packageId },
    { token }
  );
}

export function generateLoadPlanSequenceSnapshot(token: string, packageId: string) {
  return apiPost<LoadPlanSequenceSnapshot>("/api/v1/modules/load-plan/sequence/snapshots", { package_id: packageId }, { token });
}

export function exportLoadPlanCutoverReadiness(token: string, readinessId: string) {
  return apiPost<LoadPlanReadinessExport>(`/api/v1/modules/load-plan/cutover-readiness/${readinessId}/export`, {}, { token });
}

export function exportCutoverChecklistPackage(token: string, checklistId: string) {
  return apiPost<CutoverPackageExport>(
    `/api/v1/modules/load-plan/cutover-checklists/${checklistId}/export-package`,
    {},
    { token }
  );
}

export function decideCutoverGoNoGo(token: string, checklistId: string) {
  return apiPost<CutoverGoNoGoDecision>(
    `/api/v1/modules/load-plan/cutover-checklists/${checklistId}/go-no-go`,
    { decision_note: "Synthetic UI go/no-go review." },
    { token }
  );
}

export function commitCutoverHandoff(token: string, packageId: string) {
  return apiPost<CutoverHandoffCommit>("/api/v1/modules/load-plan/cutover-handoff", { package_id: packageId }, { token });
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

export function runLoadPlanZipAnalysis(token: string, packageId: string) {
  return apiPost<LoadPlanZipAnalysis>("/api/v1/modules/load-plan/zip-analysis", { package_id: packageId }, { token });
}

export function generateReviewQueueFromZipAnalysis(token: string, analysisId: string) {
  return apiPost<LoadPlanReviewQueueGeneration>(
    `/api/v1/modules/load-plan/review-queue/from-zip-analysis/${analysisId}`,
    {},
    { token }
  );
}

export function decideLoadPlanReviewItem(
  token: string,
  itemId: string,
  payload: { decision_note: string; decision_status: string }
) {
  return apiPost<LoadPlanReviewDecision>(`/api/v1/modules/load-plan/review-queue/${itemId}/decide`, payload, { token });
}

export function useLoadPlanReviewQueue(token: string | null, packageId: string | null) {
  return useQuery({
    queryKey: ["modules", "load-plan", "review-queue", packageId],
    queryFn: () =>
      apiGet<LoadPlanReviewQueueResponse>(`/api/v1/modules/load-plan/review-queue?package_id=${packageId}`, { token }),
    enabled: Boolean(token && packageId)
  });
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
