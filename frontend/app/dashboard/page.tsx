"use client";

import { useEffect, useState } from "react";

import { CaseQueueCard } from "@/components/case-queue-card";
import { IncidentMapCard } from "@/components/incident-map-card";
import { SeverityDistributionCard } from "@/components/severity-distribution-card";
import { Card } from "@/components/ui/card";
import { getDashboardIncidentMapUrl, getDashboardSummary } from "@/lib/api";
import type { DashboardSummary } from "@/lib/types";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void getDashboardSummary()
      .then((payload) => {
        setSummary(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Unable to load dashboard.");
      });
  }, []);

  return (
    <div className="space-y-8" aria-live="polite">
      <section className="rounded-[32px] border border-white/10 bg-white/5 p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-cyan">Operations dashboard</p>
        <h2 className="mt-3 font-display text-4xl font-semibold text-white">
          Command visibility across active cases
        </h2>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {summary?.totals.map((metric) => (
          <Card key={metric.label} className="p-6">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">{metric.label}</p>
            <p className="mt-4 font-display text-5xl font-semibold text-white">{metric.value}</p>
          </Card>
        ))}
      </section>

      {error ? (
        <Card className="border-critical/30 bg-critical/10 p-6" role="alert">
          <p className="font-medium text-white">Dashboard unavailable</p>
          <p className="mt-2 text-sm text-rose-100">{error}</p>
        </Card>
      ) : null}

      {summary ? (
        <>
          <section className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
            <SeverityDistributionCard buckets={summary.severity_distribution} />
            <IncidentMapCard
              pulses={summary.incident_pulses}
              mapPreviewUrl={
                summary.incident_pulses.some((pulse) => pulse.lat != null && pulse.lng != null)
                  ? getDashboardIncidentMapUrl()
                  : undefined
              }
            />
          </section>
          <CaseQueueCard cases={summary.queue} />
        </>
      ) : null}
    </div>
  );
}
