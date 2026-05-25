import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../../platform/auth";
import { LoginPanel } from "./LoginPanel";

describe("LoginPanel", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    sessionStorage.clear();
  });

  it("signs in through the backend session endpoint", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ access_token: "session_token", token_type: "bearer" }), {
        headers: { "Content-Type": "application/json" },
        status: 200
      })
    );

    render(
      <AuthProvider>
        <LoginPanel />
      </AuthProvider>
    );

    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(sessionStorage.getItem("otm_workbench.session_token")).toBe("session_token");
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/platform/session/login",
      expect.objectContaining({
        body: JSON.stringify({
          email: "synthetic.user@example.test",
          password: "SyntheticPass123!"
        }),
        method: "POST"
      })
    );
  });

  it("renders backend auth errors inside the shell-owned login pattern", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ code: "AUTH_FAILED", message: "Invalid credentials." }), {
        headers: { "Content-Type": "application/json" },
        status: 401
      })
    );

    render(
      <AuthProvider>
        <LoginPanel />
      </AuthProvider>
    );

    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "bad-password");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Invalid credentials.")).toBeInTheDocument();
    expect(sessionStorage.getItem("otm_workbench.session_token")).toBeNull();
  });

  it("clears stale auth errors when the user edits the login draft", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ code: "AUTH_FAILED", message: "Invalid credentials." }), {
        headers: { "Content-Type": "application/json" },
        status: 401
      })
    );

    render(
      <AuthProvider>
        <LoginPanel />
      </AuthProvider>
    );

    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.test");
    await userEvent.type(screen.getByLabelText("Password"), "bad-password");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Invalid credentials.")).toBeInTheDocument();

    await userEvent.clear(screen.getByLabelText("Password"));
    await userEvent.type(screen.getByLabelText("Password"), "SyntheticPass123!");

    expect(screen.queryByText("Invalid credentials.")).not.toBeInTheDocument();
  });
});
