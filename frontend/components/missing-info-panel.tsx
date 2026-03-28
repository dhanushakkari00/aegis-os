import { HelpCircle } from "lucide-react";

import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { MissingInformationItem } from "@/lib/types";

export function MissingInfoPanel({ items }: { items: MissingInformationItem[] }) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>Missing Critical Information</CardTitle>
          <CardDescription>Gaps are surfaced so the next operator knows what to clarify.</CardDescription>
        </div>
      </CardHeader>
      <div className="space-y-3">
        {items.length ? (
          items.map((item) => (
            <div
              key={`${item.item}-${item.reason}`}
              className="rounded-2xl border border-white/10 bg-white/5 p-4"
            >
              <div className="flex items-start gap-3">
                <HelpCircle className="mt-0.5 h-4 w-4 text-signal" />
                <div>
                  <p className="font-medium text-white">{item.item}</p>
                  <p className="text-sm text-slate-300">{item.reason}</p>
                  <p className="mt-2 text-xs uppercase tracking-[0.24em] text-slate-400">
                    Criticality {item.criticality}
                  </p>
                </div>
              </div>
            </div>
          ))
        ) : (
          <p className="rounded-2xl border border-calm/20 bg-calm/10 p-4 text-sm text-calm">
            No high-priority gaps surfaced for this intake.
          </p>
        )}
      </div>
    </Card>
  );
}

