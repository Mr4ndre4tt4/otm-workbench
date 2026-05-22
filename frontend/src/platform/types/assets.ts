import type { PageResponse } from "./shared";

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
  tags: string[];
  current_version_id: string | null;
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
  tags: string[];
};

export type AssetLinkCreateRequest = {
  link_type: string;
  target_id: string;
  target_label: string;
};

export type AssetsResponse = PageResponse<AssetItem>;
export type AssetVersionsResponse = PageResponse<AssetVersion>;
export type AssetLinksResponse = PageResponse<AssetLink>;
