import { type FormEvent, useState } from "react";

import { ApiError } from "../../platform/api";
import { login } from "../../platform/hooks";
import { useAuth } from "../../platform/useAuth";
import { Button } from "../../ui/components";

export function LoginPanel() {
  const auth = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const response = await login(email, password);
      auth.signIn(response.access_token);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Unable to sign in.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="login-panel" aria-label="Workbench sign in">
      <div>
        <p className="section-label">Backend session</p>
        <h1>Sign in to OTM Workbench</h1>
        <p>Use a backend session so navigation, permissions, preferences, and cockpit data stay API-owned.</p>
      </div>
      <form className="login-form" onSubmit={handleSubmit}>
        <label>
          <span>Email</span>
          <input
            autoComplete="email"
            name="email"
            onChange={(event) => setEmail(event.target.value)}
            required
            type="email"
            value={email}
          />
        </label>
        <label>
          <span>Password</span>
          <input
            autoComplete="current-password"
            name="password"
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
        </label>
        {error ? <p className="form-error">{error}</p> : null}
        <Button disabled={isSubmitting} type="submit" variant="primary">
          {isSubmitting ? "Signing in..." : "Sign in"}
        </Button>
      </form>
    </section>
  );
}
