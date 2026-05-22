import type { PageResponse } from "./shared";

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

export type MasterDataBatch = {
  batch_id: string;
  template_code: string;
  status: string;
  file_name?: string;
  sheet_count?: number;
  row_count?: number;
  sheets?: Array<{
    sheet_code: string;
    row_count: number;
  }>;
  summary?: Record<string, unknown>;
};

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
