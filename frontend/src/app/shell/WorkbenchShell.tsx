import { type PropsWithChildren, useState } from "react";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

import { ApiError } from "../../platform/api";
import { updateUserPreferences } from "../../platform/hooks";
import type { NavigationItem, UserPreferences } from "../../platform/types";
import { Button, FeedbackMessage, IconButton } from "../../ui/components";
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
  const queryClient = useQueryClient();
  const [isSidebarSaving, setIsSidebarSaving] = useState(false);
  const [sidebarError, setSidebarError] = useState<string | null>(null);
  const themeMode = preferences?.theme_mode ?? "light";
  const density = preferences?.density ?? "comfortable";
  const nextSidebarMode: UserPreferences["sidebar_mode"] = sidebarMode === "collapsed" ? "expanded" : "collapsed";

  async function toggleSidebarMode() {
    if (!token || !preferences || isSidebarSaving) return;
    setSidebarError(null);
    setIsSidebarSaving(true);
    const nextPreferences = { ...preferences, sidebar_mode: nextSidebarMode };
    try {
      await updateUserPreferences(token, nextPreferences);
      queryClient.setQueryData(["platform", "user-preferences"], nextPreferences);
      await queryClient.invalidateQueries({ queryKey: ["platform", "user-preferences"] });
    } catch (caught) {
      if (caught instanceof ApiError) {
        setSidebarError(caught.message);
      } else {
        setSidebarError("Unable to update sidebar preference.");
      }
    } finally {
      setIsSidebarSaving(false);
    }
  }

  return (
    <div className="app-shell" data-density={density} data-sidebar={sidebarMode} data-theme={themeMode}>
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-lockup">
            <span className="brand-mark">OTM</span>
            <div className="brand-text">
              <strong>Workbench</strong>
              <span>Implementation cockpit</span>
            </div>
          </div>
          <IconButton
            disabled={!token || !preferences || isSidebarSaving}
            label={sidebarMode === "collapsed" ? "Expand sidebar" : "Collapse sidebar"}
            onClick={() => void toggleSidebarMode()}
          >
            {sidebarMode === "collapsed" ? <PanelLeftOpen aria-hidden="true" /> : <PanelLeftClose aria-hidden="true" />}
          </IconButton>
        </div>
        {sidebarError ? <FeedbackMessage tone="error">{sidebarError}</FeedbackMessage> : null}
        <SidebarNav currentPath={currentPath} items={navigationItems} />
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
