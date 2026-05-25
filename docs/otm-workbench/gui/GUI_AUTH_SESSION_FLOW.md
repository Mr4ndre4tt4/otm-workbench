# GUI Auth Session Flow

**Status:** initial GUI session flow delivered  
**Branch:** `codex/gui-auth-session`

## Objective

Let the browser-first GUI consume protected backend contracts through a real
FastAPI session token instead of calling platform endpoints anonymously.

## Implemented

- Login panel rendered before protected contracts are called.
- Login panel markup and submit behavior centralized in
  `frontend/src/app/shell/LoginPanel.tsx`.
- Login submits to `POST /api/v1/platform/session/login`.
- Successful login stores the bearer token through a platform session storage
  adapter.
- API client attaches `Authorization: Bearer <token>` when a token is present.
- Navigation, Project Cockpit summary, and user preferences queries are enabled
  only after authentication.
- Backend auth errors are scoped to the current login draft. Editing email or
  password clears stale error feedback before the next submit.
- Sign out clears the session token and returns the shell to the login state.

## Ownership Boundary

The frontend stores only the current browser session token. It does not own:

- user identity truth;
- roles or permissions;
- module visibility;
- durable preferences;
- lifecycle or readiness decisions.

Those remain backend-owned and are fetched after authentication.

## Files

```text
frontend/src/platform/auth.tsx
frontend/src/platform/authContext.ts
frontend/src/platform/useAuth.ts
frontend/src/platform/sessionStorage.ts
frontend/src/platform/api.ts
frontend/src/platform/hooks.ts
frontend/src/app/App.tsx
frontend/src/app/shell/LoginPanel.tsx
```

## Verification

```text
npm run test -- LoginPanel.test.tsx
npm run qa:functional:shell:browser
npm run lint
npm run build
```

The auth tests assert that protected contracts are not called before login and
that authenticated requests receive the bearer token after login. The shell
browser journey also covers failed-login recovery before the successful
session handoff.
