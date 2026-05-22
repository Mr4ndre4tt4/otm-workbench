import type { ArtifactListItem, BlockerPanelItem, DetailListItem, MetricItem, ModuleObjectListItem } from "../../ui/components";
import type { AvailableAction, NavigationItem, UserPreferences } from "../../platform/types";

export const syntheticNavigationItems: NavigationItem[] = [
  {
    id: "rates",
    label: "Rates Studio",
    label_key: "module.rates.label",
    description: "Rates workspace",
    path: "/rates",
    status: "ready",
    icon_key: "rates",
    icon_family: "iconly",
    icon_variant: "regular",
    icon_style: "broken",
    icon_name: "Chart",
    icon_light_ref: {},
    icon_dark_ref: {}
  },
  {
    id: "catalog",
    label: "OTM Catalog Core",
    label_key: "module.catalog.label",
    description: "Catalog workspace",
    path: "/catalog",
    status: "ready",
    icon_key: "catalog",
    icon_family: "iconly",
    icon_variant: "regular",
    icon_style: "broken",
    icon_name: "Folder",
    icon_light_ref: {},
    icon_dark_ref: {}
  },
  {
    id: "evidence",
    label: "Evidence Hub",
    label_key: "module.evidence.label",
    description: "Evidence workspace",
    path: "/evidence",
    status: "needs_context",
    icon_key: "evidence",
    icon_family: "iconly",
    icon_variant: "regular",
    icon_style: "broken",
    icon_name: "Shield Done",
    icon_light_ref: {},
    icon_dark_ref: {}
  }
];

export const syntheticUserPreferences: UserPreferences = {
  density: "comfortable",
  follow_system_theme: false,
  sidebar_mode: "expanded",
  theme_mode: "light"
};

export const syntheticCompactDarkPreferences: UserPreferences = {
  density: "compact",
  follow_system_theme: false,
  sidebar_mode: "collapsed",
  theme_mode: "dark"
};

export function syntheticAction(overrides: Partial<AvailableAction> = {}): AvailableAction {
  return {
    disabled: false,
    disabled_reason: null,
    href: "/api/v1/synthetic/action",
    icon_key: "play",
    key: "synthetic_action",
    label: "Run synthetic action",
    method: "POST",
    permission: "synthetic.run",
    requires_confirmation: false,
    result_hint: "refresh_object",
    variant: "primary",
    ...overrides
  };
}

export const syntheticMetricItems: MetricItem[] = [
  { key: "ready", label: "Ready", status: "READY", value: 12 },
  { key: "blocked", label: "Blocked", status: "BLOCKED", value: 2 },
  { key: "empty", label: "Empty", status: "EMPTY", value: 0 }
];

export const syntheticModuleObjects: ModuleObjectListItem[] = [
  {
    id: "synthetic_object_ready",
    meta: ["3 table(s)", "42 row(s)", "0 issue(s)"],
    status: "READY",
    subtitle: "Synthetic scenario",
    title: "Synthetic ready object"
  },
  {
    id: "synthetic_object_blocked",
    meta: ["1 table", "7 row(s)", "2 issue(s)"],
    status: "BLOCKED",
    subtitle: "Long synthetic label for responsive checks",
    title: "Synthetic object with a deliberately long display name"
  }
];

export const syntheticDetailRows: DetailListItem[] = [
  {
    id: "synthetic_detail_required",
    meta: ["Required", "Synthetic metadata"],
    status: "ACTIVE",
    title: "SYNTHETIC_REQUIRED_FIELD"
  },
  {
    id: "synthetic_detail_optional",
    meta: ["Optional", "Missing value allowed"],
    status: "READ_ONLY",
    title: "SYNTHETIC_OPTIONAL_FIELD"
  }
];

export const syntheticArtifactItems: ArtifactListItem[] = [
  {
    id: "synthetic_artifact_downloadable",
    meta: ["text/csv", "128 bytes"],
    subtitle: "CSV export",
    title: "synthetic_export.csv"
  },
  {
    id: "synthetic_evidence_status_only",
    meta: ["Artifact linked", "Client safe"],
    status: "ACTIVE",
    subtitle: "Internal",
    title: "Synthetic validation evidence"
  }
];

export const syntheticBlockers: BlockerPanelItem[] = [
  {
    codes: ["SYNTHETIC_BLOCKER"],
    id: "synthetic_blocker",
    message: "Synthetic blocker message for layout and status checks."
  }
];
