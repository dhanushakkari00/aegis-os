import { ArrowRight, Siren } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { RecommendedActionItem } from "@/lib/types";

export function RecommendationCard({ action }: { action: RecommendedActionItem }) {
  return (
    <Card className="flex h-full flex-col gap-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
            Priority {action.priority}
          </p>
          <h4 className="mt-2 font-display text-xl font-semibold text-white">{action.title}</h4>
        </div>
        <div className="rounded-2xl border border-cyan/20 bg-cyan/10 p-3 text-cyan">
          <Siren className="h-5 w-5" />
        </div>
      </div>
      <p className="text-sm leading-6 text-slate-200">{action.description}</p>
      <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
        <span className="font-medium text-white">Why this matters:</span> {action.rationale}
      </div>
      <div className="mt-auto flex items-center gap-2 text-xs uppercase tracking-[0.24em] text-cyan">
        <ArrowRight className="h-3.5 w-3.5" />
        {action.category}
        {action.is_immediate ? " | Immediate" : " | Planned"}
      </div>
    </Card>
  );
}

