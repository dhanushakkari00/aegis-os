"use client";

import { startTransition, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowRight, LoaderCircle } from "lucide-react";

import { AnalysisPipeline } from "@/components/analysis-pipeline";
import { ConfidenceMeter } from "@/components/confidence-meter";
import { HandoffSummaryCard } from "@/components/handoff-summary-card";
import { JSONInspectorDrawer } from "@/components/json-inspector-drawer";
import { MissingInfoPanel } from "@/components/missing-info-panel";
import { RecommendationCard } from "@/components/recommendation-card";
import { UrgencyBadge } from "@/components/urgency-badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { analyzeCase, getCase } from "@/lib/api";
import type { CaseDetail } from "@/lib/types";
import { formatTimestamp } from "@/lib/utils";

export default function AnalyzePage() {
  const searchParams = useSearchParams();
  const caseId = searchParams.get("caseId");
  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        if (!caseId) {
          setCaseData(null);
          setLoading(false);
          return;
        }

        for (let current = 0; current < 5; current += 1) {
          if (cancelled) {
            return;
          }
          setStep(current);
          await new Promise((resolve) => window.setTimeout(resolve, 180));
        }

        const existing = await getCase(caseId);
        const analyzed =
          existing.structured_result_json === null ? await analyzeCase(caseId) : existing;
        if (!cancelled) {
          setCaseData(analyzed);
          setStep(4);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Analysis failed.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    startTransition(() => {
      void run();
    });

    return () => {
      cancelled = true;
    };
  }, [caseId]);

  return (
    <div className="space-y-8" aria-live="polite" aria-busy={loading}>
      <section className="flex flex-col gap-4 rounded-[32px] border border-white/10 bg-white/5 p-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-cyan">Analysis board</p>
          <h2 className="mt-3 font-display text-4xl font-semibold text-white">
            Live command pipeline
          </h2>
          <p className="mt-3 max-w-2xl text-slate-300">
            Intake moves through validation, extraction, classification, and handoff generation
            before operators commit to action.
          </p>
        </div>
        {caseData ? (
          <div className="flex flex-wrap items-center gap-3">
            <UrgencyBadge urgency={caseData.urgency_level} />
            <JSONInspectorDrawer payload={caseData.structured_result_json} />
            <Button asChild variant="secondary">
              <Link href={`/cases/${caseData.id}`} className="inline-flex items-center gap-2">
                Full case detail
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        ) : null}
      </section>

      <AnalysisPipeline activeStep={step} loading={loading} />

      {!caseId ? (
        <Card className="p-6">
          <p className="font-medium text-white">No case selected</p>
          <p className="mt-2 text-sm text-slate-300">
            Start a real intake from the main command surface, then open the live analysis view for
            that case.
          </p>
          <div className="mt-4">
            <Button asChild variant="secondary">
              <Link href="/">Go to intake</Link>
            </Button>
          </div>
        </Card>
      ) : null}

      {error ? (
        <Card className="border-critical/30 bg-critical/10 p-6" role="alert">
          <p className="font-medium text-white">Analysis could not complete</p>
          <p className="mt-2 text-sm text-rose-100">{error}</p>
        </Card>
      ) : null}

      {loading && !caseData ? (
        <Card className="flex items-center gap-4 p-6" role="status" aria-label="Analysis in progress">
          <LoaderCircle className="h-5 w-5 animate-spin text-cyan" aria-hidden="true" />
          <p className="text-slate-200">Running analysis and building the handoff package.</p>
        </Card>
      ) : null}

      {caseData ? (
        <>
          <section className="grid gap-6 xl:grid-cols-2" aria-label="Urgency and confidence">
            <UrgencyBadge urgency={caseData.urgency_level} />
            <ConfidenceMeter confidence={caseData.confidence} />
          </section>

          <MissingInfoPanel
            items={caseData.structured_result_json?.missing_information ?? []}
          />

          <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <HandoffSummaryCard
              summary={caseData.handoff_summary}
              disclaimers={caseData.structured_result_json?.disclaimers}
            />
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Case signal</CardTitle>
                  <CardDescription>
                    Created {formatTimestamp(caseData.created_at)} and last updated{" "}
                    {formatTimestamp(caseData.updated_at)}.
                  </CardDescription>
                </div>
              </CardHeader>
              <div className="space-y-3 text-sm text-slate-300">
                <p>
                  <span className="font-medium text-white">Mode:</span>{" "}
                  {caseData.mode.replaceAll("_", " ")}
                </p>
                <p>
                  <span className="font-medium text-white">Detected type:</span>{" "}
                  {caseData.detected_case_type}
                </p>
                <p className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  {caseData.structured_result_json?.concise_summary}
                </p>
              </div>
            </Card>
          </section>

          <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Observed Facts</CardTitle>
                  <CardDescription>
                    Facts are separated from inferred risks to avoid overclaiming certainty.
                  </CardDescription>
                </div>
              </CardHeader>
              <div className="space-y-3">
                {caseData.structured_result_json?.observed_facts.map((fact) => (
                  <div
                    key={`${fact.label}-${fact.value}`}
                    className="rounded-2xl border border-white/10 bg-white/5 p-4"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-medium text-white">{fact.label}</p>
                      <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                        {Math.round(fact.confidence * 100)}% confidence
                      </p>
                    </div>
                    <p className="mt-2 text-sm text-slate-300">{fact.value}</p>
                    <p className="mt-2 text-xs uppercase tracking-[0.24em] text-cyan">
                      Source {fact.source}
                    </p>
                  </div>
                ))}
              </div>
            </Card>
          </section>

          <section className="grid gap-6 lg:grid-cols-3">
            {caseData.recommended_actions.map((action) => (
              <RecommendationCard key={`${action.priority}-${action.title}`} action={action} />
            ))}
          </section>

          <div className="text-sm text-slate-400">
            Need the permanent detail view? Open{" "}
            <Link className="text-cyan" href={`/cases/${caseData.id}`}>
              /cases/{caseData.id}
            </Link>
            .
          </div>
        </>
      ) : null}
    </div>
  );
}
