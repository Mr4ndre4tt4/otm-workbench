import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { SidebarNav } from "./SidebarNav";

const navigationItems = [
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
    status: "PLANNED",
    icon_key: "chart",
    icon_family: "iconly",
    icon_variant: "regular",
    icon_style: "broken",
    icon_name: "Chart",
    icon_light_ref: {},
    icon_dark_ref: {}
  }
];

describe("SidebarNav", () => {
  it("renders backend navigation with status chips while expanded", () => {
    render(
      <MemoryRouter>
        <SidebarNav currentPath="/rates" items={navigationItems} sidebarMode="expanded" />
      </MemoryRouter>
    );

    expect(screen.getByRole("navigation", { name: "Workbench modules" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Project Cockpit/ })).toHaveAttribute("href", "/home");
    expect(screen.getByRole("link", { name: /Rates Studio/ })).toHaveClass("nav-item-active");
    expect(screen.getByText("ACTIVE")).toBeInTheDocument();
    expect(screen.getByText("PLANNED")).toBeInTheDocument();
  });

  it("renders icons from backend-owned icon keys instead of module ids", () => {
    render(
      <MemoryRouter>
        <SidebarNav currentPath="/rates" items={navigationItems} sidebarMode="expanded" />
      </MemoryRouter>
    );

    expect(screen.getByTestId("nav-icon-home")).toHaveAttribute("data-icon-key", "home");
    expect(screen.getByTestId("nav-icon-rates")).toHaveAttribute("data-icon-key", "chart");
  });

  it("keeps collapsed navigation icon-first without duplicating status chips", () => {
    render(
      <MemoryRouter>
        <SidebarNav currentPath="/rates" items={navigationItems} sidebarMode="collapsed" />
      </MemoryRouter>
    );

    expect(screen.getByRole("link", { name: /Project Cockpit/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Rates Studio/ })).toHaveClass("nav-item-active");
    expect(screen.queryByText("ACTIVE")).not.toBeInTheDocument();
    expect(screen.queryByText("PLANNED")).not.toBeInTheDocument();
  });
});
