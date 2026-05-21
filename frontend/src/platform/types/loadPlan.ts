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
