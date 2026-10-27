import { CheckCircle2, Clock, Loader2, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { BacktestStatus } from "@/types/api";

const config: Record<BacktestStatus, { label: string; variant: "success" | "secondary" | "destructive"; icon: typeof Clock }> = {
  pending: { label: "Pending", variant: "secondary", icon: Clock },
  running: { label: "Running", variant: "secondary", icon: Loader2 },
  completed: { label: "Completed", variant: "success", icon: CheckCircle2 },
  failed: { label: "Failed", variant: "destructive", icon: XCircle },
};

export function BacktestStatusBadge({ status }: { status: BacktestStatus }) {
  const { label, variant, icon: Icon } = config[status];
  return (
    <Badge variant={variant}>
      <Icon className={Icon === Loader2 ? "h-3 w-3 animate-spin" : "h-3 w-3"} />
      {label}
    </Badge>
  );
}
