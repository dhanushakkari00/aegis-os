import { AlertTriangle, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { UrgencyLevel } from "@/lib/types";
import { cn } from "@/lib/utils";

export const urgencyMeta: Record<
  UrgencyLevel,
  { label: string; className: string; iconLabel: string }
> = {
  low: {
    label: "Low",
    className: "border-calm/20 bg-calm/10 text-calm",
    iconLabel: "Level 1"
  },
  moderate: {
    label: "Moderate",
    className: "border-moderate/20 bg-moderate/10 text-moderate",
    iconLabel: "Level 2"
  },
  high: {
    label: "High",
    className: "border-elevated/20 bg-elevated/10 text-elevated",
    iconLabel: "Level 3"
  },
  critical: {
    label: "Critical",
    className: "border-critical/25 bg-critical/10 text-critical",
    iconLabel: "Level 4"
  }
};

export function UrgencyBadge({ urgency }: { urgency: UrgencyLevel }) {
  const meta = urgencyMeta[urgency];
  return (
    <Badge className={cn("font-semibold tracking-[0.25em]", meta.className)}>
      {urgency === "critical" ? (
        <ShieldAlert aria-hidden className="h-3.5 w-3.5" />
      ) : (
        <AlertTriangle aria-hidden className="h-3.5 w-3.5" />
      )}
      {meta.iconLabel} {meta.label}
    </Badge>
  );
}

