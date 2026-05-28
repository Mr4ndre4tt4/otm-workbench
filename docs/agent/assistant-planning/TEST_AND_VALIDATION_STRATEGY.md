# Workbench Assistant Test And Validation Strategy

## Purpose

The Workbench Assistant needs more than normal UI tests because it crosses
search, permissions, local indexing, SQL drafting, web lookup, and source
trust. This document defines the validation strategy for future implementation.

## Testing Principles

1. Test source access before testing answer wording.
2. Test SQL safety before testing SQL convenience.
3. Test local-only behavior before online behavior.
4. Test denied results for non-leakage, not only for absence.
5. Test each tool independently before testing full chat flow.
6. Keep all fixtures synthetic.

## Backend Test Areas

### Intent Routing

Coverage:

- Workbench help question routes to `workbench_help`;
- file/template question routes to `find_artifact`;
- SQL question routes to `sql_help`;
- Oracle documentation question routes to `oracle_docs`;
- ambiguous question requests clarification.

Expected tests:

```text
test_intent_routes_current_screen_help
test_intent_routes_template_search
test_intent_routes_sql_draft
test_intent_routes_oracle_docs
test_intent_returns_clarification_for_ambiguous_request
```

### Source Index

Coverage:

- indexes local Markdown/help source;
- chunks source content;
- writes FTS entries;
- updates source hash;
- reports index health;
- handles parser failure without aborting all indexing.

Expected tests:

```text
test_index_markdown_source_creates_chunks
test_index_search_ranks_current_module
test_index_rebuild_updates_source_hash
test_index_parser_failure_is_recorded
test_index_health_reports_source_counts
```

### Scope Guard

Coverage:

- same-domain results visible;
- cross-domain results hidden;
- cross-environment results hidden;
- Public View sees only public sources;
- denied results do not leak title, path, snippet, or client name.

Expected tests:

```text
test_assistant_search_filters_cross_domain_source
test_assistant_search_filters_cross_environment_source
test_public_view_hides_private_sources
test_denied_result_does_not_leak_metadata
test_dba_can_search_across_allowed_scopes_with_explicit_context
```

### Workbench Help Tool

Coverage:

- current route help;
- module help fallback;
- unknown route safe response;
- source citations present.

Expected tests:

```text
test_current_route_help_returns_steps_and_sources
test_module_help_fallback_when_route_help_missing
test_unknown_route_help_returns_safe_empty_state
```

### Finder Tool

Coverage:

- template search;
- workbook search;
- saved query search;
- artifact/evidence search;
- archived/retired hidden by default.

Expected tests:

```text
test_finder_returns_current_template_in_scope
test_finder_ranks_current_environment_first
test_finder_hides_archived_sources_by_default
test_finder_can_filter_source_type
```

### SQL Helper

Coverage:

- exact table lookup;
- fuzzy table lookup;
- ambiguous table family;
- unknown table;
- known and unknown column;
- approved query pattern;
- join pattern;
- unsafe mutation rejection;
- pasted SQL explanation.

Expected tests:

```text
test_sql_helper_resolves_exact_table
test_sql_helper_asks_for_ambiguous_shipment_family
test_sql_helper_rejects_unknown_column_in_draft
test_sql_helper_uses_approved_join_pattern
test_sql_helper_rejects_update_delete_insert
test_sql_helper_explains_pasted_select_and_flags_unknowns
```

### Oracle Docs Connector

Coverage:

- official domain allowlist;
- cache hit;
- cache miss;
- expired cache;
- no official result;
- network failure.

Expected tests:

```text
test_oracle_docs_uses_cached_result_when_fresh
test_oracle_docs_fetches_and_caches_official_result
test_oracle_docs_marks_expired_cache
test_oracle_docs_refuses_unofficial_source_as_authority
test_oracle_docs_network_failure_returns_local_limited_state
```

## Frontend Test Areas

### Launcher And Panel

Coverage:

- launcher renders on authenticated Workbench routes;
- launcher has accessible name;
- click opens panel;
- Escape closes panel;
- focus returns to launcher;
- panel shows current context.

Expected tests:

```text
renders assistant launcher with accessible name
opens assistant panel from launcher
closes assistant panel with escape
shows current module and environment in context strip
```

### Quick Actions

Coverage:

- global quick actions render;
- module-specific quick actions render;
- quick action submits structured request;
- unavailable actions show disabled reason.

### Result Rendering

Coverage:

- help answer;
- finder cards;
- SQL draft block;
- Oracle docs link;
- blocked state;
- offline state;
- clarification state.

## Browser QA Scenarios

Browser QA should only happen after the runtime freshness gate passes.

Core scenarios:

1. Open assistant from Cockpit and ask for current screen help.
2. Open assistant from Master Data and find a synthetic template.
3. Open assistant from Rates and draft a safe SQL query.
4. Open assistant from Assets and verify private result suppression.
5. Trigger Oracle Docs lookup with mocked or controlled official result.
6. Simulate offline Oracle lookup and verify local-only state.
7. Verify the launcher does not cover module primary actions at desktop width.
8. Verify narrow viewport panel behavior.

## Synthetic Fixtures

Required fixture families:

- synthetic Workbench help docs;
- synthetic scoped templates/files;
- synthetic saved queries;
- synthetic Data Dictionary tables and columns;
- synthetic approved join patterns;
- synthetic Oracle docs cache entries;
- synthetic denied/private cross-domain source.

No real client data should appear in any fixture.

## Acceptance Evidence

Each implementation slice should record:

```text
backend tests
frontend tests
browser QA when UI changes
runtime freshness result
screenshots for meaningful states
source index health
SQL helper safety checks
Oracle docs cache/freshness behavior when applicable
```

## Non-Functional Validation

Performance targets for future implementation should include:

- launcher render has negligible impact on module screen load;
- local search returns quickly for typical local corpus size;
- source indexing can run without freezing the UI;
- Oracle lookup has timeout and fallback;
- assistant panel remains usable with long SQL snippets and many source cards.

Exact numeric thresholds should be chosen after corpus size is known.
