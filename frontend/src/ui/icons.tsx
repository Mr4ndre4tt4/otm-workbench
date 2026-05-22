import {
  Activity,
  Archive,
  BarChart3,
  Calendar,
  ChevronRight,
  FileText,
  Folder,
  Home,
  Image,
  Settings,
  ShieldCheck,
  Shuffle,
  Upload,
  Wrench,
  type LucideIcon
} from "lucide-react";

const approvedIcons: Record<string, LucideIcon> = {
  activity: Activity,
  admin: Settings,
  archive: Archive,
  assets: Image,
  catalog: Folder,
  dev_tools: Wrench,
  evidence: ShieldCheck,
  home: Home,
  integration_mapping: Shuffle,
  load_plan: Calendar,
  master_data: FileText,
  order_release_generator: Upload,
  rates: BarChart3
};

export function renderIcon(iconKey: string) {
  const Icon = approvedIcons[iconKey] ?? ChevronRight;
  return <Icon aria-hidden="true" />;
}
