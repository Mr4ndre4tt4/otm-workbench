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
