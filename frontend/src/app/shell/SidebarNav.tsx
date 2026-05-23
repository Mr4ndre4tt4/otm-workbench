import { NavLink } from "react-router-dom";

import { isNavigationItemActive } from "../routes/routeUtils";
import { renderIcon } from "../../ui/icons";
import type { NavigationItem } from "../../platform/types";

export function SidebarNav({
  currentPath,
  items
}: {
  currentPath: string;
  items: NavigationItem[];
}) {
  return (
    <nav className="sidebar-nav" aria-label="Workbench modules">
      {items.map((item) => (
        <NavLink
          className={isNavigationItemActive(item, currentPath) ? "nav-item nav-item-active" : "nav-item"}
          key={item.id}
          to={item.path}
        >
          <span className="nav-icon" data-icon-key={item.icon_key} data-testid={`nav-icon-${item.id}`}>
            {renderIcon(item.icon_key)}
          </span>
          <span className="nav-label">{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
