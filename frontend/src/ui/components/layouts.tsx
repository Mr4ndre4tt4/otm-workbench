import type { PropsWithChildren, ReactNode } from "react";

import { StatusChip } from "./primitives";

type ModuleWorkspaceLayoutProps = PropsWithChildren<{
  ariaLabel: string;
  side: ReactNode;
  status: string;
  title: string;
}>;

export function ModuleWorkspaceLayout({ ariaLabel, children, side, status, title }: ModuleWorkspaceLayoutProps) {
  return (
    <section className={side ? "module-template" : "module-template module-template-single"} aria-label={ariaLabel}>
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
