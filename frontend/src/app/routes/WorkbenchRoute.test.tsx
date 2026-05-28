import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { WorkbenchRoute } from "./WorkbenchRoute";
import type { NavigationItem } from "../../platform/types";

const activeNavigationItems: NavigationItem[] = [
  {
    id: "home",
    label: "Project Cockpit",
    label_key: "module.home.label",
    description: "Project overview",
    path: "/home",
    status: "ACTIVE",
    icon_key: "home",
    icon_family: "iconly",
    icon_variant: "regular",
    icon_style: "broken",
    icon_name: "Home",
    icon_light_ref: {},
    icon_dark_ref: {}
  },
  {
    id: "rates",
    label: "Rates Studio",
    label_key: "module.rates.label",
    description: "Rates workspace",
    path: "/rates",
    status: "ACTIVE",
    icon_key: "rates",
    icon_family: "iconly",
    icon_variant: "regular",
    icon_style: "broken",
    icon_name: "Chart",
    icon_light_ref: {},
    icon_dark_ref: {}
  },
  {
    id: "settings",
    label: "Settings",
    label_key: "module.settings.label",
    description: "Settings workspace",
    path: "/settings",
    status: "ACTIVE",
    icon_key: "settings",
    icon_family: "iconly",
    icon_variant: "regular",
    icon_style: "broken",
    icon_name: "Setting",
    icon_light_ref: {},
    icon_dark_ref: {}
  }
];

function renderRoute(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <WorkbenchRoute items={activeNavigationItems} token="session_token" />
    </MemoryRouter>
  );
}

describe("WorkbenchRoute", () => {
  it.each(["/catalog", "/evidence", "/admin", "/dev-tools", "/dev-tools/data-dictionary"])(
    "keeps excluded route %s unavailable unless backend navigation returns it",
    (path) => {
      renderRoute(path);

      expect(screen.getByRole("heading", { name: "Module unavailable" })).toBeInTheDocument();
      expect(screen.getByText("Use the backend-owned navigation menu to open an available module.")).toBeInTheDocument();
      expect(screen.getByRole("link", { name: "Return to Cockpit" })).toHaveAttribute("href", "/home");
    }
  );
});
