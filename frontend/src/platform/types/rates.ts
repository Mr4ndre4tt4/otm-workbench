import type { CockpitArtifact, CockpitJob } from "./cockpit";
import type { AvailableAction, ModuleBlocker, ModuleCount } from "./shared";

export type RatesSummaryItem = {
  id: string;
  code: string;
  display_name: string;
  status: string;
  project_id: string | null;
  profile_id: string | null;
  environment_id: string | null;
  domain_name: string | null;
  summary: {
    ready_for_approval: boolean;
    ready_for_export: boolean;
    table_count: number;
    row_count: number;
    issue_summary: Record<string, number>;
  };
  badges: string[];
  available_actions: AvailableAction[];
};

export type RateBatchTable = {
  id: string;
  batch_id: string;
  table_name: string;
  sequence_index: number;
  requirement_level: string;
  row_count: number;
  status: string;
};

export type RateBatchDetail = {
  id: string;
  project_id: string | null;
  environment_id: string | null;
  profile_id: string | null;
  scenario_code: string;
  catalog_macro_object_code: string;
  catalog_load_plan_path: string;
  name: string;
  description: string;
  status: string;
  source_type: string;
  domain_name: string;
  created_by: string | null;
  summary_json: string;
  tables: RateBatchTable[];
  available_actions: AvailableAction[];
};

export type RateArtifact = {
  id: string;
  artifact_type: string;
  file_name: string;
  content_type: string;
  sha256: string;
  size_bytes: number;
  sensitivity_level: string;
  download_url?: string;
};

export type RateEvidence = {
  id: string;
  evidence_type: string;
  status: string;
  summary_json: string;
  artifact_id: string | null;
  manifest_id: string | null;
  client_safe: boolean;
  sensitivity_level: string;
};

export type RateBatchArtifactsResponse = {
  batch_id: string;
  catalog_macro_object_code: string;
  catalog_load_plan_path: string;
  items: RateArtifact[];
  total: number;
};

export type RateBatchEvidenceResponse = {
  batch_id: string;
  catalog_macro_object_code: string;
  catalog_load_plan_path: string;
  items: RateEvidence[];
  total: number;
};

export type RatesSummary = {
  module_id: "rates";
  status: string;
  title: string;
  description: string;
  primary_object: "rate_batch";
  counts: ModuleCount[];
  recent_objects: RatesSummaryItem[];
  open_blockers: ModuleBlocker[];
  recent_jobs: CockpitJob[];
  recent_artifacts: CockpitArtifact[];
  available_actions: AvailableAction[];
};
