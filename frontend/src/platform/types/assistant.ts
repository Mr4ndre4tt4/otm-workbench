export type AssistantHealth = {
  status: string;
  module: string;
  capabilities: string[];
};

export type AssistantSearchResult = {
  source_id: string;
  source_title: string;
  source_type: string;
  source_uri: string;
  module_id: string | null;
  domain_name: string | null;
  visibility: string;
  chunk_id: string;
  snippet: string;
  rank: number;
};

export type AssistantOracleLookupAction = {
  label: string;
  url: string;
  source_domain: string;
};

export type AssistantOracleLookupRequest = {
  answer_type: "lookup_request";
  summary: string;
  confidence: string;
  source_mode: string;
  cost_level: string;
  network_performed: boolean;
  sanitized_query: string;
  actions: AssistantOracleLookupAction[];
  warnings: string[];
};

export type AssistantSqlDraftRequest = {
  table_name: string;
  columns: string[];
  filter_column: string;
  purpose: string;
};

export type AssistantSqlExplainRequest = {
  sql_text: string;
};

export type AssistantSqlDraftBlock = {
  type: "sql_draft";
  purpose: string;
  sql: string;
  parameters: Array<{
    name: string;
    description: string;
  }>;
  tables: string[];
  columns: string[];
  assumptions: string[];
  warnings: string[];
};

export type AssistantSqlDraft = {
  answer_type: "sql_draft" | "blocked";
  summary: string;
  confidence: string;
  source_mode: string;
  cost_level: string;
  block?: AssistantSqlDraftBlock;
  warnings?: string[];
  sources?: string[];
};
