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
