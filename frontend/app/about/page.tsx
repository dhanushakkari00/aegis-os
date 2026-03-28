import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const principles = [
  "Confidence and severity are shown separately to avoid overclaiming certainty.",
  "Observed facts are separated from inferred risks.",
  "Keyboard navigation, focus states, contrast controls, and reduced motion are built in.",
  "Gemini access remains backend-only and uploads are validated before processing."
];

export default function AboutPage() {
  return (
    <div className="space-y-8">
      <section className="rounded-[32px] border border-white/10 bg-white/5 p-8">
        <Badge className="border-cyan/20 bg-cyan/10 text-cyan">About Aegis OS</Badge>
        <h2 className="mt-5 max-w-3xl font-display text-4xl font-semibold text-white">
          Aegis OS is an emergency operations product, not a generic chatbot.
        </h2>
        <p className="mt-4 max-w-3xl text-lg leading-8 text-slate-300">
          The platform is designed to convert messy intake into structured decision support for
          medical triage and disaster response, while keeping uncertainty visible and preserving
          operational readability under stress.
        </p>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Accessibility</CardTitle>
              <CardDescription>
                Built for high-pressure environments and broad device coverage.
              </CardDescription>
            </div>
          </CardHeader>
          <ul className="space-y-3 text-sm leading-7 text-slate-200">
            {principles.map((item) => (
              <li key={item} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                {item}
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>Disclaimers</CardTitle>
              <CardDescription>
                Safety support depends on human judgment and local protocols.
              </CardDescription>
            </div>
          </CardHeader>
          <div className="space-y-3 text-sm leading-7 text-slate-200">
            <div className="rounded-2xl border border-critical/20 bg-critical/10 p-4">
              Medical outputs do not replace licensed clinical evaluation or emergency medical
              services.
            </div>
            <div className="rounded-2xl border border-signal/20 bg-signal/10 p-4">
              Disaster guidance does not replace incident command, local authorities, or public
              safety directives.
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              If a situation is immediately life-threatening, contact emergency services and follow
              official instructions first.
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}

