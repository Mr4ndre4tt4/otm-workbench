const SESSION_TOKEN_KEY = "otm_workbench.session_token";

export function readSessionToken(): string | null {
  return window.sessionStorage.getItem(SESSION_TOKEN_KEY);
}

export function writeSessionToken(token: string): void {
  window.sessionStorage.setItem(SESSION_TOKEN_KEY, token);
}

export function clearSessionToken(): void {
  window.sessionStorage.removeItem(SESSION_TOKEN_KEY);
}
