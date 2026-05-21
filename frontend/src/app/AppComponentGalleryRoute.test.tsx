import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "../platform/auth";

function renderApp(initialPath = "/__gui/component-gallery") {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false }
    }
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={[initialPath]}>
          <App />
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

describe("App internal component gallery route", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
  });

  it("keeps the gallery authenticated but outside backend navigation", async () => {
    const fetchMock = vi.fn(async (input: string | URL, init) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return jsonResponse({ access_token: "session_token", token_type: "bearer" });
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return jsonResponse({
          items: [
            { id: "home", label: "Project Cockpit", path: "/home", status: "ACTIVE" },
            { id: "rates", label: "Rates Studio", path: "/rates", status: "ACTIVE" }
          ],
          total: 2,
          page: 1,
          page_size: 50
        });
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        expect(init?.headers).toMatchObject({ Authorization: "Bearer session_token" });
        return jsonResponse({
          theme_mode: "light",
          follow_system_theme: false,
          density: "comfortable",
          sidebar_mode: "expanded"
        });
      }
      return jsonResponse({ detail: "Unexpected request" }, 404);
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp();
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Component Gallery" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Project Cockpit/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Rates Studio/ })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Component Gallery/ })).not.toBeInTheDocument();
    expect(screen.getByText(/Internal synthetic component gallery for shared GUI patterns/)).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalledWith("/api/v1/platform/project-cockpit/summary", expect.anything());
  });
});
