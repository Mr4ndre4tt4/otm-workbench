import { StatusChip } from "./primitives";

export type NextActionPanelAction = {
  description?: string;
  disabled?: boolean;
  disabledReason?: string | null;
  label: string;
  status: string;
};

type NextActionPanelProps = {
  action: NextActionPanelAction;
  ariaLabel: string;
  blockers?: string[];
  context?: string[];
  objectLabel?: string;
  objectValue?: string | null;
  stageLabel?: string;
  title: string;
};

export function NextActionPanel({
  action,
  ariaLabel,
  blockers = [],
  context = [],
  objectLabel = "Object",
  objectValue,
  stageLabel,
  title
}: NextActionPanelProps) {
  const effectiveBlockers = [...blockers, action.disabledReason].filter((item): item is string => Boolean(item));

  return (
    <section className="next-action-panel" aria-label={ariaLabel}>
      <div className="panel-header">
        <h2>{title}</h2>
        <StatusChip status={action.status} />
      </div>
      <div className="next-action-body">
        <div className="next-action-context">
          <span>
            <span>{objectLabel}</span>
            <strong>{objectValue ?? "No object selected"}</strong>
          </span>
          {stageLabel ? (
            <span>
              <span>Stage</span>
              <strong>{stageLabel}</strong>
            </span>
          ) : null}
        </div>
        <div className="next-action-primary">
          <strong>{action.label}</strong>
          {action.description ? <span>{action.description}</span> : null}
        </div>
        {context.length ? (
          <div className="next-action-meta" aria-label={`${ariaLabel} context`}>
            {context.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        ) : null}
        {effectiveBlockers.length ? (
          <div className="next-action-blockers" aria-label={`${ariaLabel} blockers`}>
            {effectiveBlockers.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}
