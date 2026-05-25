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

export type IntegrationSchemaNode = {
  id: string;
  schema_document_id: string;
  parent_path: string | null;
  path: string;
  name: string;
  node_type: string;
  sequence_index: number;
};

export type IntegrationMapping = {
  id: string;
  definition_id: string;
  source_schema_document_id: string | null;
  target_schema_document_id: string | null;
  source_path: string;
  target_path: string;
  transform_type: string;
  transform_config: Record<string, unknown>;
  description: string;
  sequence_index: number;
  status: string;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationLoopDefinition = {
  id: string;
  definition_id: string;
  source_schema_document_id: string;
  target_schema_document_id: string;
  source_collection_path: string;
  target_collection_path: string;
  name: string;
  description: string;
  sequence_index: number;
  status: string;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationJoinRule = {
  id: string;
  definition_id: string;
  source_schema_document_id: string;
  left_path: string;
  right_path: string;
  operator: string;
  name: string;
  description: string;
  sequence_index: number;
  status: string;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationJoinBindingHop = {
  id?: string;
  binding_id?: string;
  hop_sequence: number;
  left_collection_path: string;
  left_value_path: string;
  right_collection_path: string;
  right_value_path: string;
  operator: string;
  result_alias: string;
  status?: string;
};

export type IntegrationJoinBinding = {
  id: string;
  definition_id: string;
  source_schema_document_id: string;
  root_collection_path: string;
  target_collection_path: string;
  name: string;
  description: string;
  sequence_index: number;
  status: string;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
  hops: IntegrationJoinBindingHop[];
};

export type IntegrationLookupDefinition = {
  id: string;
  definition_id: string;
  source_schema_document_id: string;
  target_schema_document_id: string;
  input_path: string;
  output_path: string;
  lookup_type: string;
  name: string;
  description: string;
  mock_response_json: string;
  sequence_index: number;
  status: string;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationArtifact = {
  id: string;
  definition_id: string;
  source_module: string;
  artifact_type: string;
  file_name: string;
  content_type: string;
  sha256: string;
  size_bytes: number;
  sensitivity_level: string;
  download_url?: string;
};

export type IntegrationSystem = {
  id: string;
  code: string;
  name: string;
  description: string;
  system_type: string;
  base_url: string;
  status: string;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationEndpoint = {
  id: string;
  system_id: string;
  code: string;
  name: string;
  description: string;
  path: string;
  method: string;
  payload_format: string;
  status: string;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type IntegrationSystemCreatePayload = {
  code: string;
  name: string;
  system_type: string;
  base_url: string;
  description: string;
};

export type IntegrationEndpointCreatePayload = {
  code: string;
  name: string;
  path: string;
  method: string;
  payload_format: string;
  description: string;
};

export type IntegrationDefinitionCreatePayload = {
  code: string;
  name: string;
  description: string;
  source_system: string;
  target_system: string;
  source_format: string;
  target_format: string;
};

export type IntegrationPayloadArtifactCreatePayload = {
  payload_role: string;
  payload_format: string;
  file_name: string;
  content: string;
  description: string;
};

export type IntegrationMappingCreatePayload = {
  source_schema_document_id: string;
  target_schema_document_id: string;
  source_path: string;
  target_path: string;
  transform_type: string;
  transform_config?: Record<string, unknown>;
  description: string;
  sequence_index: number;
};

export type IntegrationLoopCreatePayload = {
  source_schema_document_id: string;
  target_schema_document_id: string;
  source_collection_path: string;
  target_collection_path: string;
  name: string;
  description: string;
  sequence_index: number;
};

export type IntegrationJoinCreatePayload = {
  source_schema_document_id: string;
  left_path: string;
  right_path: string;
  operator: string;
  name: string;
  description: string;
  sequence_index: number;
};

export type IntegrationJoinBindingCreatePayload = {
  source_schema_document_id: string;
  root_collection_path: string;
  target_collection_path: string;
  name: string;
  description: string;
  sequence_index: number;
  hops: Array<{
    hop_sequence: number;
    left_collection_path: string;
    left_value_path: string;
    right_collection_path: string;
    right_value_path: string;
    operator: string;
    result_alias: string;
  }>;
};

export type IntegrationLookupCreatePayload = {
  source_schema_document_id: string;
  target_schema_document_id: string;
  input_path: string;
  output_path: string;
  lookup_type: string;
  name: string;
  description: string;
  mock_response_json: string;
  sequence_index: number;
};

export type IntegrationValidationResult = {
  is_valid: boolean;
  issue_count: number;
  issues?: unknown[];
  readiness?: IntegrationValidationReadiness;
};

export type IntegrationValidationReadiness = {
  specification_ready: boolean;
  preview_executable: boolean;
  specification_blockers: string[];
  preview_blockers: string[];
};

export type IntegrationPreviewResult = {
  artifact_id: string;
  job_id: string;
  validation: IntegrationValidationResult;
  preview?: Record<string, unknown>;
};

export type IntegrationSpecResult = {
  artifact_id: string;
  job_id: string;
  validation?: IntegrationValidationResult;
};

export type IntegrationDefinitionsResponse = PageResponse<IntegrationDefinition>;
export type IntegrationSystemsResponse = PageResponse<IntegrationSystem>;
export type IntegrationEndpointsResponse = PageResponse<IntegrationEndpoint>;
export type IntegrationTransformTypesResponse = PageResponse<IntegrationTransformType>;
export type IntegrationPayloadArtifactsResponse = PageResponse<IntegrationPayloadArtifact>;
export type IntegrationSchemaDocumentsResponse = PageResponse<IntegrationSchemaDocument>;
export type IntegrationSchemaNodesResponse = PageResponse<IntegrationSchemaNode>;
export type IntegrationMappingsResponse = PageResponse<IntegrationMapping>;
export type IntegrationLoopsResponse = PageResponse<IntegrationLoopDefinition>;
export type IntegrationJoinsResponse = PageResponse<IntegrationJoinRule>;
export type IntegrationJoinBindingsResponse = PageResponse<IntegrationJoinBinding>;
export type IntegrationLookupsResponse = PageResponse<IntegrationLookupDefinition>;
export type IntegrationArtifactsResponse = PageResponse<IntegrationArtifact> & {
  definition_id: string;
};
