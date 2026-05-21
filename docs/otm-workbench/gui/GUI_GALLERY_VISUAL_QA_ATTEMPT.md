# GUI Gallery Visual QA Attempt

Date: 2026-05-21
Branch: `codex/gui-visual-qa-gallery-shell-states`
Linear: `OTM-65`

## Objective

Attempt a browser-backed visual QA pass for the internal component gallery and
shell states after the MVP gallery coverage matrix was completed.

Target route:

```text
http://127.0.0.1:8032/__gui/component-gallery
```

## Environment Check

The local Vite server started successfully from `frontend/` with:

```text
npm run dev -- --host 127.0.0.1 --port 8032
```

The HTTP readiness check returned:

```text
200
```

## Browser Result

The in-app Browser plugin could not initialize the browser-control runtime in
this Windows sandbox. The Node-backed browser runtime exited while creating the
process with:

```text
CreateProcessWithLogonW failed: 1326
```

Because of this, no screenshot, pixel inspection, or visual browser assertion
is claimed for this slice.

## Validated Without Browser

The gallery coverage branch remains protected by automated checks:

```text
npm run lint
npm run test
npm run build
git diff --check
```

The latest completed gallery validation before this visual QA attempt passed:

```text
47 frontend test files
132 frontend tests
```

The route was also verified as reachable through HTTP before browser automation
was attempted.

## Pending Visual QA Matrix

Run this matrix when browser automation is stable:

- Component gallery, desktop light mode default.
- Component gallery, desktop dark mode.
- Component gallery, compact density.
- Component gallery, collapsed sidebar.
- Component gallery, mobile width below 900px.
- LoginPanel example inside the gallery.
- Context and preference examples with no text overlap.
- ActionBar enabled, disabled, and running states.
- StatusChip variants for ready, blocked, error, read-only, pending, and active.
- Long labels and empty/blocked states across module workspace examples.

## Acceptance Notes

- OTM-65 cannot be accepted as completed visual QA without actual browser
  evidence.
- Future visual QA should attach screenshots or a browser-generated evidence
  note.
- Until browser automation is stable, continue to keep lint, tests, build, and
  contract tests green for GUI changes.
