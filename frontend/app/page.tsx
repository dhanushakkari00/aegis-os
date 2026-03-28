import { IntakeComposer } from "@/components/intake-composer";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

const features = [
  "Messy intake to structured facts",
  "Urgency, gaps, and safe next steps",
  "Medical and disaster workflows in one surface"
];

export default function HomePage() {
  return (
    <div className="space-y-8">
      <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <Card className="relative overflow-hidden p-8 md:p-10">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(78,232,255,0.12),transparent_40%),radial-gradient(circle_at_bottom_right,rgba(255,137,97,0.12),transparent_35%)]" />
          <div className="relative">
            <Badge className="border-cyan/20 bg-cyan/10 text-cyan">Hackathon-ready stack</Badge>
            <h2 className="mt-6 max-w-3xl font-display text-4xl font-semibold leading-tight text-white md:text-6xl">
              Emergency intelligence built for calm decisions under pressure.
            </h2>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
              Aegis OS turns unstructured text, uploads, transcripts, and mixed notes into
              structured facts, urgency signals, safe next actions, and operator-ready handoffs.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              {features.map((feature) => (
                <span
                  key={feature}
                  className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200"
                >
                  {feature}
                </span>
              ))}
            </div>
          </div>
        </Card>

        <Card className="grid gap-4 p-8">
          <div className="rounded-[24px] border border-critical/20 bg-critical/10 p-5">
            <p className="text-xs uppercase tracking-[0.24em] text-critical">Medical triage</p>
            <p className="mt-3 text-lg font-medium text-white">
              Symptoms, red flags, missing information, and safe escalation guidance.
            </p>
          </div>
          <div className="rounded-[24px] border border-signal/20 bg-signal/10 p-5">
            <p className="text-xs uppercase tracking-[0.24em] text-signal">Disaster response</p>
            <p className="mt-3 text-lg font-medium text-white">
              Incident type, hazards, entrapment, logistics, and command-ready field reports.
            </p>
          </div>
          <div className="rounded-[24px] border border-cyan/20 bg-cyan/10 p-5">
            <p className="text-xs uppercase tracking-[0.24em] text-cyan">Strict JSON</p>
            <p className="mt-3 text-lg font-medium text-white">
              Machine-readable outputs validated on the backend for export and automation.
            </p>
          </div>
        </Card>
      </section>

      <IntakeComposer />
    </div>
  );
}

