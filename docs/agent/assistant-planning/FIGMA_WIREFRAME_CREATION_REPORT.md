# Workbench Assistant Figma Wireframe Creation Report

## Status

Created on 2026-05-28.

## Figma File

```text
OTM Workbench - Workbench Assistant UI States
file-key: PGi8kpAkFKj7zeDQklmvsj
url: https://www.figma.com/design/PGi8kpAkFKj7zeDQklmvsj
page: Workbench Assistant UI States
```

## Created Frames

1. `01 Launcher closed`
2. `02 Open default`
3. `03 Help answer`
4. `04 Finder results`
5. `05 SQL draft`
6. `06 Oracle docs`
7. `07 Permission blocked`
8. `08 Offline limited`
9. `09 SQL clarification`
10. `10 Narrow viewport`

## Source Documents

- `FIGMA_WIREFRAME_MANIFEST.md`
- `UI_EXPERIENCE_SPEC.md`
- `SQL_HELPER_DESIGN.md`
- `ORACLE_DOCS_CONNECTOR_POLICY.md`
- `PRIVACY_AND_HISTORY_POLICY.md`
- `RESPONSE_CONTRACT.md`

## Visual Scope

The board is an annotated product wireframe, not a polished mockup.

It intentionally uses:

- synthetic Workbench context;
- synthetic SQL-shaped content;
- conceptual assistant launcher marker;
- compact right-side assistant panel;
- visible hard states, including permission-blocked and offline-limited
  behavior.

## Validation

Structural readback was performed with Figma metadata:

- top-level page `0:1` exists and is named `Workbench Assistant UI States`;
- all ten frame titles exist;
- the launcher closed frame includes a lower-right assistant launcher marker;
- assistant panel frames include context strip/pill elements;
- SQL draft, Oracle docs, permission blocked, offline limited, clarification,
  and narrow viewport states are represented.

Screenshot verification was requested for page `0:1`:

```text
rendered screenshot: 1600 x 1094
original canvas bounds: 2040 x 1395
```

## Known Limitations

- The launcher icon is a conceptual `AI` marker, not the final truck-driver
  robot illustration.
- The board uses simple Figma primitives instead of a reusable component
  library.
- Text density and panel widths should be refined in a later UI pass before
  implementation.
- No interaction prototype links were created.

## Recommended Next Step

Review the Figma board with the FigJam architecture board. Then decide whether
to:

1. refine the UI wireframes visually;
2. design the truck-driver robot launcher asset;
3. create an implementation plan for the source index foundation;
4. defer implementation until current module delivery allows a cross-cutting
   assistant slice.
