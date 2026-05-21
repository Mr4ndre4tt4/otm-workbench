import type { PropsWithChildren, ReactNode } from "react";

import { StatusChip } from "./primitives";

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
