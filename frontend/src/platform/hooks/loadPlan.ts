import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../api";
import type { LoadPlanPackage, LoadPlanPackagesResponse, LoadPlanSummary } from "../types";

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
