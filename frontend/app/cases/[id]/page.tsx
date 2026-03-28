"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { ConfidenceMeter } from "@/components/confidence-meter";
import { HandoffSummaryCard } from "@/components/handoff-summary-card";
import { JSONInspectorDrawer } from "@/components/json-inspector-drawer";
import { MissingInfoPanel } from "@/components/missing-info-panel";
import { RecommendationCard } from "@/components/recommendation-card";
import { TimelinePanel } from "@/components/timeline-panel";
import { UrgencyBadge } from "@/components/urgency-badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getCase } from "@/lib/api";
import type { CaseDetail } from "@/lib/types";

export default function CaseDetailPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;
  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (!caseId) {
        return;
      }
      try {
        const data = await getCase(caseId);
        if (!cancelled) {
          setCaseData(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unable to load case.");
        }
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [caseId]);

  const timelineEntries =
    caseData === null
      ? []
      : [
          {
            title: "Case created",
            description: "Intake was captured and queued for analysis.",
            timestamp: caseData.created_at,
            type: "ingest" as const
          },
          ...caseData.artifacts.map((artifact) => ({
            title: `Artifact uploaded: ${artifact.filename}`,
            description: `${artifact.artifact_type} | ${artifact.mime_type}`,
            timestamp: artifact.created_at,
            type: "artifact" as const
          })),
          ...caseData.analysis_runs.map((run) => ({
            title: "Analysis completed",
            description: `${run.model_name} via ${run.prompt_name}`,
            timestamp: run.created_at,
            type: "analysis" as const
          }))
        ];

  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-4 rounded-[32px] border border-white/10 bg-white/5 p-6 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-cyan">Case file</p>
          <h2 className="mt-3 font-display text-4xl font-semibold text-white">
            {caseId || "Loading case"}
          </h2>
        </div>
        {caseData ? (
          <div className="flex flex-wrap items-center gap-3">
            <UrgencyBadge urgency={caseData.urgency_level} />
            <JSONInspectorDrawer payload={caseData.structured_result_json} />
          </div>
        ) : null}
      </section>

      {error ? (
        <Card className="border-critical/30 bg-critical/10 p-6">
          <p className="font-medium text-white">Case load failed</p>
          <p className="mt-2 text-sm text-rose-100">{error}</p>
        </Card>
      ) : null}

      {caseData ? (
        <>
          <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <HandoffSummaryCard
              summary={caseData.handoff_summary}
              disclaimers={caseData.structured_result_json?.disclaimers}
            />
            <div className="space-y-6">
              <ConfidenceMeter confidence={caseData.confidence} />
              <Card>
                <CardHeader>
                  <div>
                    <CardTitle>Raw intake</CardTitle>
                    <CardDescription>
                      Original unstructured text is preserved for review.
                    </CardDescription>
                  </div>
                </CardHeader>
                <p className="rounded-[24px] border border-white/10 bg-white/5 p-5 text-sm leading-7 text-slate-200">
                  {caseData.raw_input}
                </p>
              </Card>
            </div>
          </section>

          <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
            <TimelinePanel entries={timelineEntries} />
            <MissingInfoPanel
              items={caseData.structured_result_json?.missing_information ?? []}
            />
          </section>

          <section className="grid gap-6 lg:grid-cols-3">
            {caseData.recommended_actions.map((action) => (
              <RecommendationCard key={`${action.priority}-${action.title}`} action={action} />
            ))}
          </section>
        </>
      ) : null}
    </div>
  );
}
