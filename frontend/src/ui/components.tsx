import { AlertCircle } from "lucide-react";
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
  ariaLabel: string;
  emptyText?: string;
  items: ModuleObjectListItem[];
  onSelect: (id: string) => void;
  selectedId: string | null;
};

export function ModuleObjectList({
  ariaLabel,
  emptyText = "No objects available.",
  items,
  onSelect,
  selectedId
}: ModuleObjectListProps) {
  if (!items.length) {
    return <p className="empty-text">{emptyText}</p>;
  }

  return (
    <div className="module-list" aria-label={ariaLabel}>
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

export type DetailListItem = {
  id: string;
  meta: Array<number | string>;
  status?: string;
  title: string;
};

type DetailListProps = {
  ariaLabel: string;
  emptyText?: string;
  items: DetailListItem[];
};

export function DetailList({ ariaLabel, emptyText = "No detail rows available.", items }: DetailListProps) {
  if (!items.length) {
    return <p className="empty-text">{emptyText}</p>;
  }

  return (
    <div className="table-list" aria-label={ariaLabel}>
      {items.map((item) => (
        <div className="table-list-item" key={item.id}>
          <strong>{item.title}</strong>
          {item.meta.map((value, index) => (
            <span key={`${item.id}-${index}`}>{value}</span>
          ))}
          {item.status ? <StatusChip status={item.status} /> : null}
        </div>
      ))}
    </div>
  );
}

export type ArtifactListItem = {
  action?: ReactNode;
  id: string;
  meta: Array<number | string>;
  status?: string;
  subtitle: string;
  title: string;
};

type ArtifactListProps = {
  items: ArtifactListItem[];
};

export function ArtifactList({ items }: ArtifactListProps) {
  return (
    <div className="artifact-list">
      {items.map((item) => (
        <div className="artifact-list-item" key={item.id}>
          <div>
            <strong>{item.title}</strong>
            <span>{item.subtitle}</span>
          </div>
          {item.meta.map((value, index) => (
            <span key={`${item.id}-${index}`}>{value}</span>
          ))}
          {item.action ?? (item.status ? <StatusChip status={item.status} /> : null)}
        </div>
      ))}
    </div>
  );
}

type ModuleWorkspaceLayoutProps = PropsWithChildren<{
  ariaLabel: string;
  side: ReactNode;
  status: string;
  title: string;
}>;

export function ModuleWorkspaceLayout({ ariaLabel, children, side, status, title }: ModuleWorkspaceLayoutProps) {
  return (
    <section className="module-template" aria-label={ariaLabel}>
      <div className="module-template-main">
        <div className="panel-header">
          <h2>{title}</h2>
          <StatusChip status={status} />
        </div>
        {children}
      </div>
      {side}
    </section>
  );
}

type ModuleWorkspaceSideProps = PropsWithChildren<{
  ariaLabel?: string;
  title: string;
}>;

export function ModuleWorkspaceSide({ ariaLabel, children, title }: ModuleWorkspaceSideProps) {
  return (
    <aside className="module-template-side" aria-label={ariaLabel}>
      <h2>{title}</h2>
      {children}
    </aside>
  );
}

export type BlockerPanelItem = {
  codes: string[];
  id: string;
  message: string;
};

type BlockerPanelProps = {
  emptyText: string;
  items: BlockerPanelItem[];
  title: string;
};

export function BlockerPanel({ emptyText, items, title }: BlockerPanelProps) {
  return (
    <section className="panel blockers-panel">
      <div className="panel-header">
        <h2>{title}</h2>
        <StatusChip status={items.length ? "BLOCKED" : "READY"} />
      </div>
      {items.length ? (
        <div className="blocker-list">
          {items.map((item) => (
            <div className="blocker-item" key={item.id}>
              <strong>{item.codes.join(", ")}</strong>
              <span>{item.message}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="empty-text">{emptyText}</p>
      )}
    </section>
  );
}

type OperationalPanelProps = PropsWithChildren<{
  ariaLabel: string;
  className?: string;
  emptyText: string;
  hasItems: boolean;
  isLoading?: boolean;
  loadingText?: string;
  status: string;
  title: string;
}>;

export function OperationalPanel({
  ariaLabel,
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
    <div className={`panel ${className}`.trim()} aria-label={ariaLabel}>
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
  ariaLabel: string;
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
  ariaLabel,
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
    <aside className="module-template-side" aria-label={ariaLabel}>
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
