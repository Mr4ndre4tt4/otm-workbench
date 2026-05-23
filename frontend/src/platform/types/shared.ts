export type PageResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type AvailableAction = {
  key: string;
  label: string;
  method: string;
  href: string;
  variant: string;
  icon_key: string;
  disabled: boolean;
  disabled_reason: string | null;
  recommended?: boolean;
  requires_confirmation: boolean;
  permission?: string | null;
  result_hint?: "download" | "refresh_list" | "refresh_object" | string | null;
};

export type ModuleCount = {
  key: string;
  label: string;
  value: number;
  severity: "neutral" | "success" | "warning" | "danger";
};

export type ModuleBlocker = {
  object_id: string;
  object_type: string;
  severity: string;
  codes: string[];
  message: string;
};
