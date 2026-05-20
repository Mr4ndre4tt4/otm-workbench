import { createContext } from "react";

export type AuthContextValue = {
  token: string | null;
  isAuthenticated: boolean;
  signIn: (token: string) => void;
  signOut: () => void;
};

export const AuthContext = createContext<AuthContextValue | null>(null);
