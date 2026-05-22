import {
  Activity,
  Archive,
  BadgeCheck,
  BarChart3,
  Calendar,
  Check,
  CheckCircle,
  ChevronRight,
  Download,
  FileCheck,
  FileText,
  Folder,
  Home,
  Image,
  Play,
  Plus,
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
  "badge-check": BadgeCheck,
  catalog: Folder,
  check: Check,
  "check-circle": CheckCircle,
  context: Settings,
  dev_tools: Wrench,
  download: Download,
  evidence: ShieldCheck,
  "file-check": FileCheck,
  home: Home,
  integration_mapping: Shuffle,
  load_plan: Calendar,
  master_data: FileText,
  order_release_generator: Upload,
  play: Play,
  plus: Plus,
  rates: BarChart3
};

export function renderIcon(iconKey: string) {
  const Icon = approvedIcons[iconKey] ?? ChevronRight;
  return <Icon aria-hidden="true" />;
}
