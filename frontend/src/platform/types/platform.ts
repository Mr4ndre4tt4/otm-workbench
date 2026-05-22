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

export type UserPreferences = {
  theme_mode: "light" | "dark" | "system";
  follow_system_theme: boolean;
  density: "comfortable" | "compact";
  sidebar_mode: "expanded" | "collapsed";
};
