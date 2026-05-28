import { useQuery } from "@tanstack/react-query";

import { apiDownload, apiGet, apiPost, apiPut } from "../api";
import type {
  AccessPolicyCreate,
  ActiveContextResponse,
  ActiveContextUpdate,
  AuditLogItem,
  CockpitSummary,
  CurrentUser,
  DevToolsDataDictionaryResponse,
  DevToolsDataDictionaryTableDetailResponse,
  DevToolsEnvironmentReadinessResponse,
  DevToolsFkCatalogResponse,
  DevToolsSchemaPacksResponse,
  DevToolsSummary,
  EffectiveCapabilities,
  EnvironmentCreate,
  FeatureFlag,
  FeatureFlagUpdate,
  GrantCreate,
  IdName,
  IdNameResponse,
  LoginResponse,
  NavigationResponse,
  PageResponse,
  PlatformJob,
  PlatformJobCreate,
  ProfileCreate,
  ProjectCreate,
  PlatformJobEvent,
  ProjectSetupStatus,
  RoleCreate,
  SettingsAccessModel,
  SettingsAccessPolicy,
  SettingsGrant,
  SettingsRole,
  SettingsScopeAuthority,
  SettingsUser,
  UserCreate,
  WorkspaceCreate,
  UserPreferences
} from "../types";

export function login(email: string, password: string) {
  return apiPost<LoginResponse>("/api/v1/platform/session/login", { email, password });
}

export function useNavigation(token: string | null) {
  return useQuery({
    queryKey: ["platform", "navigation"],
    queryFn: () => apiGet<NavigationResponse>("/api/v1/platform/navigation", { token }),
    enabled: Boolean(token)
  });
}

export function useCurrentUser(token: string | null) {
  return useQuery({
    queryKey: ["platform", "session", "me"],
    queryFn: () => apiGet<CurrentUser>("/api/v1/platform/session/me", { token }),
    enabled: Boolean(token)
  });
}

export function useProjects(token: string | null) {
  return useQuery({
    queryKey: ["platform", "projects"],
    queryFn: () => apiGet<IdNameResponse>("/api/v1/platform/projects", { token }),
    enabled: Boolean(token)
  });
}

export function useWorkspaces(token: string | null) {
  return useQuery({
    queryKey: ["platform", "workspaces"],
    queryFn: () => apiGet<IdName[]>("/api/v1/platform/workspaces", { token }),
    enabled: Boolean(token)
  });
}

export function createWorkspace(token: string, payload: WorkspaceCreate) {
  return apiPost<IdName>("/api/v1/platform/workspaces", payload, { token });
}

export function createProject(token: string, payload: ProjectCreate) {
  return apiPost<IdName>("/api/v1/platform/projects", payload, { token });
}

export function createProfile(token: string, payload: ProfileCreate) {
  return apiPost<IdName>("/api/v1/platform/profiles", payload, { token });
}

export function createEnvironment(token: string, payload: EnvironmentCreate) {
  return apiPost<IdName>("/api/v1/platform/environments", payload, { token });
}

export function useProjectSetupStatus(token: string | null, projectId: string | null) {
  return useQuery({
    queryKey: ["platform", "projects", projectId, "setup-status"],
    queryFn: () => apiGet<ProjectSetupStatus>(`/api/v1/platform/projects/${projectId}/setup-status`, { token }),
    enabled: Boolean(token && projectId)
  });
}

export function useSettingsScopeAuthority(token: string | null) {
  return useQuery({
    queryKey: ["platform", "settings", "scope-authority"],
    queryFn: () => apiGet<SettingsScopeAuthority>("/api/v1/platform/settings/scope-authority", { token }),
    enabled: Boolean(token)
  });
}

export function useSettingsAccessModel(token: string | null) {
  return useQuery({
    queryKey: ["platform", "settings", "access-model"],
    queryFn: () => apiGet<SettingsAccessModel>("/api/v1/platform/settings/access-model", { token }),
    enabled: Boolean(token)
  });
}

export function createRole(token: string, payload: RoleCreate) {
  return apiPost<SettingsRole>("/api/v1/platform/roles", payload, { token });
}

export function createUser(token: string, payload: UserCreate) {
  return apiPost<SettingsUser>("/api/v1/platform/users", payload, { token });
}

export function createGrant(token: string, payload: GrantCreate) {
  return apiPost<SettingsGrant>("/api/v1/platform/grants", payload, { token });
}

export function createAccessPolicy(token: string, payload: AccessPolicyCreate) {
  return apiPost<SettingsAccessPolicy>("/api/v1/platform/access-policies", payload, { token });
}

export function useActiveContextCapabilities(token: string | null) {
  return useQuery({
    queryKey: ["platform", "active-context", "capabilities"],
    queryFn: () => apiGet<EffectiveCapabilities>("/api/v1/platform/active-context/capabilities", { token }),
    enabled: Boolean(token)
  });
}

export function usePlatformJobs(token: string | null) {
  return useQuery({
    queryKey: ["platform", "jobs"],
    queryFn: () => apiGet<PageResponse<PlatformJob>>("/api/v1/platform/jobs", { token }),
    enabled: Boolean(token)
  });
}

export function usePlatformJobEvents(token: string | null, jobId: string | null) {
  return useQuery({
    queryKey: ["platform", "jobs", jobId, "events"],
    queryFn: () => apiGet<PageResponse<PlatformJobEvent>>(`/api/v1/platform/jobs/${jobId}/events`, { token }),
    enabled: Boolean(token && jobId)
  });
}

export function createPlatformJob(token: string, payload: PlatformJobCreate) {
  return apiPost<PlatformJob>("/api/v1/platform/jobs", payload, { token });
}

export function runPlatformJob(token: string, jobId: string) {
  return apiPost<PlatformJob>(`/api/v1/platform/jobs/${jobId}/run`, {}, { token });
}

export function cancelPlatformJob(token: string, jobId: string) {
  return apiPost<PlatformJob>(`/api/v1/platform/jobs/${jobId}/cancel`, {}, { token });
}

export function useAuditLogs(token: string | null) {
  return useQuery({
    queryKey: ["platform", "audit-logs"],
    queryFn: () => apiGet<PageResponse<AuditLogItem>>("/api/v1/platform/audit-logs", { token }),
    enabled: Boolean(token)
  });
}

export function useFeatureFlags(token: string | null) {
  return useQuery({
    queryKey: ["platform", "feature-flags"],
    queryFn: () => apiGet<PageResponse<FeatureFlag>>("/api/v1/platform/feature-flags", { token }),
    enabled: Boolean(token)
  });
}

export function upsertFeatureFlag(token: string, payload: FeatureFlagUpdate) {
  return apiPost<FeatureFlag>("/api/v1/platform/feature-flags", payload, { token });
}

export function useProfiles(token: string | null, projectId: string | null) {
  return useQuery({
    queryKey: ["platform", "profiles", projectId],
    queryFn: () => apiGet<IdNameResponse>(`/api/v1/platform/profiles?project_id=${projectId}`, { token }),
    enabled: Boolean(token && projectId)
  });
}

export function useEnvironments(token: string | null, projectId: string | null) {
  return useQuery({
    queryKey: ["platform", "environments", projectId],
    queryFn: () => apiGet<IdNameResponse>(`/api/v1/platform/environments?project_id=${projectId}`, { token }),
    enabled: Boolean(token && projectId)
  });
}

export function updateActiveContext(token: string, payload: ActiveContextUpdate) {
  return apiPost<ActiveContextResponse>("/api/v1/platform/active-context", payload, { token });
}

export function executeBackendAction<T = Record<string, unknown>>(token: string, href: string) {
  return apiPost<T>(href, {}, { token });
}

export function downloadBackendArtifact(token: string, href: string) {
  return apiDownload(href, { token });
}

export function useCockpitSummary(token: string | null) {
  return useQuery({
    queryKey: ["platform", "project-cockpit", "summary"],
    queryFn: () => apiGet<CockpitSummary>("/api/v1/platform/project-cockpit/summary", { token }),
    enabled: Boolean(token)
  });
}

export function useDevToolsSummary(token: string | null) {
  return useQuery({
    queryKey: ["platform", "dev-tools", "summary"],
    queryFn: () => apiGet<DevToolsSummary>("/api/v1/platform/dev-tools/summary", { token }),
    enabled: Boolean(token)
  });
}

export function useDevToolsDataDictionary(token: string | null, query: string, limit = 25) {
  const params = new URLSearchParams();
  params.set("query", query);
  params.set("limit", String(limit));
  return useQuery({
    queryKey: ["platform", "dev-tools", "data-dictionary", query, limit],
    queryFn: () => apiGet<DevToolsDataDictionaryResponse>(`/api/v1/platform/dev-tools/data-dictionary?${params}`, { token }),
    enabled: Boolean(token)
  });
}

export function useDevToolsDataDictionaryTable(token: string | null, tableName: string | undefined) {
  return useQuery({
    queryKey: ["platform", "dev-tools", "data-dictionary", "tables", tableName],
    queryFn: () =>
      apiGet<DevToolsDataDictionaryTableDetailResponse>(`/api/v1/platform/dev-tools/data-dictionary/tables/${tableName}`, {
        token
      }),
    enabled: Boolean(token && tableName)
  });
}

export function useDevToolsFkCatalog(token: string | null, sourceTable: string, limit = 50) {
  const params = new URLSearchParams();
  params.set("source_table", sourceTable);
  params.set("limit", String(limit));
  return useQuery({
    queryKey: ["platform", "dev-tools", "fk-catalog", sourceTable, limit],
    queryFn: () => apiGet<DevToolsFkCatalogResponse>(`/api/v1/platform/dev-tools/fk-catalog?${params}`, { token }),
    enabled: Boolean(token && sourceTable)
  });
}

export function useDevToolsSchemaPacks(token: string | null, otmVersion: string, code = "", limit = 25) {
  const params = new URLSearchParams();
  params.set("otm_version", otmVersion);
  if (code) {
    params.set("code", code);
  }
  params.set("limit", String(limit));
  return useQuery({
    queryKey: ["platform", "dev-tools", "schema-packs", otmVersion, code, limit],
    queryFn: () => apiGet<DevToolsSchemaPacksResponse>(`/api/v1/platform/dev-tools/schema-packs?${params}`, { token }),
    enabled: Boolean(token && otmVersion)
  });
}

export function useDevToolsEnvironmentReadiness(token: string | null) {
  return useQuery({
    queryKey: ["platform", "dev-tools", "environment-readiness"],
    queryFn: () => apiGet<DevToolsEnvironmentReadinessResponse>("/api/v1/platform/dev-tools/environment-readiness", { token }),
    enabled: Boolean(token)
  });
}

export function useUserPreferences(token: string | null) {
  return useQuery({
    queryKey: ["platform", "user-preferences"],
    queryFn: () => apiGet<UserPreferences>("/api/v1/platform/user-preferences", { token }),
    enabled: Boolean(token)
  });
}

export function updateUserPreferences(token: string, payload: UserPreferences) {
  return apiPut<UserPreferences>("/api/v1/platform/user-preferences", payload, { token });
}
