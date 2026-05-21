import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../api";
import type { AssetItem, AssetsResponse, AssetVersionsResponse } from "../types";

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
