import { ClipboardCheck } from "lucide-react";

import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function HandoffSummaryCard({
  summary,
  disclaimers
}: {
  summary?: string | null;
  disclaimers?: string[];
}) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>Handoff Summary</CardTitle>
          <CardDescription>Condensed and structured for the next responder.</CardDescription>
        </div>
        <div className="rounded-2xl border border-cyan/20 bg-cyan/10 p-3 text-cyan">
          <ClipboardCheck className="h-5 w-5" />
        </div>
      </CardHeader>
      <p className="text-base leading-7 text-slate-100">
        {summary ?? "No summary is available yet."}
      </p>
      {disclaimers?.length ? (
        <div className="mt-5 space-y-2 rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Disclaimers</p>
          {disclaimers.map((item) => (
            <p key={item} className="text-sm text-slate-300">
              {item}
            </p>
          ))}
        </div>
      ) : null}
    </Card>
  );
}

