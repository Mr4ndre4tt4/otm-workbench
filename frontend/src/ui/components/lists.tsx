import type { ReactNode } from "react";

import { StatusChip } from "./primitives";

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
  maxVisibleItems?: number;
  onSelect: (id: string) => void;
  selectedId: string | null;
};

function limitedItems<T extends { id: string }>(items: T[], maxVisibleItems?: number, selectedId?: string | null) {
  if (!maxVisibleItems || items.length <= maxVisibleItems) {
    return { items, selectedPinned: false };
  }
  const visible = items.slice(0, maxVisibleItems);
  if (!selectedId || visible.some((item) => item.id === selectedId)) {
    return { items: visible, selectedPinned: false };
  }
  const selected = items.find((item) => item.id === selectedId);
  if (!selected) {
    return { items: visible, selectedPinned: false };
  }
  return { items: [...items.slice(0, Math.max(maxVisibleItems - 1, 0)), selected], selectedPinned: true };
}

export function ModuleObjectList({
  ariaLabel,
  emptyText = "No objects available.",
  items,
  maxVisibleItems,
  onSelect,
  selectedId
}: ModuleObjectListProps) {
  if (!items.length) {
    return <p className="empty-text">{emptyText}</p>;
  }

  const visible = limitedItems(items, maxVisibleItems, selectedId);

  return (
    <div className="module-list" aria-label={ariaLabel}>
      {visible.items.map((item) => (
        <button
          aria-pressed={item.id === selectedId}
          className={item.id === selectedId ? "module-row module-row-selected" : "module-row"}
          key={item.id}
          onClick={() => onSelect(item.id)}
          type="button"
        >
          <div>
            <strong title={item.title}>{item.title}</strong>
            {item.subtitle ? <span title={item.subtitle}>{item.subtitle}</span> : null}
          </div>
          {item.meta.map((value, index) => (
            <span key={`${item.id}-${index}`} title={String(value)}>
              {value}
            </span>
          ))}
          <StatusChip status={item.status} />
        </button>
      ))}
      {visible.items.length < items.length ? (
        <p className="list-density-summary">
          Showing {visible.items.length} of {items.length}
          {visible.selectedPinned ? "; selected item pinned" : ""}
        </p>
      ) : null}
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
          <strong className="table-list-main">{item.title}</strong>
          <div className="table-list-meta">
            {item.meta.map((value, index) => (
              <span key={`${item.id}-${index}`}>{value}</span>
            ))}
          </div>
          <div className="table-list-status">{item.status ? <StatusChip status={item.status} /> : null}</div>
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
  maxVisibleItems?: number;
};

export function ArtifactList({ items, maxVisibleItems }: ArtifactListProps) {
  const visible = limitedItems(items, maxVisibleItems);

  return (
    <div className="artifact-list">
      {visible.items.map((item) => (
        <div className="artifact-list-item" key={item.id}>
          <div className="artifact-list-main">
            <strong title={item.title}>{item.title}</strong>
            <span title={item.subtitle}>{item.subtitle}</span>
          </div>
          <div className="artifact-list-meta">
            {item.meta.map((value, index) => (
              <span key={`${item.id}-${index}`} title={String(value)}>
                {value}
              </span>
            ))}
          </div>
          <div className="artifact-list-action">{item.action ?? (item.status ? <StatusChip status={item.status} /> : null)}</div>
        </div>
      ))}
      {visible.items.length < items.length ? (
        <p className="list-density-summary">
          Showing {visible.items.length} of {items.length}
        </p>
      ) : null}
    </div>
  );
}
