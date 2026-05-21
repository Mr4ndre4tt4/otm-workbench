import { StatusChip } from "./primitives";

type ActivityRowProps = {
  status?: string;
  subtitle: string;
  title: string;
};

export function ActivityRow({ status, subtitle, title }: ActivityRowProps) {
  return (
    <div className="activity-row">
      <strong>{title}</strong>
      <span>{subtitle}</span>
      {status ? <StatusChip status={status} /> : null}
    </div>
  );
}
