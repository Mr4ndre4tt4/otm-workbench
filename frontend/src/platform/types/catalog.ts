import type { PageResponse } from "./shared";

export type CatalogMacroObjectSummary = {
  table_count: number;
  dependency_count: number;
  validated_table_count: number;
  all_tables_validated: boolean;
  csvutil_table_count: number;
  cutover_table_count: number;
};

export type CatalogMacroObject = {
  id: string;
  code: string;
  name: string;
  category: string;
  description: string;
  default_load_order: number;
  default_method: string;
  method_options: string[];
  allow_cutover: boolean;
  allow_csvutil: boolean;
  evidence_required_default: boolean;
  summary?: CatalogMacroObjectSummary;
};

export type CatalogMacroObjectsResponse = PageResponse<CatalogMacroObject>;

export type CatalogMacroObjectTable = {
  id: string;
  table_name: string;
  relationship_role: string;
  is_primary_table: boolean;
  is_required: boolean;
  data_category: string;
  validated_by_datadict: boolean;
  allow_csvutil: boolean;
  allow_cutover: boolean;
};

export type CatalogMacroObjectTablesResponse = PageResponse<CatalogMacroObjectTable>;

export type CatalogLoadPlanItem = {
  macro_object_code: string;
  macro_object_name: string;
  dependency_role: string;
  dependency_type: string;
  is_required: boolean;
  tables: string[];
  table_count: number;
  all_tables_validated: boolean;
};

export type CatalogMacroObjectLoadPlan = {
  macro_object_code: string;
  items: CatalogLoadPlanItem[];
  summary: {
    step_count: number;
    dependency_count: number;
    target_table_count: number;
    all_target_tables_validated: boolean;
  };
};
