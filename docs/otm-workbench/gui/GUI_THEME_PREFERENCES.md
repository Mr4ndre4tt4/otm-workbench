# GUI Shell Preferences

**Status:** implemented
**Branch:** `codex/gui-shell-preference-controls`

## Objective

Make theme, density, and sidebar choices backend-owned from the first GUI
iteration, so future browser, desktop, and collaborative clients can consume the
same user preference contract instead of reimplementing local-only state.

## Backend Contract

User preferences are stored in `user_preferences` with one row per user.

```text
GET /api/v1/platform/user-preferences
PUT /api/v1/platform/user-preferences
```

Default response:

```json
{
  "theme_mode": "light",
  "follow_system_theme": false,
  "density": "comfortable",
  "sidebar_mode": "expanded"
}
```

Supported values:

- `theme_mode`: `light`, `dark`, `system`
- `density`: `comfortable`, `compact`
- `sidebar_mode`: `expanded`, `collapsed`

## GUI Behavior

The topbar preference controls now call the backend preference contract:

- Sun icon sets `theme_mode = light`
- Moon icon sets `theme_mode = dark`
- Monitor icon sets `theme_mode = system` and `follow_system_theme = true`
- Rows icon toggles `density` between `comfortable` and `compact`
- Sidebar icon toggles `sidebar_mode` between `expanded` and `collapsed`

The active preference is reflected with `aria-pressed`, an active button style,
and root shell attributes:

```text
data-theme
data-density
data-sidebar
```

## Desktop-Ready Note

The `system` option is intentionally represented in the backend contract. The
current web GUI uses CSS media preference behavior; a future Windows desktop
client can map the same value to the OS theme source without changing the API.

## Validation

- Backend preference defaults and update/read cycle covered by
  `tests/test_operational_context.py`.
- GUI preference writes and active shell state covered by
  `frontend/src/app/App.test.tsx`.
