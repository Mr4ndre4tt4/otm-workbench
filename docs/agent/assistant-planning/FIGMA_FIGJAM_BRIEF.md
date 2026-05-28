# Workbench Assistant Figma And FigJam Brief

## Purpose

This brief prepares the visual design and diagramming work for the Workbench
Assistant. It should be used before creating Figma or FigJam artifacts.

## Recommended Order

1. FigJam technical architecture and flow board.
2. Figma low-to-mid fidelity assistant UI state board.
3. Optional launcher icon exploration.
4. Optional clickable prototype after the UI state board is accepted.

## User Context

Primary user:

```text
OTM consultant
desktop-heavy usage
frequent short assistant interactions
works inside dense operational modules
needs source-traceable answers
```

Primary tasks:

- ask for help on current screen;
- find templates/files/queries/evidence;
- navigate to the right Workbench route;
- draft SQL using Data Dictionary;
- consult official Oracle documentation.

## Visual Direction

```text
density: compact
tone: precise, operational, consultant-focused
launcher personality: small truck-driver robot
panel personality: restrained Workbench utility
primary visual hierarchy: context -> answer -> sources -> actions
```

Avoid:

- consumer support-chat look;
- generic "ask me anything" hero copy;
- decorative mascot-heavy empty states;
- large gradients;
- source-less answers;
- panel layouts too small for SQL and citations.

## FigJam Board Scope

Recommended sections:

```text
01 Intent and boundaries
02 High-level architecture
03 Local source index
04 Scope guard and Public View
05 SQL helper
06 Oracle docs lookup and cache
07 UI state model
08 Delivery roadmap
09 Risks and gates
```

## Figma Board Scope

Recommended frames:

```text
01 Launcher closed on dense Workbench route
02 Assistant open default
03 Current screen help answer
04 Finder results
05 SQL draft answer
06 Oracle docs result
07 Permission blocked result
08 Offline/local-only result
09 Ambiguous SQL clarification
10 Narrow viewport panel
```

## Frame Requirements

Each Figma frame should annotate:

- user task;
- primary action;
- source/citation region;
- backend data required;
- permission behavior;
- empty/error/blocked state where relevant;
- accessibility notes.

## Launcher Direction

The launcher should be:

- small enough to stay out of the way;
- visually distinct from normal Workbench controls;
- recognizable as assistant access;
- not cartoonish enough to reduce trust;
- paired with accessible text/tooltip.

Potential visual concepts:

1. robot head with tiny trucker cap;
2. robot face inside a steering-wheel/speedometer mark;
3. compact delivery-cab robot silhouette.

The icon can be custom later. For wireframes, use a labeled circular launcher.

## Open Questions For Visual Calibration

Before drawing the first Figma board, confirm:

1. Should the Figma artifact be diagram-only, annotated wireframe, or
   mockup-ready?
2. Should the launcher icon be concept-only or designed visually?
3. Should SQL helper states be shown with real SQL-shaped synthetic examples?
4. Should the panel open as an overlay drawer or as a resizable side panel?
5. Should Oracle live lookup show an explicit cost/network confirmation?

## Recommended Answer For First Visual Pass

Use:

```text
annotated product wireframe
concept launcher only
synthetic SQL-shaped examples
right-side drawer
explicit Oracle live lookup indicator
```

Reason:

This gives enough detail for engineering without spending time on polished
iconography before the architecture and assistant behavior are accepted.
