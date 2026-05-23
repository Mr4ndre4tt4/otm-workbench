import type { PageResponse } from "./shared";

export type OrderReleaseTemplate = {
  id: string;
  code: string;
  name: string;
  version: number;
  status: string;
  macro_object_code: string;
  description: string;
  required_columns: string[];
  optional_columns: string[];
  defaults: Record<string, unknown>;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type OrderReleaseTemplatesResponse = PageResponse<OrderReleaseTemplate>;

export type OrderReleaseBatchRow = {
  id: string;
  batch_id: string;
  row_number: number;
  release_gid: string | null;
  status: string;
  normalized_json: Record<string, unknown>;
  issues: Array<Record<string, unknown>>;
  created_at: string | null;
  updated_at: string | null;
};

export type OrderReleaseBatch = {
  id: string;
  template_id: string;
  status: string;
  file_name: string;
  row_count: number;
  release_count: number;
  issue_count: number;
  summary: Record<string, unknown>;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
  rows?: OrderReleaseBatchRow[];
};

export type OrderReleaseBatchesResponse = PageResponse<OrderReleaseBatch>;

export type OrderReleaseBatchCreateRequest = {
  template_id: string;
  file_name: string;
  rows: Array<Record<string, unknown>>;
};

export type OrderReleaseXmlPreview = {
  batch_id: string;
  job_id: string;
  release_count: number;
  line_count: number;
  xml: string;
};

export type OrderReleaseXmlArtifact = {
  artifact_id: string;
  batch_id: string;
  content_type?: string;
  download_url?: string | null;
  evidence_id: string;
  file_name: string;
  job_id: string;
  release_count: number;
  line_count: number;
  sha256: string;
  size_bytes: number;
  status?: string;
};

export type OrderReleaseArtifact = {
  id: string;
  batch_id: string;
  source_module: string;
  artifact_type: string;
  file_name: string;
  content_type: string;
  sha256: string;
  size_bytes: number;
  sensitivity_level: string;
  download_url: string | null;
};

export type OrderReleaseArtifactsResponse = {
  batch_id: string;
  items: OrderReleaseArtifact[];
  total: number;
};
