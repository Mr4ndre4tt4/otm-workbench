import { type PropsWithChildren, useMemo, useState } from "react";

import { AuthContext, type AuthContextValue } from "./authContext";
import { clearSessionToken, readSessionToken, writeSessionToken } from "./sessionStorage";

export function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(() => readSessionToken());

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      isAuthenticated: Boolean(token),
      signIn: (nextToken: string) => {
        writeSessionToken(nextToken);
        setToken(nextToken);
      },
      signOut: () => {
        clearSessionToken();
        setToken(null);
      }
    }),
    [token]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
