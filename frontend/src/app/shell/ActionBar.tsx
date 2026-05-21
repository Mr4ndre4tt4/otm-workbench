import { Button } from "../../ui/components";
import type { AvailableAction } from "../../platform/types";

export function ActionBar({ actions }: { actions: AvailableAction[] }) {
  return (
    <div className="action-bar">
      {actions.map((action) => (
        <Button disabled={action.disabled} key={action.key} variant={action.variant === "primary" ? "primary" : "secondary"}>
          {action.label}
        </Button>
      ))}
    </div>
  );
}
