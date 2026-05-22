import { useQuery } from "@tanstack/react-query";

import { apiDownload, apiGet, apiPost } from "../api";
import type {
  EvidenceArchivePackageRequest,
  EvidenceArchivePackageResponse,
  EvidenceHubFilters,
  EvidenceHubResponse,
  EvidenceItem
} from "../types";

function evidenceFilterPath(filters: EvidenceHubFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    params.set(key, String(value));
  });
  const query = params.toString();
  return `/api/v1/evidence-hub/evidence${query ? `?${query}` : ""}`;
}

export function useEvidenceHub(token: string | null, filters: EvidenceHubFilters = {}) {
  return useQuery({
    queryKey: ["evidence-hub", "evidence", filters],
    queryFn: () => apiGet<EvidenceHubResponse>(evidenceFilterPath(filters), { token }),
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

export function createEvidenceArchivePackage(
  token: string | null,
  payload: EvidenceArchivePackageRequest
) {
  return apiPost<EvidenceArchivePackageResponse>("/api/v1/evidence-hub/archive-packages", payload, { token });
}

export function downloadEvidenceArtifact(token: string | null, artifactId: string) {
  return apiDownload(`/api/v1/evidence-hub/artifacts/${artifactId}/download`, { token });
}
