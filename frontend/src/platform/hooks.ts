import { useQuery } from "@tanstack/react-query";

import { apiGet, apiPost, apiPut } from "./api";
import type {
  ActiveContextResponse,
  ActiveContextUpdate,
  CockpitSummary,
  IdNameResponse,
  LoginResponse,
  NavigationResponse,
  RateBatchDetail,
  RatesSummary,
  UserPreferences
} from "./types";

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

export function useProjects(token: string | null) {
  return useQuery({
    queryKey: ["platform", "projects"],
    queryFn: () => apiGet<IdNameResponse>("/api/v1/platform/projects", { token }),
    enabled: Boolean(token)
  });
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

export function useCockpitSummary(token: string | null) {
  return useQuery({
    queryKey: ["platform", "project-cockpit", "summary"],
    queryFn: () => apiGet<CockpitSummary>("/api/v1/platform/project-cockpit/summary", { token }),
    enabled: Boolean(token)
  });
}

export function useRatesSummary(token: string | null) {
  return useQuery({
    queryKey: ["modules", "rates", "summary"],
    queryFn: () => apiGet<RatesSummary>("/api/v1/modules/rates/summary", { token }),
    enabled: Boolean(token)
  });
}

export function useRateBatchDetail(token: string | null, batchId: string | null) {
  return useQuery({
    queryKey: ["modules", "rates", "batches", batchId],
    queryFn: () => apiGet<RateBatchDetail>(`/api/v1/modules/rates/batches/${batchId}`, { token }),
    enabled: Boolean(token && batchId)
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
