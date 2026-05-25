import type { PageResponse } from "./shared";
import type { AvailableAction } from "./shared";

export type MasterDataTemplateField = {
  name: string;
  label: string;
  target_column: string;
  required?: boolean;
};

export type MasterDataTemplateSheet = {
  code: string;
  name: string;
  target_table: string;
  fields: MasterDataTemplateField[];
};

export type MasterDataTemplate = {
  id: string;
  code: string;
  name: string;
  version: string | number;
  status: string;
  catalog_macro_object_code: string;
  data_category: string;
  target_tables: string[];
  sheets: MasterDataTemplateSheet[];
  definition?: MasterDataTemplateDefinition;
  available_actions?: AvailableAction[];
  description: string;
  created_at: string | null;
  updated_at: string | null;
};

export type MasterDataTemplatesResponse = PageResponse<MasterDataTemplate>;

export type MasterDataTemplateValidation = {
  template_code: string;
  valid: boolean;
  severity: string;
  issues: Array<{
    code: string;
    message: string;
    severity?: string;
    table_name?: string;
    column_name?: string;
  }>;
  summary: {
    sheet_count: number;
    field_count: number;
    validated_table_count: number;
    validated_column_count: number;
  };
};

export type MasterDataWorkbookArtifact = {
  template_code: string;
  artifact_id: string;
  file_name: string;
  content_type: string;
  sheet_count: number;
  field_count: number;
};

export type MasterDataWorkbookEditor = {
  template_code: string;
  template_name?: string;
  version?: string | number;
  sheets: Array<{
    code: string;
    name: string;
    target_table: string;
    fields: Array<{
      field_key: string;
      label: string;
      data_type: string;
      required: boolean;
    }>;
    starter_rows: Array<{
      row_id: string;
      values: Record<string, string>;
    }>;
  }>;
  relationship_rules: Array<Record<string, unknown>>;
  documentation_refs: MasterDataTemplateDefinitionRef[];
};

export type MasterDataWorkbookEditorRowsRequest = {
  file_name?: string;
  sheets: Array<{
    sheet_code: string;
    rows: Array<{
      row_id: string;
      values: Record<string, string>;
    }>;
  }>;
};

export type MasterDataWorkbookEditorValidation = {
  template_code: string;
  valid: boolean;
  status: "VALID" | "INVALID";
  issues: Array<{
    code: string;
    message: string;
    severity?: string;
    sheet_code?: string;
    row_id?: string;
    field_key?: string;
    parent_sheet_code?: string;
    parent_field_key?: string;
  }>;
  summary: {
    sheet_count: number;
    row_count: number;
    issue_count: number;
  };
};

export type MasterDataBatch = {
  batch_id: string;
  template_code: string;
  status: string;
  content_type?: string;
  file_name?: string;
  issue_count?: number;
  sheet_count?: number;
  row_count?: number;
  sheets?: Array<{
    sheet_code: string;
    row_count: number;
  }>;
  sheet_summaries?: Array<{
    sheet_code: string;
    target_table?: string;
    row_count: number;
  }>;
  csv_file_count?: number;
  available_actions?: AvailableAction[];
  summary?: Record<string, unknown>;
};

export type MasterDataBatchesResponse = PageResponse<MasterDataBatch>;

export type MasterDataBatchSummaryBucket = {
  batch_count: number;
  issue_count: number;
  row_count: number;
  status?: string;
  template_code?: string;
};

export type MasterDataBatchSummary = {
  latest_batch_id?: string | null;
  status_breakdown: MasterDataBatchSummaryBucket[];
  template_breakdown: MasterDataBatchSummaryBucket[];
  total_batches: number;
  total_issues: number;
  total_rows: number;
};

export type MasterDataArtifact = {
  id: string;
  artifact_type: string;
  file_name: string;
  content_type: string;
  sha256: string;
  size_bytes: number;
  sensitivity_level: string;
  evidence_id?: string;
  created_at?: string | null;
  availability_status?: "AVAILABLE" | "FILE_MISSING";
  download_url?: string | null;
};

export type MasterDataArtifactsResponse = PageResponse<MasterDataArtifact>;

export type MasterDataOtmImportReadiness = {
  batch_id: string;
  status: "BLOCKED" | "GUARDED" | "READY";
  ready: boolean;
  required_capability: string;
  recommended_transport: string;
  official_source_basis: string[];
  blockers: Array<{
    code: string;
    message: string;
  }>;
  artifact: null | {
    artifact_id: string;
    file_name: string;
    sha256: string;
    content_type: string;
  };
};

export type MasterDataOutputRecord = {
  id: string;
  batch_id: string;
  template_code: string;
  target_table: string;
  record_index: number;
  payload: Record<string, unknown>;
  created_at?: string | null;
  updated_at?: string | null;
};

export type MasterDataOutputRecordsResponse = PageResponse<MasterDataOutputRecord>;

export type MasterDataCsvFile = {
  id: string;
  batch_id: string;
  template_code: string;
  table_name: string;
  file_name: string;
  row_count: number;
  content_preview: string;
  line_count: number;
  created_at?: string | null;
  updated_at?: string | null;
};

export type MasterDataCsvFilesResponse = PageResponse<MasterDataCsvFile>;

export type MasterDataRelationshipValidation = {
  batch_id: string;
  status: string;
  valid: boolean;
  issues: Array<{
    code: string;
    message: string;
    severity?: string;
    sheet_code?: string;
    row_number?: number;
  }>;
  summary: Record<string, unknown>;
};

export type MasterDataActionResult = {
  batch_id: string;
  status: string;
  summary?: Record<string, unknown>;
  evidence_id?: string;
  artifact_id?: string;
  manifest_id?: string;
  file_name?: string;
  content_type?: string;
};

export type MasterDataTemplateDefinitionRef = {
  source_type: "DATA_DICTIONARY" | "ORACLE_OFFICIAL" | "USER_CONFIRMED";
  scope: string;
  note: string;
};

export type MasterDataTemplateDefinition = {
  schema_version: "master-data-template-definition/v2";
  template: {
    code: string;
    name: string;
    version: number;
    status: string;
    catalog_macro_object_code: string;
    data_category: string;
  };
  target_tables: Array<{
    table_name: string;
    sequence: number;
    required: boolean;
  }>;
  sheets: Array<{
    code: string;
    name: string;
    sequence: number;
    field_keys: string[];
  }>;
  fields: Array<{
    field_key: string;
    label: string;
    data_type: string;
    required: boolean;
    sheet_code: string;
  }>;
  mappings: Array<{
    mapping_key: string;
    source_type: "USER_FIELD" | "FIXED_VALUE" | "DEFAULT_VALUE";
    source_field_key?: string;
    fixed_value?: string;
    default_value?: string;
    target_table: string;
    target_column: string;
    required: boolean;
  }>;
  relationship_rules: Array<Record<string, unknown>>;
  documentation_refs: MasterDataTemplateDefinitionRef[];
};

export type MasterDataTemplateDraftRequest = {
  code: string;
  name: string;
  catalog_macro_object_code: string;
  data_category: string;
  target_tables: MasterDataTemplateDefinition["target_tables"];
  sheets: MasterDataTemplateDefinition["sheets"];
  fields: MasterDataTemplateDefinition["fields"];
  mappings: MasterDataTemplateDefinition["mappings"];
  relationship_rules: MasterDataTemplateDefinition["relationship_rules"];
  documentation_refs: MasterDataTemplateDefinition["documentation_refs"];
};

export type MasterDataScenarioPack = {
  code: string;
  name: string;
  description: string;
  catalog_macro_object_code: string;
  target_tables: string[];
  summary: {
    sheet_count: number;
    field_count: number;
    mapping_count: number;
    relationship_rule_count: number;
  };
  documentation_refs: MasterDataTemplateDefinitionRef[];
  draft_payload: MasterDataTemplateDraftRequest;
};

export type MasterDataScenarioPacksResponse = PageResponse<MasterDataScenarioPack>;

export type CoordinateQualityRecord = {
  location_gid: string;
  location_name?: string | null;
  address_line?: string | null;
  city?: string | null;
  province_code?: string | null;
  postal_code?: string | null;
  country_code3_gid?: string | null;
  lat?: number | null;
  lon?: number | null;
};

export type CoordinateQualityRequest = {
  records: CoordinateQualityRecord[];
  fake_candidates: Record<string, { lat: number; lon: number; source?: string }>;
  source_type?: string;
  source_batch_id?: string | null;
};

export type CoordinateQualitySummary = {
  total_count: number;
  processed_count: number;
  ok_count: number;
  corrected_count: number;
  review_count: number;
  divergent_count: number;
  failed_count: number;
};

export type CoordinateQualityResult = {
  id?: string;
  batch_id?: string;
  location_gid: string;
  location_name: string | null;
  address: Record<string, unknown>;
  country_code3_gid: string | null;
  province_code: string | null;
  postal_code: string | null;
  lat_orig: string | number | null;
  lon_orig: string | number | null;
  lat_new: string | number | null;
  lon_new: string | number | null;
  status: string;
  source: string | null;
  diff_lat: string | number | null;
  diff_lon: string | number | null;
  orig_valid_uf: boolean;
  new_valid_uf: boolean;
  issue: Record<string, unknown>;
};

export type CoordinateQualityPreview = {
  summary: CoordinateQualitySummary;
  results: CoordinateQualityResult[];
};

export type CoordinateQualityBatch = {
  batch_id: string;
  status: string;
  provider_mode: string;
  summary: CoordinateQualitySummary;
  issues: Array<Record<string, unknown>>;
  created_at?: string | null;
  updated_at?: string | null;
};

export type CoordinateQualityBatchesResponse = PageResponse<CoordinateQualityBatch>;
export type CoordinateQualityResultsResponse = PageResponse<CoordinateQualityResult>;

export type CoordinateQualityExport = {
  batch_id: string;
  artifact_id: string;
  manifest_id: string;
  evidence_id: string;
  file_name: string;
  sha256: string;
  size_bytes: number;
};
