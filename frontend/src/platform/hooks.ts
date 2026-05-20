import { useQuery } from "@tanstack/react-query";

import { apiGet, apiPost } from "./api";
import type { CockpitSummary, LoginResponse, NavigationResponse, UserPreferences } from "./types";

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

export function useCockpitSummary(token: string | null) {
  return useQuery({
    queryKey: ["platform", "project-cockpit", "summary"],
    queryFn: () => apiGet<CockpitSummary>("/api/v1/platform/project-cockpit/summary", { token }),
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
