# GUI Preference Controls Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-preference-controls-contract`  
**Scope:** shared shell rendering for theme, density, and sidebar preferences.

## 1. Decision

Workbench preference controls must use the shared `PreferenceControls` shell
component instead of rendering theme, density, or sidebar toggles directly
inside app or module screens.

This keeps light/dark/system mode, density, and sidebar behavior consistent
while preserving backend ownership of persisted user preferences.

## 2. Current Contract

Use:

```text
PreferenceControls
```

For:

```text
- light mode
- dark mode
- system theme mode
- comfortable/compact density
- expanded/collapsed sidebar
```

Do not use raw `preference-controls` markup outside:

```text
frontend/src/app/shell/PreferenceControls.tsx
```

## 3. Boundary

The component owns preference control rendering and optimistic local query
refresh only.

Backend remains responsible for:

```text
- persisted user preferences
- allowed preference values
- default preference values
- authentication/token requirements
- future user-level preference policy
```

The frontend must not store these preferences only in local UI state.

## 4. Guardrail

The contract is enforced by:

```text
frontend/src/app/shell/PreferenceControls.test.tsx
frontend/tests/preferenceControlsPatternContract.test.ts
```

The static contract blocks raw `preference-controls` markup outside the shared
shell component.

## 5. Next Extensions

Later slices can extend this pattern with:

```text
- backend-provided preference schema
- icon family swap for light/dark variants
- keyboard shortcuts
- per-user persisted workspace defaults
- desktop wrapper preference sync
```

Those extensions should continue using backend-owned preference contracts.
