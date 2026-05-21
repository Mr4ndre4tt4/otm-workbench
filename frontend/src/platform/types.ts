export type PageResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type NavigationItem = {
  id: string;
  label: string;
  path: string;
  status: string;
};

export type NavigationResponse = PageResponse<NavigationItem>;

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
};

export type IdName = {
  id: string;
  name: string;
};

export type IdNameResponse = PageResponse<IdName>;

export type ActiveContextUpdate = {
  project_id: string | null;
  profile_id: string | null;
  environment_id: string | null;
  domain_name: string | null;
  can_view_all_domains: boolean;
};

export type ActiveContextResponse = ActiveContextUpdate & {
  user_id?: string;
  allowed_domains: string[];
};

export type AvailableAction = {
  key: string;
  label: string;
  method: string;
  href: string;
  variant: string;
  icon_key: string;
  disabled: boolean;
  disabled_reason: string | null;
  requires_confirmation: boolean;
  permission?: string | null;
  result_hint?: "download" | "refresh_list" | "refresh_object" | string | null;
};

export type ModuleCount = {
  key: string;
  label: string;
  value: number;
  severity: "neutral" | "success" | "warning" | "danger";
};

export type ModuleBlocker = {
  object_id: string;
  object_type: string;
  severity: string;
  codes: string[];
  message: string;
};

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

export type AssetItem = {
  id: string;
  project_id: string | null;
  profile_id: string | null;
  environment_id: string | null;
  name: string;
  description: string;
  asset_type: string;
  category: string;
  visibility: string;
  scope_type: string;
  sensitivity: string;
  status: string;
  module_id: string | null;
  macro_object_code: string | null;
  otm_table_name: string | null;
  tags: string[];
  current_version_id: string | null;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type AssetVersion = {
  id: string;
  asset_id: string;
  version_number: number;
  status: string;
  file_name: string;
  content_type: string;
  sha256: string;
  size_bytes: number;
  uploaded_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type AssetsResponse = PageResponse<AssetItem>;
export type AssetVersionsResponse = PageResponse<AssetVersion>;

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
  version: string;
  status: string;
  catalog_macro_object_code: string;
  data_category: string;
  target_tables: string[];
  sheets: MasterDataTemplateSheet[];
  description: string;
  created_at: string | null;
  updated_at: string | null;
};

export type MasterDataTemplatesResponse = PageResponse<MasterDataTemplate>;

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

export type IntegrationDefinition = {
  id: string;
  code: string;
  name: string;
  description: string;
  source_system: string;
  target_system: string;
  source_format: string;
  target_format: string;
  status: string;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationTransformType = {
  id: string;
  code: string;
  name: string;
  description: string;
  requires_expression: boolean;
  status: string;
  sequence_index: number;
  system_seeded: boolean;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationPayloadArtifact = {
  id: string;
  definition_id: string;
  artifact_id: string;
  payload_role: string;
  payload_format: string;
  file_name: string;
  description: string;
  content_type: string;
  sha256: string;
  size_bytes: number;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationSchemaDocument = {
  id: string;
  definition_id: string;
  payload_artifact_id: string | null;
  payload_format: string;
  root_name: string;
  node_count: number;
  status: string;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationMapping = {
  id: string;
  definition_id: string;
  source_schema_document_id: string | null;
  target_schema_document_id: string | null;
  source_path: string;
  target_path: string;
  transform_type: string;
  description: string;
  sequence_index: number;
  status: string;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationDefinitionsResponse = PageResponse<IntegrationDefinition>;
export type IntegrationTransformTypesResponse = PageResponse<IntegrationTransformType>;
export type IntegrationPayloadArtifactsResponse = PageResponse<IntegrationPayloadArtifact>;
export type IntegrationSchemaDocumentsResponse = PageResponse<IntegrationSchemaDocument>;
export type IntegrationMappingsResponse = PageResponse<IntegrationMapping>;

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

export type UserPreferences = {
  theme_mode: "light" | "dark" | "system";
  follow_system_theme: boolean;
  density: "comfortable" | "compact";
  sidebar_mode: "expanded" | "collapsed";
};

export type SetupStatus = {
  status: string;
  profile_count: number;
  environment_count: number;
  active_context_selected: boolean;
  missing_requirements: string[];
};

export type CockpitJob = {
  id: string;
  job_type: string;
  source_module: string;
  status: string;
  progress: number;
  input_present: boolean;
  result_present: boolean;
};

export type CockpitEvidence = {
  id: string;
  source_module: string;
  evidence_type: string;
  status: string;
  summary: Record<string, unknown>;
};

export type CockpitArtifact = {
  id: string;
  source_module: string;
  artifact_type: string;
  file_name: string;
  content_type: string;
  sha256: string;
};

export type CockpitSummary = {
  module_id: "home";
  title: string;
  status: "ready" | "needs_context";
  description: string;
  active_context: Record<string, unknown>;
  setup_status: SetupStatus | null;
  counts: {
    recent_jobs: number;
    recent_artifacts: number;
    recent_evidence: number;
  };
  module_summary: {
    total: number;
    counts_by_status: Record<string, number>;
    items: NavigationItem[];
  };
  recent_jobs: CockpitJob[];
  recent_artifacts: CockpitArtifact[];
  recent_evidence: CockpitEvidence[];
  available_actions: AvailableAction[];
};
