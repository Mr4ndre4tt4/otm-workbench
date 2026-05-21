import { useLocation } from "react-router-dom";

import { WorkbenchRoute } from "./routes/WorkbenchRoute";
import { LoginPanel, WorkbenchShell } from "./shell";
import { useNavigation, useUserPreferences } from "../platform/hooks";
import { useAuth } from "../platform/useAuth";

export function App() {
  const auth = useAuth();
  const navigation = useNavigation(auth.token);
  const preferences = useUserPreferences(auth.token);
  const location = useLocation();
  const sidebarMode = preferences.data?.sidebar_mode ?? "expanded";
  const navigationItems = navigation.data?.items ?? [];

  return (
    <WorkbenchShell
      currentPath={location.pathname}
      isAuthenticated={auth.isAuthenticated}
      navigationItems={navigationItems}
      onSignOut={auth.signOut}
      preferences={preferences.data}
      sidebarMode={sidebarMode}
      token={auth.token}
    >
      {auth.token ? <WorkbenchRoute items={navigationItems} token={auth.token} /> : <LoginPanel />}
    </WorkbenchShell>
  );
}
