# GUI Login Panel Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-login-panel-contract`  
**Scope:** unauthenticated shell entry point and backend session handoff.

## 1. Purpose

`LoginPanel` is the single shell-owned pattern for unauthenticated access to
OTM Workbench.

It keeps the sign-in form, backend session messaging, submit state, and error
rendering out of `App.tsx` so the app root remains responsible for orchestration
only.

## 2. Ownership Boundary

`LoginPanel` may own:

```text
- email and password input state
- submit-in-progress state
- presentation of backend login errors
- calling the backend session endpoint through the platform hook
- handing the returned access token to AuthProvider
```

`LoginPanel` must not own:

```text
- roles or permissions
- module visibility
- active project/profile/environment context
- user preferences
- lifecycle, readiness, or action availability
- durable user profile data
```

Those remain backend-owned and are fetched after authentication.

## 3. Required Behavior

```text
1. Render before protected backend contracts are queried.
2. Submit credentials through POST /api/v1/platform/session/login.
3. Store only the returned browser session token through AuthProvider.
4. Render backend auth errors inside the shared shell form pattern.
5. Keep the unauthenticated message focused on backend-owned contracts.
```

## 4. Component Rule

```text
frontend/src/app/shell/LoginPanel.tsx owns:
- login-panel markup
- login-form markup
- sign-in submit state
- auth error message rendering
```

No module view or page route should create its own login form.

## 5. Verification

```text
frontend/src/app/shell/LoginPanel.test.tsx
frontend/tests/loginPanelPatternContract.test.ts
```

The tests verify that the component calls the backend session endpoint, persists
only the returned session token, renders backend auth errors, and keeps login
markup centralized in the shell component.
