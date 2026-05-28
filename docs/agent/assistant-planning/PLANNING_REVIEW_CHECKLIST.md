# Workbench Assistant Planning Review Checklist

## Purpose

This checklist helps review the Workbench Assistant planning packet before the
work moves to FigJam/Figma artifacts or implementation planning.

## Product Boundary

- [ ] The assistant is understood as an embedded Workbench utility, not a
      top-level module.
- [ ] The lower-right truck-driver robot launcher is accepted as the entry
      concept.
- [ ] The open assistant panel is accepted as a right-side drawer/panel, not a
      small chat bubble.
- [ ] The assistant is focused on consultant help, search, navigation, SQL, and
      Oracle docs lookup.
- [ ] The assistant is not expected to behave like a generic reasoning agent.

## Stack Direction

- [ ] FastAPI inside the existing backend is accepted as the future backend
      boundary.
- [ ] SQLite remains the baseline assistant store.
- [ ] SQLite FTS5 is accepted as the first search engine.
- [ ] No heavy local LLM is required.
- [ ] Optional AI remains a future enhancement, disabled by default.
- [ ] No package installation is required during planning.

## Source And Search

- [ ] Local source index model is accepted.
- [ ] Workbench docs, route metadata, assets, artifacts, evidence, Data
      Dictionary, saved queries, and Oracle cache are valid source categories.
- [ ] Scope filtering before snippets is accepted.
- [ ] Source confidence labels are accepted.
- [ ] Index health and failed-source reporting are accepted as future
      diagnostic capabilities.

## SQL Helper

- [ ] SQL helper is accepted as select-only and draft-only.
- [ ] Data Dictionary grounding is mandatory.
- [ ] Approved query examples can influence suggestions.
- [ ] Join patterns must be explicit and source-backed.
- [ ] Ambiguous SQL requests should trigger clarification instead of guessing.
- [ ] Mutating SQL requests should be rejected in the initial design.

## Oracle Docs

- [ ] Oracle docs lookup requires official source links.
- [ ] Live lookup should be explicit because it may use web/API cost.
- [ ] Queries sent outside the Workbench must be sanitized.
- [ ] Cached Oracle docs results must show freshness.
- [ ] No official source means no authoritative answer.

## Privacy And Governance

- [ ] Full chat history is not persisted by default.
- [ ] Saved SQL drafts require explicit action.
- [ ] Denied private results do not reveal title, path, snippet, client name, or
      count.
- [ ] Public View assistant behavior is restricted to public/shared sources.
- [ ] Optional AI cannot bypass scope guard or invent citations.

## UI/UX

- [ ] Launcher closed state is quiet and accessible.
- [ ] Panel shows current module, route, domain, environment, and visibility.
- [ ] Quick actions vary by current module.
- [ ] SQL, finder, help, Oracle, blocked, offline, and clarification states are
      all represented.
- [ ] Figma/FigJam should start with annotated wireframes/diagrams, not polished
      visual design.

## Delivery

- [ ] Phase 0 planning is accepted before implementation.
- [ ] Phase 1 should build source index before the assistant UI.
- [ ] Figma/FigJam diagrams should come before high-fidelity prototype work.
- [ ] GitHub tracking should wait until the assistant is promoted into active
      roadmap scope.
- [ ] Current Assets/module delivery remains undisturbed.

## Open Decisions To Resolve

Review:

- `OPEN_DECISIONS.md`

Most important decisions:

1. Public View assistant behavior.
2. SQL draft copy/save behavior.
3. Oracle Docs live lookup trigger.
4. Conversation history persistence.
5. First implementation slice.

## Review Outcome

Use one of these outcomes:

```text
Accepted for FigJam/Figma diagramming
Accepted with revisions
Needs more planning
Rejected/deferred
```

## Notes

Record review notes here when this planning packet is formally reviewed.
