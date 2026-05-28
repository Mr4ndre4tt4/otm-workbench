import { useQuery } from "@tanstack/react-query";

import { apiGet, apiPost } from "../api";
import type {
  AssistantHealth,
  AssistantOracleLookupRequest,
  AssistantSearchResult,
  AssistantSqlDraft,
  AssistantSqlExplainRequest,
  AssistantSqlDraftRequest,
  PageResponse
} from "../types";

export function useAssistantHealth(token: string | null, enabled = true) {
  return useQuery({
    queryKey: ["assistant", "health"],
    queryFn: () => apiGet<AssistantHealth>("/api/v1/assistant/health", { token }),
    enabled: Boolean(token && enabled)
  });
}

export function useAssistantSearch(token: string | null, query: string, enabled: boolean) {
  const params = new URLSearchParams();
  params.set("query", query);
  params.set("limit", "5");
  return useQuery({
    queryKey: ["assistant", "search", query],
    queryFn: () => apiGet<PageResponse<AssistantSearchResult>>(`/api/v1/assistant/search?${params}`, { token }),
    enabled: Boolean(token && enabled && query.trim())
  });
}

export function prepareOracleLookup(token: string, query: string, privateTerms: string[]) {
  return apiPost<AssistantOracleLookupRequest>(
    "/api/v1/assistant/oracle-docs/live-lookup",
    { query, private_terms: privateTerms },
    { token }
  );
}

export function draftAssistantSql(token: string, payload: AssistantSqlDraftRequest) {
  return apiPost<AssistantSqlDraft>("/api/v1/assistant/sql/draft", payload, { token });
}

export function explainAssistantSql(token: string, payload: AssistantSqlExplainRequest) {
  return apiPost<AssistantSqlDraft>("/api/v1/assistant/sql/explain", payload, { token });
}
