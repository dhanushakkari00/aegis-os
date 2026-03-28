import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { UrgencyBadge } from "@/components/urgency-badge";
import type { QueueCase } from "@/lib/types";
import { formatTimestamp } from "@/lib/utils";

export function CaseQueueCard({ cases }: { cases: QueueCase[] }) {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Case Queue</CardTitle>
          <CardDescription>Recent intakes ordered for rapid routing.</CardDescription>
        </div>
      </CardHeader>
      <div className="space-y-3">
        {cases.map((caseItem) => (
          <Link
            key={caseItem.id}
            href={`/cases/${caseItem.id}`}
            className="flex items-center justify-between gap-4 rounded-2xl border border-white/10 bg-white/5 p-4 transition hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan/70"
          >
            <div className="min-w-0">
              <p className="truncate font-medium text-white">{caseItem.handoff_summary ?? caseItem.id}</p>
              <p className="mt-1 text-xs uppercase tracking-[0.24em] text-slate-400">
                {caseItem.mode.replaceAll("_", " ")} | {formatTimestamp(caseItem.created_at)}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <UrgencyBadge urgency={caseItem.urgency_level} />
              <ArrowUpRight className="h-4 w-4 text-slate-400" />
            </div>
          </Link>
        ))}
      </div>
    </Card>
  );
}

