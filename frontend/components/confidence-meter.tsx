import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { clamp } from "@/lib/utils";

export function ConfidenceMeter({ confidence }: { confidence: number }) {
  const normalized = clamp(confidence);
  const percentage = Math.round(normalized * 100);

  return (
    <Card>
      <CardHeader className="mb-4">
        <div>
          <CardTitle>Confidence</CardTitle>
          <CardDescription>Model certainty is shown explicitly and never treated as fact.</CardDescription>
        </div>
        <div className="font-display text-3xl font-semibold text-white">{percentage}%</div>
      </CardHeader>
      <div
        aria-label={`Confidence ${percentage}%`}
        aria-valuemax={100}
        aria-valuemin={0}
        aria-valuenow={percentage}
        role="progressbar"
        className="h-4 rounded-full border border-white/10 bg-white/5"
      >
        <div
          className="h-full rounded-full bg-[linear-gradient(90deg,rgba(78,232,255,0.85),rgba(108,242,180,0.85))]"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="mt-3 text-xs uppercase tracking-[0.24em] text-slate-400">
        Confidence is separate from severity.
      </p>
    </Card>
  );
}

