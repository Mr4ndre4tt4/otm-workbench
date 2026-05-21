# GUI Shell QA Contracts

Date: 2026-05-21
Branch: `codex/gui-shell-qa-contracts`

## Objective

Keep the GUI foundation stable before deeper component and screen-level CSS splits. This slice turns the visual governance points into lightweight contracts around the backend-owned shell state.

## Covered Contracts

- Theme controls must persist through `/api/v1/platform/user-preferences`.
- System theme must store `theme_mode=system` with `follow_system_theme=true`.
- Density and sidebar mode must continue to update `.app-shell` data attributes.
- Expanded sidebar must show backend navigation status chips.
- Collapsed sidebar must keep navigation links available while omitting status chips from the compact rail.

## Manual Visual QA Checklist

Run this checklist before major GUI refactors or before accepting new module screens:

- Light mode, comfortable density, expanded sidebar.
- Dark mode, comfortable density, expanded sidebar.
- System theme with OS dark preference.
- Compact density with expanded sidebar.
- Compact density with collapsed sidebar.
- Mobile viewport below 900px with collapsed sidebar.
- Each module route opens from backend navigation without custom page chrome.
- No text overlap in topbar, preference controls, nav labels, status chips, and primary module panels.
- Icon-only controls expose labels through accessible names and tooltips.

## Non-goals

- No redesign in this slice.
- No browser screenshot claim without an actual browser run.
- No frontend-only preference state; persisted preference behavior remains backend-owned.

## Follow-up

- Add browser-backed visual snapshots when the local browser sandbox is stable.
- Split larger component CSS only after the shell QA contract remains green.

## Browser QA Attempt

`GUI_BROWSER_QA_ATTEMPT.md` records the first post-CSS-split browser QA attempt.
The local Vite server responded successfully, but the in-app browser runner was
blocked by the Windows process creation environment, so no screenshot evidence
is claimed yet.
