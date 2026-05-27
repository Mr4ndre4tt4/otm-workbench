import { useQuery } from "@tanstack/react-query";

import { apiGet, apiPost } from "../api";
import type {
  AddRateBatchTablesPayload,
  AddRateBatchTablesResponse,
  CreateRateBatchPayload,
  RateBatchApprovalPayload,
  RateBatchApprovalResponse,
  RateBatchArtifactsResponse,
  RateBatchCsvExportResponse,
  RateBatchCsvPreviewResponse,
  RateBatchesResponse,
  RateBatchDetail,
  RateBatchEvidenceResponse,
  RateBatchIssuesResponse,
  RateBatchTableDetailResponse,
  RatesSummary
} from "../types";

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

export function useRateBatches(token: string | null) {
  return useQuery({
    queryKey: ["modules", "rates", "batches"],
    queryFn: () => apiGet<RateBatchesResponse>("/api/v1/modules/rates/batches", { token }),
    enabled: Boolean(token)
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

export function useRateBatchIssues(token: string | null, batchId: string | null) {
  return useQuery({
    queryKey: ["modules", "rates", "batches", batchId, "issues"],
    queryFn: () => apiGet<RateBatchIssuesResponse>(`/api/v1/modules/rates/batches/${batchId}/issues`, { token }),
    enabled: Boolean(token && batchId)
  });
}

export function useRateBatchTableDetail(token: string | null, batchId: string | null, tableName: string | null) {
  return useQuery({
    queryKey: ["modules", "rates", "batches", batchId, "tables", tableName],
    queryFn: () =>
      apiGet<RateBatchTableDetailResponse>(`/api/v1/modules/rates/batches/${batchId}/tables/${tableName}`, { token }),
    enabled: Boolean(token && batchId && tableName)
  });
}

export function createRateBatch(token: string, payload: CreateRateBatchPayload) {
  return apiPost<RateBatchDetail>("/api/v1/modules/rates/batches", payload, { token });
}

export function addRateBatchTables(token: string, batchId: string, payload: AddRateBatchTablesPayload) {
  return apiPost<AddRateBatchTablesResponse>(`/api/v1/modules/rates/batches/${batchId}/tables`, payload, { token });
}

export function previewRateBatchCsv(token: string, batchId: string) {
  return apiPost<RateBatchCsvPreviewResponse>(`/api/v1/modules/rates/batches/${batchId}/csv-preview`, {}, { token });
}

export function exportRateBatchCsv(token: string, batchId: string) {
  return apiPost<RateBatchCsvExportResponse>(`/api/v1/modules/rates/batches/${batchId}/export-csv`, {}, { token });
}

export function approveRateBatch(token: string, batchId: string, payload: RateBatchApprovalPayload) {
  return apiPost<RateBatchApprovalResponse>(`/api/v1/modules/rates/batches/${batchId}/approve`, payload, { token });
}
