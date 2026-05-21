import type { PageResponse } from "./shared";

export type MasterDataTemplateField = {
  name: string;
  label: string;
  target_column: string;
  required?: boolean;
};

export type MasterDataTemplateSheet = {
  code: string;
  name: string;
  target_table: string;
  fields: MasterDataTemplateField[];
};

export type MasterDataTemplate = {
  id: string;
  code: string;
  name: string;
  version: string;
  status: string;
  catalog_macro_object_code: string;
  data_category: string;
  target_tables: string[];
  sheets: MasterDataTemplateSheet[];
  description: string;
  created_at: string | null;
  updated_at: string | null;
};

export type MasterDataTemplatesResponse = PageResponse<MasterDataTemplate>;
