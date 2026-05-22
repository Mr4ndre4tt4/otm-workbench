import { useQuery } from "@tanstack/react-query";

import { apiDownload, apiGet, apiPost, apiUpload, type DownloadResponse } from "../api";
import type {
  AssetCreateRequest,
  AssetItem,
  AssetLink,
  AssetLinkCreateRequest,
  AssetLinksResponse,
  AssetsResponse,
  AssetVersion,
  AssetVersionsResponse
} from "../types";

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

export function useAssetLinks(token: string | null, assetId: string | null) {
  return useQuery({
    queryKey: ["modules", "assets", "assets", assetId, "links"],
    queryFn: () => apiGet<AssetLinksResponse>(`/api/v1/modules/assets/assets/${assetId}/links`, { token }),
    enabled: Boolean(token && assetId)
  });
}

export function createAsset(token: string | null, payload: AssetCreateRequest) {
  return apiPost<AssetItem>("/api/v1/modules/assets/assets", payload, { token });
}

export function uploadAssetVersion(token: string | null, assetId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiUpload<AssetVersion>(`/api/v1/modules/assets/assets/${assetId}/versions`, formData, { token });
}

export function createAssetLink(token: string | null, assetId: string, payload: AssetLinkCreateRequest) {
  return apiPost<AssetLink>(`/api/v1/modules/assets/assets/${assetId}/links`, payload, { token });
}

export function archiveAsset(token: string | null, assetId: string) {
  return apiPost<AssetItem>(`/api/v1/modules/assets/assets/${assetId}/archive`, {}, { token });
}

export function downloadCurrentAssetVersion(token: string | null, assetId: string): Promise<DownloadResponse> {
  return apiDownload(`/api/v1/modules/assets/assets/${assetId}/download`, { token });
}
