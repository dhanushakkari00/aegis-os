import { Activity, Clock3, FileClock, UploadCloud } from "lucide-react";

import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatTimestamp } from "@/lib/utils";

type TimelineEntry = {
  title: string;
  description: string;
  timestamp?: string;
  type: "ingest" | "artifact" | "analysis";
};

const iconByType = {
  ingest: Clock3,
  artifact: UploadCloud,
  analysis: Activity
};

export function TimelinePanel({ entries }: { entries: TimelineEntry[] }) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>Operational Timeline</CardTitle>
          <CardDescription>Each case action is visible in time order.</CardDescription>
        </div>
        <FileClock className="h-5 w-5 text-cyan" />
      </CardHeader>
      <ol className="space-y-4">
        {entries.map((entry) => {
          const Icon = iconByType[entry.type];
          return (
            <li
              key={`${entry.title}-${entry.timestamp}`}
              className="flex gap-4 rounded-2xl border border-white/10 bg-white/5 p-4"
            >
              <div className="mt-1 rounded-2xl border border-white/10 bg-white/5 p-2">
                <Icon className="h-4 w-4 text-cyan" />
              </div>
              <div>
                <p className="font-medium text-white">{entry.title}</p>
                <p className="text-sm text-slate-300">{entry.description}</p>
                <p className="mt-1 text-xs uppercase tracking-[0.24em] text-slate-400">
                  {formatTimestamp(entry.timestamp)}
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </Card>
  );
}

