import { AlertCircle } from "lucide-react";
import type { ReactNode } from "react";

type StatePanelProps = {
  children: ReactNode;
  tone?: "default" | "error";
};

export function StatePanel({ children, tone = "default" }: StatePanelProps) {
  return (
    <section className={tone === "error" ? "state-panel state-panel-error" : "state-panel"}>
      {tone === "error" ? <AlertCircle aria-hidden="true" /> : null}
      <span>{children}</span>
    </section>
  );
}

type FeedbackMessageProps = {
  children: ReactNode;
  tone: "error" | "success";
};

export function FeedbackMessage({ children, tone }: FeedbackMessageProps) {
  return <p className={tone === "success" ? "form-success" : "form-error"}>{children}</p>;
}
