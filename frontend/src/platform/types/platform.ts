import type { PageResponse } from "./shared";

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

export type UserPreferences = {
  theme_mode: "light" | "dark" | "system";
  follow_system_theme: boolean;
  density: "comfortable" | "compact";
  sidebar_mode: "expanded" | "collapsed";
};
