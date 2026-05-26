import type { PageResponse } from "./shared";

export type NavigationItem = {
  id: string;
  label: string;
  label_key: string;
  description: string;
  path: string;
  status: string;
  icon_key: string;
  icon_family: string;
  icon_variant: string;
  icon_style: string;
  icon_name: string;
  icon_light_ref: Record<string, unknown>;
  icon_dark_ref: Record<string, unknown>;
};

export type NavigationResponse = PageResponse<NavigationItem>;

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
};

export type CurrentUser = {
  id: string;
  email: string;
  is_admin: boolean;
};

export type IdName = {
  id: string;
  name: string;
};

export type IdNameResponse = PageResponse<IdName>;

export type WorkspaceCreate = {
  name: string;
};

export type ProjectCreate = {
  workspace_id: string;
  name: string;
};

export type ProfileCreate = {
  project_id: string;
  name: string;
};

export type EnvironmentCreate = {
  project_id: string;
  name: string;
  environment_type: string;
};

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

export type ProjectSetupStatus = {
  project_id: string;
  project_name: string;
  status: string;
  profile_count: number;
  environment_count: number;
  active_context_selected: boolean;
  missing_requirements: string[];
};

export type EffectiveCapabilities = {
  user_id: string;
  project_id: string | null;
  is_admin: boolean;
  roles: string[];
  capabilities: string[];
};

export type PlatformJobError = {
  code: string | null;
  details: Record<string, unknown>;
  message: string | null;
};

export type PlatformJob = {
  id: string;
  job_type: string;
  source_module: string;
  project_id: string | null;
  profile_id: string | null;
  environment_id: string | null;
  domain_name: string | null;
  status: string;
  progress: number;
  message: string;
  input: Record<string, unknown>;
  result: Record<string, unknown>;
  error: PlatformJobError | null;
  created_by: string | null;
  created_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  cancelled_at: string | null;
};

export type PlatformJobEvent = {
  id: string;
  job_id: string;
  event_type: string;
  status_before: string | null;
  status_after: string | null;
  message: string;
  payload: Record<string, unknown>;
  created_by: string | null;
  created_at: string | null;
};

export type PlatformJobCreate = {
  job_type: string;
  source_module: string;
  project_id?: string | null;
  profile_id?: string | null;
  environment_id?: string | null;
  domain_name?: string | null;
  input?: Record<string, unknown>;
  execute_now?: boolean;
};

export type AuditLogItem = {
  id: string;
  action: string;
  target_type: string;
  target_id: string;
};

export type FeatureFlag = {
  id: string;
  name: string;
  enabled: boolean;
  scope: string;
};

export type FeatureFlagUpdate = {
  name: string;
  enabled: boolean;
  scope: string;
};

export type DevToolsGuard = {
  key: string;
  label: string;
  status: string;
  message: string;
};

export type DevToolsTool = {
  key: string;
  label: string;
  status: string;
  href: string | null;
  required_capability: string;
  disabled_reason: string | null;
};

export type DevToolsRun = {
  id: string;
  job_type: string;
  source_module: string;
  project_id: string | null;
  profile_id: string | null;
  environment_id: string | null;
  domain_name: string | null;
  status: string;
  progress: number;
  message: string;
  input_present: boolean;
  result_present: boolean;
  created_at: string | null;
  finished_at: string | null;
};

export type DevToolsSummary = {
  module_id: string;
  title: string;
  status: string;
  description: string;
  active_context: ActiveContextResponse;
  guards: DevToolsGuard[];
  counts: {
    available_tools: number;
    disabled_tools: number;
    recent_runs: number;
  };
  tools: DevToolsTool[];
  recent_runs: DevToolsRun[];
};

export type DevToolsDataDictionaryTable = {
  table_name: string;
  schema_name: string;
  description: string;
  column_count: number;
  data_category: string;
  is_transactional: boolean;
  allow_cutover: boolean;
  allow_csvutil: boolean;
};

export type DevToolsDataDictionaryResponse = {
  module_id: string;
  tool_key: string;
  title: string;
  status: string;
  description: string;
  query: string;
  limit: number;
  total: number;
  source_contract: string;
  active_context: ActiveContextResponse;
  items: DevToolsDataDictionaryTable[];
};

export type DevToolsDataDictionaryTableDefinition = DevToolsDataDictionaryTable & {
  primary_key: string[];
  required_columns: string[];
  date_columns: string[];
  foreign_key_count: number;
  exists: boolean;
};

export type DevToolsDataDictionaryColumn = {
  column_name: string;
  data_type: string | null;
  nullable: boolean | null;
  is_primary_key?: boolean;
  is_required?: boolean;
};

export type DevToolsDataDictionaryTableDetailResponse = {
  module_id: string;
  tool_key: string;
  title: string;
  status: string;
  source_contract: string;
  active_context: ActiveContextResponse;
  table: DevToolsDataDictionaryTableDefinition;
  columns: DevToolsDataDictionaryColumn[];
  column_total: number;
};

export type DevToolsFkCatalogRelationship = {
  source_table_name: string;
  column_name: string;
  parent_table_name: string;
  parent_column_name: string;
  relationship_type: string;
  parent_table_href: string;
};

export type DevToolsFkCatalogResponse = {
  module_id: string;
  tool_key: string;
  title: string;
  status: string;
  description: string;
  source_table: string;
  limit: number;
  total: number;
  source_contract: string;
  active_context: ActiveContextResponse;
  items: DevToolsFkCatalogRelationship[];
};

export type DevToolsSchemaPackRoot = {
  id: string;
  schema_pack_id: string;
  schema_file_id: string;
  root_name: string;
  root_display_label: string;
  canonical_root_name: string;
  schema_root_aliases: string[];
  data_dictionary_family: string;
  schema_guidance_role: string;
  namespace: string;
  domain_area: string;
  root_type: string;
  envelope_role: string;
  recommended_modules: string[];
  documentation: string;
};

export type DevToolsSchemaPack = {
  id: string;
  code: string;
  name: string;
  otm_version: string;
  source_type: string;
  asset_id: string | null;
  status: string;
  namespace_count: number;
  root_count: number;
  operation_count: number;
  content_hash: string;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
  root_total: number;
  root_preview: DevToolsSchemaPackRoot[];
};

export type DevToolsSchemaPacksResponse = {
  module_id: string;
  tool_key: string;
  title: string;
  status: string;
  description: string;
  otm_version: string;
  code: string;
  filter_status: string;
  limit: number;
  total: number;
  source_contract: string;
  root_contract: string;
  active_context: ActiveContextResponse;
  items: DevToolsSchemaPack[];
};

export type DevToolsEnvironmentReadinessEnvironment = {
  id: string;
  name: string;
  environment_type: string;
  status: string;
  is_active: boolean;
};

export type DevToolsEnvironmentReadinessCheck = {
  key: string;
  label: string;
  status: string;
  message: string;
};

export type DevToolsEnvironmentReadinessResponse = {
  module_id: string;
  tool_key: string;
  title: string;
  status: string;
  description: string;
  active_context: ActiveContextResponse;
  active_environment_id: string | null;
  counts: {
    environments: number;
    ready_checks: number;
    blocked_checks: number;
  };
  environments: DevToolsEnvironmentReadinessEnvironment[];
  checks: DevToolsEnvironmentReadinessCheck[];
  source_contract: string;
};

export type UserPreferences = {
  theme_mode: "light" | "dark" | "system";
  follow_system_theme: boolean;
  density: "comfortable" | "compact";
  sidebar_mode: "expanded" | "collapsed";
};
