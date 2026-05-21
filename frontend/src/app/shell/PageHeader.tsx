import type { AvailableAction } from "../../platform/types";
import { ActionBar } from "./ActionBar";

export function PageHeader({
  actions,
  description,
  label,
  title
}: {
  actions?: AvailableAction[];
  description: string;
  label: string;
  title: string;
}) {
  return (
    <header className="page-header">
      <div>
        <p className="section-label">{label}</p>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {actions ? <ActionBar actions={actions} /> : null}
    </header>
  );
}
