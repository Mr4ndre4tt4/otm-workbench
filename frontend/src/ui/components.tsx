import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type ButtonProps = PropsWithChildren<
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: "primary" | "secondary";
  }
>;

export function Button({ children, className = "", variant = "secondary", ...props }: ButtonProps) {
  return (
    <button className={`button button-${variant} ${className}`.trim()} type={props.type ?? "button"} {...props}>
      {children}
    </button>
  );
}

export function IconButton({
  children,
  className = "",
  label,
  ...props
}: PropsWithChildren<ButtonHTMLAttributes<HTMLButtonElement> & { label: string }>) {
  return (
    <button className={`icon-button ${className}`.trim()} aria-label={label} title={label} type="button" {...props}>
      {children}
    </button>
  );
}

export function StatusChip({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  return <span className={`status-chip status-${normalized}`}>{status.replaceAll("_", " ")}</span>;
}

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

type OperationalPanelProps = PropsWithChildren<{
  className?: string;
  emptyText: string;
  hasItems: boolean;
  isLoading?: boolean;
  loadingText?: string;
  status: string;
  title: string;
}>;

export function OperationalPanel({
  children,
  className = "",
  emptyText,
  hasItems,
  isLoading = false,
  loadingText = "Loading...",
  status,
  title
}: OperationalPanelProps) {
  return (
    <div className={`panel ${className}`.trim()}>
      <div className="panel-header">
        <h2>{title}</h2>
        <StatusChip status={status} />
      </div>
      {isLoading ? (
        <p className="empty-text">{loadingText}</p>
      ) : hasItems ? (
        children
      ) : (
        <p className="empty-text">{emptyText}</p>
      )}
    </div>
  );
}
