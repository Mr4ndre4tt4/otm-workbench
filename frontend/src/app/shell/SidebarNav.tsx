import { Activity, Archive, ChevronRight } from "lucide-react";
import { NavLink } from "react-router-dom";

import { isNavigationItemActive } from "../routes/routeUtils";
import { StatusChip } from "../../ui/components";
import type { NavigationItem, UserPreferences } from "../../platform/types";

function navIcon(moduleId: string) {
  if (moduleId === "home") return <Activity aria-hidden="true" />;
  if (moduleId === "evidence") return <Archive aria-hidden="true" />;
  return <ChevronRight aria-hidden="true" />;
}

export function SidebarNav({
  currentPath,
  items,
  sidebarMode
}: {
  currentPath: string;
  items: NavigationItem[];
  sidebarMode: UserPreferences["sidebar_mode"];
}) {
  return (
    <nav className="sidebar-nav" aria-label="Workbench modules">
      {items.map((item) => (
        <NavLink
          className={isNavigationItemActive(item, currentPath) ? "nav-item nav-item-active" : "nav-item"}
          key={item.id}
          to={item.path}
        >
          <span className="nav-icon">{navIcon(item.id)}</span>
          <span className="nav-label">{item.label}</span>
          {sidebarMode === "expanded" ? <StatusChip status={item.status} /> : null}
        </NavLink>
      ))}
    </nav>
  );
}
