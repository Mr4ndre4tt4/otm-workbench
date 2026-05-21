import { AlertCircle, CheckCircle2 } from "lucide-react";

import type { SetupStatus } from "../../platform/types";

type ReadinessPanelProps = {
  setupStatus: SetupStatus | null;
  status: "ready" | "needs_context";
};

export function ReadinessPanel({ setupStatus, status }: ReadinessPanelProps) {
  const isReady = status === "ready";
  return (
    <section className={isReady ? "readiness readiness-ready" : "readiness"}>
      {isReady ? <CheckCircle2 aria-hidden="true" /> : <AlertCircle aria-hidden="true" />}
      <div>
        <strong>{isReady ? "Project context ready" : "Select an active project context"}</strong>
        <span>
          {setupStatus
            ? `${setupStatus.profile_count} profile(s), ${setupStatus.environment_count} environment(s)`
            : "The shell is waiting for project, profile, and environment context."}
        </span>
      </div>
    </section>
  );
}
