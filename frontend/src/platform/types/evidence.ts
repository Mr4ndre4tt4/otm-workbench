import type { PageResponse } from "./shared";

export type EvidenceArtifactSummary = {
  id: string;
  source_module: string;
  artifact_type: string;
  file_name: string;
  content_type: string;
  sha256: string;
  size_bytes: number;
  sensitivity_level: string;
  created_at: string | null;
};

export type EvidenceManifestSummary = {
  id: string;
  source_module: string;
  status: string;
  manifest_type: string | null;
  schema_version: string | null;
  created_at: string | null;
};

export type EvidenceItem = {
  id: string;
  project_id: string | null;
  source_module: string;
  evidence_type: string;
  status: string;
  summary: Record<string, unknown>;
  artifact: EvidenceArtifactSummary | null;
  manifest: EvidenceManifestSummary | null;
  client_safe: boolean;
  sensitivity_level: string;
  created_at: string | null;
};

export type EvidenceHubResponse = PageResponse<EvidenceItem>;

export type EvidenceHubFilters = {
  artifact_id?: string;
  client_safe?: boolean;
  evidence_type?: string;
  manifest_id?: string;
  project_id?: string;
  sensitivity_level?: string;
  source_module?: string;
  status?: string;
};

export type EvidenceArchivePackageRequest = {
  evidence_type?: string;
  project_id?: string;
  sensitivity_level?: string;
  source_module?: string;
  status?: string;
};

export type EvidenceArchivePackageResponse = {
  archive_id: string;
  artifact_id: string;
  evidence_id: string;
  file_name: string;
  manifest_id: string;
  sha256: string;
  size_bytes: number;
  summary: {
    artifact_ref_count: number;
    evidence_count: number;
    manifest_ref_count: number;
  };
};
