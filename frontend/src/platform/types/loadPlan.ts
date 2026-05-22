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
