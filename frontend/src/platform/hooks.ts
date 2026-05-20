import { useQuery } from "@tanstack/react-query";

import { apiGet } from "./api";
import type { CockpitSummary, NavigationResponse, UserPreferences } from "./types";

export function useNavigation() {
  return useQuery({
    queryKey: ["platform", "navigation"],
    queryFn: () => apiGet<NavigationResponse>("/api/v1/platform/navigation")
  });
}

export function useCockpitSummary() {
  return useQuery({
    queryKey: ["platform", "project-cockpit", "summary"],
    queryFn: () => apiGet<CockpitSummary>("/api/v1/platform/project-cockpit/summary")
  });
}

export function useUserPreferences() {
  return useQuery({
    queryKey: ["platform", "user-preferences"],
    queryFn: () => apiGet<UserPreferences>("/api/v1/platform/user-preferences")
  });
}
