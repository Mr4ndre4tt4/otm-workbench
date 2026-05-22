import type { PageResponse } from "./shared";

export type LoadPlanPackageSummary = {
  source_module?: string;
  package_type?: string;
  catalog_macro_object_code?: string;
  catalog_load_plan_path?: string;
  table_count?: number;
  row_count?: number;
  has_export_artifact?: boolean;
  has_approval_evidence?: boolean;
};

export type LoadPlanSequenceItem = {
  position: number;
  table_name: string;
  row_count: number;
  requirement_level: string;
};

export type LoadPlanPackage = {
  id: string;
  project_id: string | null;
  environment_id: string | null;
  profile_id: string | null;
  source_module: string;
  source_entity_type: string;
  source_entity_id: string;
  package_type: string;
  status: string;
  artifact_id: string | null;
  manifest_id: string | null;
  evidence_id: string | null;
  approval_evidence_id: string | null;
  load_sequence: LoadPlanSequenceItem[];
  summary: LoadPlanPackageSummary;
  created_by: string | null;
  registered_at: string | null;
};

export type LoadPlanPackagesResponse = PageResponse<LoadPlanPackage>;

export type LoadPlanSummary = {
  registered_packages: number;
  by_source_module: Record<string, number>;
  by_status: Record<string, number>;
  by_catalog_macro_object: Record<
    string,
    {
      package_count: number;
      catalog_load_plan_path?: string;
    }
  >;
  next_actions: string[];
};

export type CutoverChecklistItem = {
  id: string;
  checklist_id: string;
  package_id: string;
  template_item_id: string;
  item_code: string;
  title: string;
  status: string;
  method: string;
  table_name: string | null;
  sort_order: number;
  evidence_required: boolean;
  evidence_id: string | null;
  details: Record<string, unknown>;
};

export type CutoverChecklist = {
  id: string;
  project_id: string | null;
  environment_id: string | null;
  profile_id: string | null;
  template_id: string;
  template_code: string | null;
  package_id: string;
  status: string;
  package_type: string;
  catalog_macro_object_code: string | null;
  summary: {
    source_module?: string;
    package_type?: string;
    package_status?: string;
    item_count?: number;
    package_item_count?: number;
    table_item_count?: number;
    status_counts?: Record<string, number>;
    catalog_macro_object_code?: string;
    catalog_load_plan_path?: string;
  };
  evidence_id: string | null;
  created_by: string | null;
  items: CutoverChecklistItem[];
};

export type CutoverReadinessBlocker = {
  code: string;
  severity: string;
  message: string;
  item_id?: string;
  item_code?: string;
  table_name?: string | null;
  details?: Record<string, unknown>;
};

export type CutoverChecklistReadiness = {
  checklist_id: string;
  package_id: string;
  status: string;
  summary: {
    ready: boolean;
    item_count: number;
    done_count: number;
    pending_count: number;
    blocked_count: number;
    skipped_count: number;
    missing_evidence_count: number;
    blocker_count: number;
    error_count: number;
    warning_count: number;
    status_counts: Record<string, number>;
    catalog_macro_object_code?: string;
    catalog_load_plan_path?: string;
  };
  blockers: CutoverReadinessBlocker[];
  evidence_id?: string;
};

export type CsvutilBuild = {
  id: string;
  project_id: string | null;
  environment_id: string | null;
  profile_id: string | null;
  package_id: string;
  status: string;
  ctl_artifact_id: string | null;
  cl_artifact_id: string | null;
  manifest_id: string | null;
  evidence_id: string | null;
  summary: {
    package_type?: string;
    table_count?: number;
    row_count?: number;
    catalog_macro_object_code?: string;
    catalog_load_plan_path?: string;
    parameter_set?: Record<string, string>;
  };
  created_by: string | null;
  built_at: string | null;
};

export type LoadPlanZipFinding = {
  severity: string;
  code: string;
  message: string;
  table_name?: string | null;
  file_name?: string | null;
  details?: Record<string, unknown>;
};

export type LoadPlanZipAnalysis = {
  id: string;
  project_id: string | null;
  environment_id: string | null;
  profile_id: string | null;
  package_id: string;
  status: string;
  source_artifact_id: string | null;
  source_manifest_id: string | null;
  manifest_id: string | null;
  evidence_id: string | null;
  summary: {
    package_type?: string;
    file_count?: number;
    csv_file_count?: number;
    table_count?: number;
    row_count?: number;
    finding_count?: number;
    error_count?: number;
    warning_count?: number;
    catalog_macro_object_code?: string;
    catalog_load_plan_path?: string;
  };
  findings: LoadPlanZipFinding[];
  created_by: string | null;
  analyzed_at: string | null;
};

export type LoadPlanReviewItem = {
  id: string;
  project_id: string | null;
  environment_id: string | null;
  profile_id: string | null;
  package_id: string;
  zip_analysis_id: string;
  source_type: string;
  source_code: string;
  severity: string;
  status: string;
  category: string;
  table_name: string | null;
  file_name: string | null;
  title: string;
  description: string;
  details: Record<string, unknown>;
  created_by: string | null;
  created_at: string | null;
  latest_decision_id?: string | null;
  latest_decision_status?: string | null;
  latest_decided_at?: string | null;
};

export type LoadPlanReviewQueueResponse = PageResponse<LoadPlanReviewItem>;

export type LoadPlanReviewQueueGeneration = {
  analysis_id: string;
  package_id: string;
  created_count: number;
  existing_count: number;
  catalog_macro_object_code?: string;
  catalog_load_plan_path?: string;
  items: LoadPlanReviewItem[];
};

export type LoadPlanReviewDecision = {
  id: string;
  project_id: string | null;
  environment_id: string | null;
  profile_id: string | null;
  package_id: string;
  review_item_id: string;
  decision_status: string;
  decision_note: string;
  evidence_id: string | null;
  decided_by: string | null;
  decided_at: string | null;
  catalog_macro_object_code?: string;
  catalog_load_plan_path?: string;
  review_item: LoadPlanReviewItem;
};

export type LoadPlanCutoverReadiness = {
  id: string;
  project_id: string | null;
  environment_id: string | null;
  profile_id: string | null;
  package_id: string;
  sequence_snapshot_id: string | null;
  status: string;
  readiness: Record<string, unknown>;
  blockers: CutoverReadinessBlocker[];
  summary: Record<string, unknown>;
  evidence_id: string | null;
  generated_by: string | null;
  generated_at: string | null;
};

export type LoadPlanSequenceSnapshot = {
  id: string;
  project_id: string | null;
  environment_id: string | null;
  profile_id: string | null;
  package_id: string;
  status: string;
  sequence: Array<Record<string, unknown>>;
  blockers: CutoverReadinessBlocker[];
  summary: Record<string, unknown>;
  evidence_id: string | null;
  generated_by: string | null;
  generated_at: string | null;
};

export type LoadPlanCutoverReadinessGeneration = {
  items: LoadPlanCutoverReadiness[];
  summary: Record<string, unknown>;
};

export type LoadPlanReadinessExport = {
  id: string;
  project_id: string | null;
  environment_id: string | null;
  profile_id: string | null;
  package_id: string;
  readiness_id: string;
  status: string;
  artifact_id: string | null;
  manifest_id: string | null;
  evidence_id: string | null;
  summary: Record<string, unknown>;
  exported_by: string | null;
  exported_at: string | null;
};

export type CutoverPackageExport = {
  status: string;
  checklist_id: string;
  package_id: string;
  readiness_evidence_id: string | null;
  readiness_status: string | null;
  csvutil_build_count: number;
  exported_at: string | null;
  exported_by: string | null;
  catalog_macro_object_code?: string;
  catalog_load_plan_path?: string;
  artifact_id: string | null;
  manifest_id: string | null;
  evidence_id: string | null;
  file_name: string | null;
  content_type: string | null;
};

export type CutoverGoNoGoDecision = {
  decision: string;
  checklist_id: string;
  package_id: string;
  readiness_status: string | null;
  readiness_evidence_id: string | null;
  cutover_package_evidence_id: string | null;
  blocker_count: number;
  evidence_id: string | null;
  blockers: CutoverReadinessBlocker[];
  decided_at?: string | null;
  decided_by?: string | null;
  catalog_macro_object_code?: string;
  catalog_load_plan_path?: string;
};

export type CutoverHandoffEligibility = {
  package_id: string;
  eligible: boolean;
  status: string;
  readiness_id: string | null;
  readiness_status: string | null;
  readiness_export_id: string | null;
  readiness_export_evidence_id: string | null;
  archive_evidence_id: string | null;
  checklist_id: string | null;
  checklist_readiness_status: string | null;
  checklist_readiness_evidence_id: string | null;
  blockers: CutoverReadinessBlocker[];
  next_actions: string[];
  catalog_macro_object_code?: string;
  catalog_load_plan_path?: string;
};
