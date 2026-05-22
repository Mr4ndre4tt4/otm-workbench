import {
  Activity,
  Archive,
  BarChart3,
  Calendar,
  ChevronRight,
  FileText,
  Folder,
  Home,
  Image,
  Settings,
  ShieldCheck,
  Shuffle,
  Upload,
  Wrench
} from "lucide-react";
import { NavLink } from "react-router-dom";

import { isNavigationItemActive } from "../routes/routeUtils";
import { StatusChip } from "../../ui/components";
import type { NavigationItem, UserPreferences } from "../../platform/types";

function navIcon(iconKey: string) {
  if (iconKey === "home") return <Home aria-hidden="true" />;
  if (iconKey === "master_data") return <FileText aria-hidden="true" />;
  if (iconKey === "evidence") return <ShieldCheck aria-hidden="true" />;
  if (iconKey === "rates") return <BarChart3 aria-hidden="true" />;
  if (iconKey === "catalog") return <Folder aria-hidden="true" />;
  if (iconKey === "load_plan") return <Calendar aria-hidden="true" />;
  if (iconKey === "assets") return <Image aria-hidden="true" />;
  if (iconKey === "order_release_generator") return <Upload aria-hidden="true" />;
  if (iconKey === "integration_mapping") return <Shuffle aria-hidden="true" />;
  if (iconKey === "admin") return <Settings aria-hidden="true" />;
  if (iconKey === "dev_tools") return <Wrench aria-hidden="true" />;
  if (iconKey === "activity") return <Activity aria-hidden="true" />;
  if (iconKey === "archive") return <Archive aria-hidden="true" />;
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
          <span className="nav-icon" data-icon-key={item.icon_key} data-testid={`nav-icon-${item.id}`}>
            {navIcon(item.icon_key)}
          </span>
          <span className="nav-label">{item.label}</span>
          {sidebarMode === "expanded" ? <StatusChip status={item.status} /> : null}
        </NavLink>
      ))}
    </nav>
  );
}
