import { type PropsWithChildren } from "react";

import type { NavigationItem, UserPreferences } from "../../platform/types";
import { Button } from "../../ui/components";
import { PreferenceControls } from "./PreferenceControls";
import { SidebarNav } from "./SidebarNav";

type WorkbenchShellProps = PropsWithChildren<{
  currentPath: string;
  isAuthenticated: boolean;
  navigationItems: NavigationItem[];
  onSignOut: () => void;
  preferences: UserPreferences | undefined;
  sidebarMode: UserPreferences["sidebar_mode"];
  token: string | null;
}>;

export function WorkbenchShell({
  children,
  currentPath,
  isAuthenticated,
  navigationItems,
  onSignOut,
  preferences,
  sidebarMode,
  token
}: WorkbenchShellProps) {
  const themeMode = preferences?.theme_mode ?? "light";
  const density = preferences?.density ?? "comfortable";

  return (
    <div className="app-shell" data-density={density} data-sidebar={sidebarMode} data-theme={themeMode}>
      <aside className="sidebar">
        <div className="brand-lockup">
          <span className="brand-mark">OTM</span>
          <div className="brand-text">
            <strong>Workbench</strong>
            <span>Implementation cockpit</span>
          </div>
        </div>
        <SidebarNav currentPath={currentPath} items={navigationItems} sidebarMode={sidebarMode} />
      </aside>

      <main className="main-area">
        <div className="topbar">
          <span>Backend-owned contracts</span>
          <div className="topbar-actions">
            {isAuthenticated ? <Button onClick={onSignOut}>Sign out</Button> : null}
            <PreferenceControls preferences={preferences} token={token} />
          </div>
        </div>
        {children}
      </main>
    </div>
  );
}
