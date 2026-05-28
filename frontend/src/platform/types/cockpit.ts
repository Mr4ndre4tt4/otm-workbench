import type { AvailableAction } from "./shared";
import type { NavigationItem } from "./platform";

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

export type CockpitContextSelector = {
  mode: "PRIVATE" | "PUBLIC";
  active_context: Record<string, unknown>;
  public_view_available: boolean;
  requires_private_context: boolean;
  set_context_action_key: string;
};

export type CockpitProjectInfo = {
  title: string;
  status: string;
  links: { href: string; label: string }[];
  documents: { href: string; label: string }[];
  contacts: { label: string; value: string }[];
  secure_vault: {
    status: string;
    metadata_only: boolean;
    secret_values_available: boolean;
  };
};

export type CockpitAccelerator = {
  key: string;
  label: string;
  description: string;
  href: string;
  status: string;
  icon_key: string;
  requires_private_context: boolean;
  disabled: boolean;
  disabled_reason: string | null;
};

export type CockpitUserScope = {
  role_mode: string;
  is_dba: boolean;
  allowed_domains: string[];
  can_view_all_domains: boolean;
};

export type CockpitRouteRecovery = {
  default_path: string;
  return_action_key: string;
  blocked_route_message: string;
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
  context_selector: CockpitContextSelector;
  project_info: CockpitProjectInfo;
  accelerators: CockpitAccelerator[];
  user_scope: CockpitUserScope;
  route_recovery: CockpitRouteRecovery;
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
