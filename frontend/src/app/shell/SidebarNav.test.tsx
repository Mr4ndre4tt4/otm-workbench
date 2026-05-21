import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { SidebarNav } from "./SidebarNav";

const navigationItems = [
  { id: "home", label: "Project Cockpit", path: "/home", status: "ACTIVE" },
  { id: "rates", label: "Rates Studio", path: "/rates", status: "PLANNED" }
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
