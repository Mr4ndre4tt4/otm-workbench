import type { PageResponse } from "./shared";

export type OrderReleaseTemplate = {
  id: string;
  code: string;
  name: string;
  version: number;
  status: string;
  macro_object_code: string;
  description: string;
  required_columns: string[];
  optional_columns: string[];
  defaults: Record<string, unknown>;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type OrderReleaseTemplatesResponse = PageResponse<OrderReleaseTemplate>;
