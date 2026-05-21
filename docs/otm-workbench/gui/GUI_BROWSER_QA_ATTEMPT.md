# GUI Browser QA Attempt

Date: 2026-05-21
Branch: `codex/gui-browser-qa-attempt`

## Objective

Attempt a browser-backed visual QA pass after the CSS foundation was split into theme, base, shell, component, layout, density, sidebar, and responsive layers.

## Environment Check

The local Vite server started successfully and responded at:

```text
http://127.0.0.1:5173/
```

The HTTP readiness check returned `200`.

## Browser Result

The in-app browser runner could not start in this Windows environment. The runtime failed while creating the browser-control process with:

```text
CreateProcessWithLogonW failed: 1909
```

Because of this, no screenshot or visual browser assertion is claimed for this slice.

## Validated Without Browser

The CSS refactor stack remains covered by:

```text
npm run lint
npm run test
npm run build
git diff --check
sensitive scan over changed GUI files
```

Recent frontend contract coverage includes:

- backend-owned theme preference updates
- system theme persistence with `follow_system_theme=true`
- density and sidebar root shell attributes
- expanded versus collapsed sidebar navigation behavior

## Pending Visual QA Matrix

Run this matrix when browser automation is stable:

- Login screen, desktop width, light mode default.
- Login screen, mobile width below 900px.
- Authenticated shell, light mode, comfortable density, expanded sidebar.
- Authenticated shell, dark mode, comfortable density, expanded sidebar.
- Authenticated shell, system theme with OS dark preference.
- Authenticated shell, compact density, expanded sidebar.
- Authenticated shell, compact density, collapsed sidebar.
- Authenticated shell, mobile width below 900px, collapsed sidebar.
- Representative module route for Rates Studio.
- Representative module route for Integration Mapping Studio.

## Acceptance Notes

- Do not accept future visual QA as complete without actual browser evidence.
- Screenshots should be attached or referenced when the browser runner is available.
- Until then, CSS refactor slices must keep lint, tests, build, and contract tests green.
