import { Monitor, Moon, Rows3, Sun } from "lucide-react";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { ApiError } from "../../platform/api";
import { updateUserPreferences } from "../../platform/hooks";
import type { UserPreferences } from "../../platform/types";
import { IconButton } from "../../ui/components";

export function PreferenceControls({
  preferences,
  token
}: {
  preferences: UserPreferences | undefined;
  token: string | null;
}) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const currentMode = preferences?.theme_mode ?? "light";
  const currentDensity = preferences?.density ?? "comfortable";

  async function applyPreferences(nextValues: Partial<UserPreferences>) {
    if (!token || isSaving) return;
    setError(null);
    setIsSaving(true);
    const nextPreferences: UserPreferences = {
      theme_mode: preferences?.theme_mode ?? "light",
      follow_system_theme: preferences?.follow_system_theme ?? false,
      density: preferences?.density ?? "comfortable",
      sidebar_mode: preferences?.sidebar_mode ?? "expanded",
      ...nextValues
    };
    if (nextPreferences.theme_mode === "system") {
      nextPreferences.follow_system_theme = true;
    }
    if (nextPreferences.theme_mode !== "system") {
      nextPreferences.follow_system_theme = false;
    }
    try {
      await updateUserPreferences(token, nextPreferences);
      queryClient.setQueryData(["platform", "user-preferences"], nextPreferences);
      await queryClient.invalidateQueries({ queryKey: ["platform", "user-preferences"] });
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Unable to update preference.");
      }
    } finally {
      setIsSaving(false);
    }
  }

  const controlsDisabled = !token || isSaving;

  return (
    <div className="preference-controls" aria-label="Workbench preferences">
      <IconButton
        aria-pressed={currentMode === "light"}
        className={currentMode === "light" ? "icon-button-active" : ""}
        disabled={controlsDisabled}
        label="Use light mode"
        onClick={() => void applyPreferences({ theme_mode: "light" })}
      >
        <Sun aria-hidden="true" />
      </IconButton>
      <IconButton
        aria-pressed={currentMode === "dark"}
        className={currentMode === "dark" ? "icon-button-active" : ""}
        disabled={controlsDisabled}
        label="Use dark mode"
        onClick={() => void applyPreferences({ theme_mode: "dark" })}
      >
        <Moon aria-hidden="true" />
      </IconButton>
      <IconButton
        aria-pressed={currentMode === "system"}
        className={currentMode === "system" ? "icon-button-active" : ""}
        disabled={controlsDisabled}
        label="Follow system theme"
        onClick={() => void applyPreferences({ theme_mode: "system" })}
      >
        <Monitor aria-hidden="true" />
      </IconButton>
      <IconButton
        aria-pressed={currentDensity === "compact"}
        className={currentDensity === "compact" ? "icon-button-active" : ""}
        disabled={controlsDisabled}
        label={currentDensity === "compact" ? "Use comfortable density" : "Use compact density"}
        onClick={() =>
          void applyPreferences({ density: currentDensity === "compact" ? "comfortable" : "compact" })
        }
      >
        <Rows3 aria-hidden="true" />
      </IconButton>
      {error ? <span className="preference-error">{error}</span> : null}
    </div>
  );
}
