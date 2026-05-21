import { StatusChip } from "./primitives";

export type MetricItem = {
  key: string;
  label: string;
  status?: string;
  value: number | string;
};

type MetricGridProps = {
  ariaLabel: string;
  items: MetricItem[];
};

export function MetricGrid({ ariaLabel, items }: MetricGridProps) {
  return (
    <section className="metrics-grid" aria-label={ariaLabel}>
      {items.map((item) => (
        <div className="metric" key={item.key}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
          {item.status ? <StatusChip status={item.status} /> : null}
        </div>
      ))}
    </section>
  );
}
