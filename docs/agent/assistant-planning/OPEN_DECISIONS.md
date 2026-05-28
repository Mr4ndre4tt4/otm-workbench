# Workbench Assistant Open Decisions

## Purpose

This document lists decisions that should be resolved before implementation or
before creating high-fidelity Figma artifacts.

## Decision 1: Public View Assistant Behavior

Question:

Should the assistant be available in Public View?

Recommended answer:

Yes, but limited to public Workbench help, public/shared sources, Data
Dictionary, and official Oracle docs. Private finder results and saved queries
remain hidden.

Impact:

This keeps the assistant useful without weakening the Public View boundary.

## Decision 2: SQL Draft Storage

Question:

Should SQL helper output be copy-only, saved as draft query, or both?

Recommended answer:

Both, but saving as a draft query should require an explicit action. Copy is
immediate; saved draft becomes a scoped source with `status=draft`.

Impact:

This lets consultants reuse useful drafts while keeping unreviewed SQL separate
from approved query examples.

## Decision 3: Oracle Docs Live Lookup Trigger

Question:

Should Oracle documentation lookup require an explicit action?

Recommended answer:

Yes. The assistant can suggest "Search official Oracle docs" when needed, but
live lookup should be explicit because it may use network/API cost and has
freshness implications.

Impact:

This makes cost and source freshness visible to the consultant.

## Decision 4: Assistant Conversation History

Question:

Should the assistant persist conversation history?

Recommended answer:

Persist minimal local history only after scope and privacy rules are designed.
For the first implementation, keep history short-lived unless a saved draft or
source action is explicitly created.

Impact:

This reduces privacy risk and avoids storing accidental client details in chat
logs.

## Decision 5: Archived Source Search

Question:

Should archived assets, retired queries, and obsolete docs appear in search?

Recommended answer:

Hide them by default. Provide an explicit include archived/retired filter for
authorized users later.

Impact:

Consultants see current material first and avoid accidental reuse of retired
templates or obsolete SQL.

## Decision 6: Oracle Docs Provider

Question:

Which live lookup provider should be used for official Oracle docs?

Recommended answer:

Defer provider choice until implementation planning. The contract should only
require official-source allowlisting, cache metadata, and source links.

Impact:

Keeps architecture provider-agnostic and avoids locking in cost before testing.

## Decision 7: Assistant Icon Asset

Question:

Should the truck-driver robot launcher be custom-designed immediately?

Recommended answer:

Use a conceptual icon in wireframes first. Design the polished icon after the
assistant panel behavior is accepted.

Impact:

Prevents icon polish from distracting from architecture, safety, and source
trust.

## Decision 8: Desktop Packaging

Question:

Should the assistant target a desktop packaged app?

Recommended answer:

Not initially. Keep the architecture in the current local web app and evaluate
desktop packaging only after the assistant proves useful.

Impact:

Avoids Tauri/Electron overhead while preserving future packaging options.

## Decision 9: Optional AI Adapter

Question:

Should optional AI be included in the first assistant implementation?

Recommended answer:

No. Build local source-bound behavior first. Add AI only after the assistant can
answer useful questions without it.

Impact:

Keeps the assistant lightweight, cheaper, and easier to trust.

## Decision 10: First Implementation Slice

Question:

Should the first implementation slice be UI launcher or source index?

Recommended answer:

Source index first. The robot UI is attractive, but it needs reliable local
sources to avoid becoming an empty shell.

Impact:

Improves technical foundation and allows isolated backend tests before touching
dense module screens.
