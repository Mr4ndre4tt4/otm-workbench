import type { ButtonHTMLAttributes, PropsWithChildren, ReactNode } from "react";

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

export type ModuleObjectListItem = {
  id: string;
  meta: Array<number | string>;
  status: string;
  subtitle?: string;
  title: string;
};

type ModuleObjectListProps = {
  emptyText?: string;
  items: ModuleObjectListItem[];
  onSelect: (id: string) => void;
  selectedId: string | null;
};

export function ModuleObjectList({
  emptyText = "No objects available.",
  items,
  onSelect,
  selectedId
}: ModuleObjectListProps) {
  if (!items.length) {
    return <p className="empty-text">{emptyText}</p>;
  }

  return (
    <div className="module-list">
      {items.map((item) => (
        <button
          aria-pressed={item.id === selectedId}
          className={item.id === selectedId ? "module-row module-row-selected" : "module-row"}
          key={item.id}
          onClick={() => onSelect(item.id)}
          type="button"
        >
          <div>
            <strong>{item.title}</strong>
            {item.subtitle ? <span>{item.subtitle}</span> : null}
          </div>
          {item.meta.map((value, index) => (
            <span key={`${item.id}-${index}`}>{value}</span>
          ))}
          <StatusChip status={item.status} />
        </button>
      ))}
    </div>
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

export type SelectedObjectField = {
  label: string;
  value: number | string;
};

type SelectedObjectPanelProps = PropsWithChildren<{
  actions?: ReactNode;
  emptyText: string;
  fields?: SelectedObjectField[];
  isLoading?: boolean;
  loadingText?: string;
  status: string;
  subtitle?: string;
  title?: string;
}>;

export function SelectedObjectPanel({
  actions,
  children,
  emptyText,
  fields = [],
  isLoading = false,
  loadingText = "Loading selected object...",
  status,
  subtitle,
  title
}: SelectedObjectPanelProps) {
  return (
    <aside className="module-template-side">
      <div className="panel-header">
        <h2>Selected object</h2>
        <StatusChip status={status} />
      </div>
      {isLoading ? (
        <p className="empty-text">{loadingText}</p>
      ) : title ? (
        <div className="detail-stack">
          <div>
            <strong>{title}</strong>
            {subtitle ? <span>{subtitle}</span> : null}
          </div>
          {fields.length ? (
            <div className="detail-grid">
              {fields.map((field) => (
                <span className="detail-field" key={field.label}>
                  <span>{field.label}</span>
                  <strong>{field.value}</strong>
                </span>
              ))}
            </div>
          ) : null}
          {actions ? (
            <div className="detail-actions" aria-label="Selected object actions">
              {actions}
            </div>
          ) : null}
          {children}
        </div>
      ) : (
        <p className="empty-text">{emptyText}</p>
      )}
    </aside>
  );
}
