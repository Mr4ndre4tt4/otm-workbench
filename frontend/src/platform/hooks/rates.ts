import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../api";
import type { RateBatchArtifactsResponse, RateBatchDetail, RateBatchEvidenceResponse, RatesSummary } from "../types";

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
