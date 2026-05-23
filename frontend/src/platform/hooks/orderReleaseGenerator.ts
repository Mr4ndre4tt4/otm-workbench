import { useQuery } from "@tanstack/react-query";

import { apiDownload, apiGet, apiPost, type DownloadResponse } from "../api";
import type {
  OrderReleaseArtifactsResponse,
  OrderReleaseBatch,
  OrderReleaseBatchCreateRequest,
  OrderReleaseBatchesResponse,
  OrderReleaseTemplate,
  OrderReleaseTemplateCreateRequest,
  OrderReleaseTemplateVersionCreateRequest,
  OrderReleaseTemplatesResponse,
  OrderReleaseXmlArtifact,
  OrderReleaseXmlPreview
} from "../types";

export function useOrderReleaseTemplates(token: string | null) {
  return useQuery({
    queryKey: ["modules", "order-release-generator", "templates"],
    queryFn: () => apiGet<OrderReleaseTemplatesResponse>("/api/v1/modules/order-release-generator/templates", { token }),
    enabled: Boolean(token)
  });
}

export function useOrderReleaseBatches(token: string | null) {
  return useQuery({
    queryKey: ["modules", "order-release-generator", "batches"],
    queryFn: () => apiGet<OrderReleaseBatchesResponse>("/api/v1/modules/order-release-generator/batches", { token }),
    enabled: Boolean(token)
  });
}

export function useOrderReleaseArtifacts(token: string | null, batchId: string | null) {
  return useQuery({
    queryKey: ["modules", "order-release-generator", "batches", batchId, "artifacts"],
    queryFn: () =>
      apiGet<OrderReleaseArtifactsResponse>(`/api/v1/modules/order-release-generator/batches/${batchId}/artifacts`, {
        token
      }),
    enabled: Boolean(token && batchId)
  });
}

export function createOrderReleaseTemplate(token: string | null, payload: OrderReleaseTemplateCreateRequest) {
  return apiPost<OrderReleaseTemplate>("/api/v1/modules/order-release-generator/templates", payload, { token });
}

export function createOrderReleaseTemplateVersion(
  token: string | null,
  templateId: string,
  payload: OrderReleaseTemplateVersionCreateRequest
) {
  return apiPost<OrderReleaseTemplate>(`/api/v1/modules/order-release-generator/templates/${templateId}/versions`, payload, { token });
}

export function createOrderReleaseBatch(token: string | null, payload: OrderReleaseBatchCreateRequest) {
  return apiPost<OrderReleaseBatch>("/api/v1/modules/order-release-generator/batches", payload, { token });
}

export function previewOrderReleaseXml(token: string | null, batchId: string) {
  return apiPost<OrderReleaseXmlPreview>(`/api/v1/modules/order-release-generator/batches/${batchId}/preview-xml`, {}, { token });
}

export function generateOrderReleaseXmlArtifact(token: string | null, batchId: string) {
  return apiPost<OrderReleaseXmlArtifact>(
    `/api/v1/modules/order-release-generator/batches/${batchId}/generate-xml-artifact`,
    {},
    { token }
  );
}

export function submitOrderReleaseToOtm(token: string | null, batchId: string) {
  return apiPost<Record<string, unknown>>(`/api/v1/modules/order-release-generator/batches/${batchId}/submit-otm`, {}, { token });
}

export function downloadOrderReleaseArtifact(token: string | null, href: string): Promise<DownloadResponse> {
  return apiDownload(href, { token });
}
