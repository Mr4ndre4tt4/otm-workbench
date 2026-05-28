import { useQuery } from "@tanstack/react-query";

import { apiGet, apiPatch, apiPost, apiUpload } from "../api";
import type {
  CoordinateQualityBatch,
  CoordinateQualityBatchesResponse,
  CoordinateQualityExport,
  CoordinateQualityPreview,
  CoordinateQualityRequest,
  CoordinateQualityResultsResponse,
  MasterDataActionResult,
  MasterDataArtifactsResponse,
  MasterDataBatch,
  MasterDataBatchSummary,
  MasterDataBatchesResponse,
  MasterDataCsvFilesResponse,
  MasterDataOtmImportReadiness,
  MasterDataOutputRecordsResponse,
  MasterDataRelationshipValidation,
  MasterDataScenarioPacksResponse,
  MasterDataTemplate,
  MasterDataTemplateDraftRequest,
  MasterDataTemplateSearchOperator,
  MasterDataTemplateValidation,
  MasterDataTemplatesResponse,
  MasterDataWorkbookArtifact,
  MasterDataWorkbookEditor,
  MasterDataWorkbookEditorRowsRequest,
  MasterDataWorkbookEditorValidation
} from "../types";

export type MasterDataTemplateFilters = {
  macro_object?: string;
  macro_object_operator?: MasterDataTemplateSearchOperator;
  status?: string;
  status_operator?: MasterDataTemplateSearchOperator;
  template_code?: string;
  template_code_operator?: MasterDataTemplateSearchOperator;
  template_name?: string;
  template_name_operator?: MasterDataTemplateSearchOperator;
};

function masterDataTemplateQuery(filters: MasterDataTemplateFilters = {}) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.set(key, value);
  }
  const query = params.toString();
  return query ? `/api/v1/modules/master-data/templates?${query}` : "/api/v1/modules/master-data/templates";
}

export function useMasterDataTemplates(token: string | null, filters: MasterDataTemplateFilters = {}) {
  return useQuery({
    queryKey: ["modules", "master-data", "templates", filters],
    queryFn: () => apiGet<MasterDataTemplatesResponse>(masterDataTemplateQuery(filters), { token }),
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

export function useMasterDataScenarioPacks(token: string | null) {
  return useQuery({
    queryKey: ["modules", "master-data", "scenario-packs"],
    queryFn: () => apiGet<MasterDataScenarioPacksResponse>("/api/v1/modules/master-data/scenario-packs", { token }),
    enabled: Boolean(token)
  });
}

export type MasterDataBatchFilters = {
  file_name_contains?: string;
  min_row_count?: number;
  page?: number;
  page_size?: number;
  status?: string;
  template_code?: string;
};

function masterDataBatchQuery(filters: MasterDataBatchFilters = {}, includePagination = true) {
  const params = new URLSearchParams();
  if (filters.template_code) params.set("template_code", filters.template_code);
  if (filters.status) params.set("status", filters.status);
  if (filters.file_name_contains) params.set("file_name_contains", filters.file_name_contains);
  if (filters.min_row_count && filters.min_row_count > 0) params.set("min_row_count", String(filters.min_row_count));
  if (includePagination && filters.page && filters.page > 1) params.set("page", String(filters.page));
  if (includePagination && filters.page_size && filters.page_size !== 50) params.set("page_size", String(filters.page_size));
  const query = params.toString();
  return query ? `/api/v1/modules/master-data/batches?${query}` : "/api/v1/modules/master-data/batches";
}

export function useMasterDataBatches(token: string | null, filters: MasterDataBatchFilters = {}) {
  return useQuery({
    queryKey: ["modules", "master-data", "batches", filters],
    queryFn: () => apiGet<MasterDataBatchesResponse>(masterDataBatchQuery(filters), { token }),
    enabled: Boolean(token)
  });
}

export function getMasterDataBatch(token: string, batchId: string) {
  return apiGet<MasterDataBatch>(`/api/v1/modules/master-data/batches/${batchId}`, { token });
}

export function useMasterDataBatchDetail(token: string | null, batchId: string | null) {
  return useQuery({
    queryKey: ["modules", "master-data", "batches", batchId],
    queryFn: () => apiGet<MasterDataBatch>(`/api/v1/modules/master-data/batches/${batchId}`, { token }),
    enabled: Boolean(token && batchId)
  });
}

export function useMasterDataBatchSummary(token: string | null, filters: MasterDataBatchFilters = {}) {
  const query = masterDataBatchQuery(filters, false).replace(
    "/api/v1/modules/master-data/batches",
    "/api/v1/modules/master-data/batches/summary"
  );
  return useQuery({
    queryKey: ["modules", "master-data", "batches", "summary", filters],
    queryFn: () => apiGet<MasterDataBatchSummary>(query, { token }),
    enabled: Boolean(token)
  });
}

export function useMasterDataBatchArtifacts(token: string | null, batchId: string | null) {
  return useQuery({
    queryKey: ["modules", "master-data", "batches", batchId, "artifacts"],
    queryFn: () => apiGet<MasterDataArtifactsResponse>(`/api/v1/modules/master-data/batches/${batchId}/artifacts`, { token }),
    enabled: Boolean(token && batchId)
  });
}

export function useMasterDataOutputRecords(token: string | null, batchId: string | null) {
  return useQuery({
    queryKey: ["modules", "master-data", "batches", batchId, "output-records"],
    queryFn: () => apiGet<MasterDataOutputRecordsResponse>(`/api/v1/modules/master-data/batches/${batchId}/output-records`, { token }),
    enabled: Boolean(token && batchId)
  });
}

export function useMasterDataCsvFiles(token: string | null, batchId: string | null) {
  return useQuery({
    queryKey: ["modules", "master-data", "batches", batchId, "csv-files"],
    queryFn: () => apiGet<MasterDataCsvFilesResponse>(`/api/v1/modules/master-data/batches/${batchId}/csv-files`, { token }),
    enabled: Boolean(token && batchId)
  });
}

export function useCoordinateQualityBatches(token: string | null) {
  return useQuery({
    queryKey: ["modules", "master-data", "coordinate-quality", "batches"],
    queryFn: () =>
      apiGet<CoordinateQualityBatchesResponse>("/api/v1/modules/master-data/coordinate-quality/batches", { token }),
    enabled: Boolean(token)
  });
}

export function useCoordinateQualityBatchDetail(token: string | null, batchId: string | null) {
  return useQuery({
    queryKey: ["modules", "master-data", "coordinate-quality", "batches", batchId],
    queryFn: () =>
      apiGet<CoordinateQualityBatch>(`/api/v1/modules/master-data/coordinate-quality/batches/${batchId}`, { token }),
    enabled: Boolean(token && batchId)
  });
}

export function useCoordinateQualityResults(token: string | null, batchId: string | null) {
  return useQuery({
    queryKey: ["modules", "master-data", "coordinate-quality", "batches", batchId, "results"],
    queryFn: () =>
      apiGet<CoordinateQualityResultsResponse>(
        `/api/v1/modules/master-data/coordinate-quality/batches/${batchId}/results`,
        { token }
      ),
    enabled: Boolean(token && batchId)
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

export function useMasterDataWorkbookEditor(token: string | null, templateCode: string | null) {
  return useQuery({
    queryKey: ["modules", "master-data", "workbook-editor", templateCode],
    queryFn: () =>
      apiGet<MasterDataWorkbookEditor>(`/api/v1/modules/master-data/templates/${templateCode}/workbook-editor`, {
        token
      }),
    enabled: Boolean(token && templateCode)
  });
}

export function validateMasterDataWorkbookEditorRows(
  token: string,
  templateCode: string,
  payload: MasterDataWorkbookEditorRowsRequest
) {
  return apiPost<MasterDataWorkbookEditorValidation>(
    `/api/v1/modules/master-data/templates/${templateCode}/workbook-editor/validate`,
    payload,
    { token }
  );
}

export function createMasterDataBatchFromWorkbookEditorRows(
  token: string,
  templateCode: string,
  payload: MasterDataWorkbookEditorRowsRequest
) {
  return apiPost<MasterDataBatch>(
    `/api/v1/modules/master-data/templates/${templateCode}/workbook-editor/batches`,
    payload,
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

export function getMasterDataOtmImportReadiness(token: string, batchId: string) {
  return apiGet<MasterDataOtmImportReadiness>(
    `/api/v1/modules/master-data/batches/${batchId}/otm-import-readiness`,
    { token }
  );
}

export function submitMasterDataBatchToOtm(token: string, batchId: string) {
  return apiPost<Record<string, unknown>>(`/api/v1/modules/master-data/batches/${batchId}/submit-otm`, {}, { token });
}

export function previewCoordinateQuality(token: string, payload: CoordinateQualityRequest) {
  return apiPost<CoordinateQualityPreview>("/api/v1/modules/master-data/coordinate-quality/validate", payload, { token });
}

export function createCoordinateQualityBatch(token: string, payload: CoordinateQualityRequest) {
  return apiPost<CoordinateQualityBatch>("/api/v1/modules/master-data/coordinate-quality/batches", payload, { token });
}

export function exportCoordinateQualityBatch(token: string, batchId: string) {
  return apiPost<CoordinateQualityExport>(
    `/api/v1/modules/master-data/coordinate-quality/batches/${batchId}/export`,
    {},
    { token }
  );
}
