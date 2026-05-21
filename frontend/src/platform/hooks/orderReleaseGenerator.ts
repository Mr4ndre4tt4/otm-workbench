import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../api";
import type { OrderReleaseTemplatesResponse } from "../types";

export function useOrderReleaseTemplates(token: string | null) {
  return useQuery({
    queryKey: ["modules", "order-release-generator", "templates"],
    queryFn: () => apiGet<OrderReleaseTemplatesResponse>("/api/v1/modules/order-release-generator/templates", { token }),
    enabled: Boolean(token)
  });
}
