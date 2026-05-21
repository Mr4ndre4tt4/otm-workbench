import type { PageResponse } from "./shared";

export type IntegrationDefinition = {
  id: string;
  code: string;
  name: string;
  description: string;
  source_system: string;
  target_system: string;
  source_format: string;
  target_format: string;
  status: string;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationTransformType = {
  id: string;
  code: string;
  name: string;
  description: string;
  requires_expression: boolean;
  status: string;
  sequence_index: number;
  system_seeded: boolean;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationPayloadArtifact = {
  id: string;
  definition_id: string;
  artifact_id: string;
  payload_role: string;
  payload_format: string;
  file_name: string;
  description: string;
  content_type: string;
  sha256: string;
  size_bytes: number;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationSchemaDocument = {
  id: string;
  definition_id: string;
  payload_artifact_id: string | null;
  payload_format: string;
  root_name: string;
  node_count: number;
  status: string;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationMapping = {
  id: string;
  definition_id: string;
  source_schema_document_id: string | null;
  target_schema_document_id: string | null;
  source_path: string;
  target_path: string;
  transform_type: string;
  description: string;
  sequence_index: number;
  status: string;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationDefinitionsResponse = PageResponse<IntegrationDefinition>;
export type IntegrationTransformTypesResponse = PageResponse<IntegrationTransformType>;
export type IntegrationPayloadArtifactsResponse = PageResponse<IntegrationPayloadArtifact>;
export type IntegrationSchemaDocumentsResponse = PageResponse<IntegrationSchemaDocument>;
export type IntegrationMappingsResponse = PageResponse<IntegrationMapping>;
