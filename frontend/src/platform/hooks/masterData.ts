import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../api";
import type { MasterDataTemplate, MasterDataTemplatesResponse } from "../types";

export function useMasterDataTemplates(token: string | null) {
  return useQuery({
    queryKey: ["modules", "master-data", "templates"],
    queryFn: () => apiGet<MasterDataTemplatesResponse>("/api/v1/modules/master-data/templates", { token }),
    enabled: Boolean(token)
  });
}

export function useMasterDataTemplateDetail(token: string | null, templateCode: string | null) {
  return useQuery({
    queryKey: ["modules", "master-data", "templates", templateCode],
    queryFn: () => apiGet<MasterDataTemplate>(`/api/v1/modules/master-data/templates/${templateCode}`, { token }),
    enabled: Boolean(token && templateCode)
  });
}
