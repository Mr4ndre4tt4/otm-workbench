import type { PageResponse } from "./shared";
import type { AvailableAction } from "./shared";

export type AssetItem = {
  id: string;
  project_id: string | null;
  profile_id: string | null;
  environment_id: string | null;
  name: string;
  description: string;
  asset_type: string;
  category: string;
  visibility: string;
  scope_type: string;
  sensitivity: string;
  status: string;
  module_id: string | null;
  macro_object_code: string | null;
  otm_table_name: string | null;
  target_otm_version: string | null;
  tags: string[];
  current_version_id: string | null;
  available_actions?: AvailableAction[];
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type AssetVersion = {
  id: string;
  asset_id: string;
  version_number: number;
  status: string;
  file_name: string;
  content_type: string;
  sha256: string;
  size_bytes: number;
  uploaded_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type AssetLink = {
  id: string;
  asset_id: string;
  link_type: string;
  target_id: string;
  target_label: string;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type AssetCreateRequest = {
  name: string;
  description: string;
  asset_type: string;
  category: string;
  visibility: string;
  scope_type: string;
  sensitivity: string;
  module_id?: string | null;
  macro_object_code?: string | null;
  otm_table_name?: string | null;
  target_otm_version?: string | null;
  tags: string[];
};

export type AssetUpdateRequest = Partial<AssetCreateRequest>;

export type AssetLinkCreateRequest = {
  link_type: string;
  target_id: string;
  target_label: string;
};

export type AssetClassificationCreateRequest = {
  classification_type: string;
  code: string;
  name: string;
  description: string;
  sort_order: number;
};

export type AssetClassificationUpdateRequest = Partial<{
  name: string;
  description: string;
  sort_order: number;
  is_active: boolean;
}>;

export type AssetFilters = {
  asset_id?: string;
  asset_id_operator?: string;
  name?: string;
  name_operator?: string;
  description?: string;
  description_operator?: string;
  asset_type?: string;
  category?: string;
  status?: string;
  visibility?: string;
  sensitivity?: string;
  scope_type?: string;
  tag?: string;
  module_id?: string;
  module_id_operator?: string;
  macro_object_code?: string;
  macro_object_code_operator?: string;
  otm_table_name?: string;
  otm_table_name_operator?: string;
  target_otm_version?: string;
  target_otm_version_operator?: string;
  linked_target_type?: string;
  linked_target_type_operator?: string;
  has_current_version?: string;
  page?: string;
  page_size?: string;
};

export type AssetClassification = {
  id: string;
  classification_type: string;
  code: string;
  name: string;
  description: string;
  sort_order: number;
  system_protected: boolean;
  is_active: boolean;
};

export type AssetClassificationGroup = {
  classification_type: string;
  items: AssetClassification[];
  total: number;
};

export type AssetsResponse = PageResponse<AssetItem>;
export type AssetVersionsResponse = PageResponse<AssetVersion>;
export type AssetLinksResponse = PageResponse<AssetLink>;
export type AssetClassificationsResponse = PageResponse<AssetClassificationGroup>;
