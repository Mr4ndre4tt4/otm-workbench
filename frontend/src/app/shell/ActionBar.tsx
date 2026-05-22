import { Button } from "../../ui/components";
import { renderIcon } from "../../ui/icons";
import type { AvailableAction } from "../../platform/types";

type ActionBarProps = {
  actions: AvailableAction[];
  onAction?: (action: AvailableAction) => void;
  runningActionKey?: string | null;
};

export function ActionBar({ actions, onAction, runningActionKey = null }: ActionBarProps) {
  return (
    <div className="action-bar">
      {actions.map((action) => (
        <Button
          disabled={action.disabled || runningActionKey === action.key}
          key={action.key}
          onClick={onAction ? () => onAction(action) : undefined}
          title={action.disabled_reason ?? undefined}
          variant={action.variant === "primary" ? "primary" : "secondary"}
        >
          <span className="button-icon" data-icon-key={action.icon_key} data-testid={`action-icon-${action.key}`}>
            {renderIcon(action.icon_key)}
          </span>
          <span>{runningActionKey === action.key ? "Running..." : action.label}</span>
        </Button>
      ))}
    </div>
  );
}
