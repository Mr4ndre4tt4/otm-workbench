import { useQuery } from "@tanstack/react-query";

import { apiGet, apiPatch, apiPost, apiUpload } from "../api";
import type {
  MasterDataActionResult,
  MasterDataBatch,
  MasterDataRelationshipValidation,
  MasterDataTemplate,
  MasterDataTemplateDraftRequest,
  MasterDataTemplateValidation,
  MasterDataTemplatesResponse,
  MasterDataWorkbookArtifact
} from "../types";

export function useMasterDataTemplates(token: string | null) {
  return useQuery({
    queryKey: ["modules", "master-data", "templates"],
    queryFn: () => apiGet<MasterDataTemplatesResponse>("/api/v1/modules/master-data/templates", { token }),
    enabled: Boolean(token)
  });
}

export function useMasterDataTemplateDetail(token: string | null, templateCode: string | null) {
  return useQuery({
    queryKey: ["modules", "master-data", "templates", templateCode],
    queryFn: () => apiGet<MasterDataTemplate>(`/api/v1/modules/master-data/templates/${templateCode}`, { token }),
    enabled: Boolean(token && templateCode)
  });
}

export function validateMasterDataTemplate(token: string, templateCode: string) {
  return apiPost<MasterDataTemplateValidation>(
    `/api/v1/modules/master-data/templates/${templateCode}/validate`,
    {},
    { token }
  );
}

export function createMasterDataTemplateDraft(token: string, payload: MasterDataTemplateDraftRequest) {
  return apiPost<MasterDataTemplate>("/api/v1/modules/master-data/templates/drafts", payload, { token });
}

export function updateMasterDataTemplateDraft(
  token: string,
  templateCode: string,
  payload: MasterDataTemplateDraftRequest
) {
  return apiPatch<MasterDataTemplate>(`/api/v1/modules/master-data/templates/${templateCode}/draft`, payload, { token });
}

export function validateMasterDataTemplateDefinition(token: string, templateCode: string) {
  return apiPost<MasterDataTemplateValidation>(
    `/api/v1/modules/master-data/templates/${templateCode}/validate-definition`,
    {},
    { token }
  );
}

export function publishMasterDataTemplate(token: string, templateCode: string) {
  return apiPost<MasterDataTemplate>(`/api/v1/modules/master-data/templates/${templateCode}/publish`, {}, { token });
}

export function createMasterDataTemplateVersion(token: string, templateCode: string, newCode: string) {
  return apiPost<MasterDataTemplate>(
    `/api/v1/modules/master-data/templates/${templateCode}/versions`,
    { new_code: newCode },
    { token }
  );
}

export function buildMasterDataWorkbook(token: string, templateCode: string) {
  return apiPost<MasterDataWorkbookArtifact>(
    `/api/v1/modules/master-data/templates/${templateCode}/build-workbook`,
    {},
    { token }
  );
}

export function uploadMasterDataWorkbook(token: string, templateCode: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiUpload<MasterDataBatch>(`/api/v1/modules/master-data/templates/${templateCode}/batches`, formData, {
    token
  });
}

export function validateMasterDataRelationships(token: string, batchId: string) {
  return apiPost<MasterDataRelationshipValidation>(
    `/api/v1/modules/master-data/batches/${batchId}/validate-relationships`,
    {},
    { token }
  );
}

export function mapMasterDataBatch(token: string, batchId: string) {
  return apiPost<MasterDataActionResult>(`/api/v1/modules/master-data/batches/${batchId}/map`, {}, { token });
}

export function buildMasterDataOutput(token: string, batchId: string) {
  return apiPost<MasterDataActionResult>(`/api/v1/modules/master-data/batches/${batchId}/build-output`, {}, {
    token
  });
}

export function buildMasterDataCsv(token: string, batchId: string) {
  return apiPost<MasterDataActionResult>(`/api/v1/modules/master-data/batches/${batchId}/build-csv`, {}, { token });
}

export function exportMasterDataCsvPackage(token: string, batchId: string) {
  return apiPost<MasterDataActionResult>(
    `/api/v1/modules/master-data/batches/${batchId}/export-csv-package`,
    {},
    { token }
  );
}
