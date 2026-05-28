# Workbench Assistant Figma Wireframe Manifest

## Purpose

This manifest defines the future Figma wireframe board for the Workbench
Assistant UI. It should be created after the technical FigJam board or after
the user explicitly chooses Figma first.

## File/Page Concept

Suggested file or page name:

```text
OTM Workbench - Workbench Assistant UI States
```

## User And Task

Primary user:

```text
OTM consultant working inside dense Workbench modules.
```

Primary task:

```text
Open the assistant from the current screen, ask a scoped operational question,
and receive a source-bound answer or action.
```

## Visual Language Declaration

Recommended for wireframe stage:

```text
Display font: IBM Plex Sans
Body font: IBM Plex Sans
Mono font: IBM Plex Mono
Background: neutral Workbench canvas
Surface: existing Workbench panel surface
Accent: restrained operational blue/teal
Warning: amber
Destructive: red
Success: green
Density: compact
Border radius: 6px or existing Workbench token
Tone: precise consultant utility
```

The launcher can carry the playful truck-driver robot concept. The panel should
remain operational and restrained.

## Frame Inventory

### 01 Launcher Closed On Dense Workbench Route

Purpose:

Show the assistant as available but non-invasive.

Regions:

- existing Workbench shell;
- representative dense module content;
- lower-right launcher;
- tooltip/accessibility note.

Annotations:

- does not cover primary action;
- accessible name;
- no auto-open behavior.

### 02 Assistant Open Default

Purpose:

Show the default open state with current context and quick actions.

Regions:

- header;
- context strip;
- quick actions;
- empty/default body;
- input composer;
- source/cost mode indicator.

### 03 Current Screen Help Answer

Purpose:

Show a local Workbench help response.

Regions:

- short answer;
- steps;
- related route/action;
- sources;
- confidence.

### 04 Finder Results

Purpose:

Show templates/files/queries/evidence results.

Regions:

- search summary;
- result cards;
- scope metadata;
- open/copy actions;
- source filters.

### 05 SQL Draft

Purpose:

Show a SQL helper answer.

Regions:

- purpose;
- SQL code block;
- parameters;
- tables/columns;
- assumptions/warnings;
- sources;
- copy/save draft actions.

Synthetic example:

```sql
select
  s.shipment_gid
from shipment s
where s.shipment_gid = :shipment_gid
```

### 06 Oracle Docs Result

Purpose:

Show official Oracle docs result.

Regions:

- official link;
- short summary;
- cache/live status;
- fetched timestamp;
- refresh action.

### 07 Permission Blocked

Purpose:

Show safe no-leak behavior.

Required copy concept:

```text
I found matching material outside your current accessible scope. Change context
or request access if you expected to see it.
```

Annotations:

- no title;
- no path;
- no snippets;
- no count.

### 08 Offline Limited

Purpose:

Show local-only mode when web lookup is unavailable.

Regions:

- local capabilities still available;
- Oracle live lookup unavailable;
- cached source option if present.

### 09 Ambiguous SQL Clarification

Purpose:

Show one focused clarification instead of a risky SQL guess.

Example choices:

- shipment header;
- shipment stops;
- shipment status/events;
- shipment/order relationship.

### 10 Narrow Viewport

Purpose:

Show responsive behavior.

Requirements:

- close path remains visible;
- SQL block scrolls;
- result cards stack;
- launcher remains reachable.

## Component Inventory

Reusable components:

- `AssistantLauncher`
- `AssistantPanel`
- `AssistantContextStrip`
- `AssistantQuickActions`
- `AssistantMessageList`
- `AssistantResultCard`
- `AssistantSourceList`
- `AssistantSqlBlock`
- `AssistantOracleResult`
- `AssistantBlockedState`
- `AssistantComposer`

## Accessibility Annotations

Every frame should note:

- launcher accessible name;
- keyboard open/close;
- Escape behavior;
- focus return;
- source link focus order;
- copy button accessible label;
- polite live region for answer updates.

## Data Requirements

Each frame should annotate required backend data:

```text
current route/module context
scope context
quick action definitions
structured assistant response
source citations
actions with enabled/disabled state
```

## Acceptance Criteria

- Frames cover the hard states, not only the happy path.
- SQL state has realistic space requirements.
- Oracle state makes live/cached source clear.
- Blocked state demonstrates no-leak behavior.
- Launcher does not visually compete with module content.
- Panel feels like Workbench utility, not consumer support chat.
