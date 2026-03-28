"use client";

import { motion } from "framer-motion";
import { FileSearch, ShieldCheck, Sparkles, TriangleAlert, Workflow } from "lucide-react";

import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useReducedMotionPreference } from "@/hooks/use-reduced-motion";
import { cn } from "@/lib/utils";

const steps = [
  { title: "Ingest", description: "Normalize messy intake and artifact context.", icon: Workflow },
  { title: "Validate", description: "Schema and evidence checks before analysis.", icon: ShieldCheck },
  { title: "Extract", description: "Convert reports into observed facts and key fields.", icon: FileSearch },
  { title: "Classify", description: "Determine case type and urgency level.", icon: TriangleAlert },
  { title: "Recommend", description: "Generate next safe actions and handoff.", icon: Sparkles }
];

export function AnalysisPipeline({
  activeStep = steps.length - 1,
  loading = false
}: {
  activeStep?: number;
  loading?: boolean;
}) {
  const reducedMotion = useReducedMotionPreference();

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Live Analysis Pipeline</CardTitle>
          <CardDescription>
            Shows how Aegis OS moves from intake to structured response.
          </CardDescription>
        </div>
      </CardHeader>
      <div className="grid gap-3 md:grid-cols-5">
        {steps.map((step, index) => {
          const status =
            index < activeStep ? "complete" : index === activeStep ? "active" : "pending";
          const Icon = step.icon;

          return (
            <motion.div
              key={step.title}
              initial={reducedMotion ? false : { opacity: 0, y: 10 }}
              animate={reducedMotion ? undefined : { opacity: 1, y: 0 }}
              transition={{ duration: 0.28, delay: reducedMotion ? 0 : index * 0.05 }}
              className={cn(
                "rounded-[24px] border p-4",
                status === "complete" && "border-surge/20 bg-surge/10",
                status === "active" && "border-cyan/20 bg-cyan/10",
                status === "pending" && "border-white/10 bg-white/5"
              )}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="rounded-2xl border border-white/10 bg-ink/60 p-3">
                  <Icon className="h-4 w-4 text-white" />
                </div>
                <span className="text-xs uppercase tracking-[0.24em] text-slate-400">
                  {loading && index === activeStep ? "Running" : status}
                </span>
              </div>
              <h4 className="mt-4 font-medium text-white">{step.title}</h4>
              <p className="mt-2 text-sm leading-6 text-slate-300">{step.description}</p>
            </motion.div>
          );
        })}
      </div>
    </Card>
  );
}

