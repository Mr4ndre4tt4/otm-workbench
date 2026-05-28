# Workbench Assistant Visual Calibration Questionnaire

## Purpose

Before creating FigJam or Figma artifacts for the Workbench Assistant, confirm
the visual scope and fidelity. This follows the Michelangelo create-mode rule:
calibrate first, draw second.

## Recommended Answers

If no changes are requested, use:

```text
1A, 2B, 3B, 4A, 5A, 6B
```

## Questions

### 1. First Visual Artifact

A. FigJam technical diagrams first. Recommended.
B. Figma assistant UI wireframes first.
C. Single combined Figma/FigJam pass.

Why this matters:

The assistant has important architecture, source, scope, and SQL safety rules.
FigJam first lets the system model settle before spending time on UI layout.

### 2. Wireframe Fidelity

A. Low-fidelity boxes only.
B. Annotated product wireframe. Recommended.
C. Mockup-ready visual design.

Why this matters:

Annotated product wireframes are detailed enough for engineering and review
without prematurely polishing the robot icon or panel styling.

### 3. Assistant UI Breadth

A. Launcher and default panel only.
B. Full state set. Recommended.
C. SQL helper states only.

Why this matters:

The assistant must handle help, finder, SQL, Oracle docs, blocked, offline, and
clarification states. A full state set prevents a nice default screen from
hiding hard cases.

### 4. Robot Icon Treatment

A. Conceptual launcher marker only. Recommended.
B. Explore 3 icon concepts.
C. Design polished launcher asset.

Why this matters:

The icon matters, but it should not outrun the source, scope, and panel behavior
design. A conceptual marker is enough for the first wireframe pass.

### 5. SQL Examples In Frames

A. Use synthetic SQL-shaped examples. Recommended.
B. Use abstract SQL blocks without realistic structure.
C. Avoid SQL in visual frames.

Why this matters:

SQL is a core use case. Synthetic examples make the panel layout realistic while
preserving the no-real-client-data rule.

### 6. Oracle Lookup UX

A. Search automatically when intent is detected.
B. Show explicit "Search official Oracle docs" action. Recommended.
C. Only use cached Oracle docs in the first visual pass.

Why this matters:

Live Oracle lookup has freshness, network, and potential cost implications.
Making it explicit keeps trust visible.

## Output After Calibration

Once the answers are confirmed, the next artifact should be either:

```text
FigJam technical board manifest -> FigJam creation
```

or:

```text
Figma wireframe manifest -> Figma creation
```

The current recommendation is FigJam first, then Figma.
