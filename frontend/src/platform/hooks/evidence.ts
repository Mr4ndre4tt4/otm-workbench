import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../api";
import type { EvidenceHubResponse, EvidenceItem } from "../types";

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
