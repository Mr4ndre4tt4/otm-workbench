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
