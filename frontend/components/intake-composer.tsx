"use client";

import { startTransition, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { HeartPulse, MountainSnow, Send } from "lucide-react";

import { FileDropzone } from "@/components/file-dropzone";
import { ModeSwitcher } from "@/components/mode-switcher";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { createCase, uploadCaseArtifact } from "@/lib/api";
import { disasterSeedInput, medicalSeedInput } from "@/lib/demo-data";
import type { CaseMode } from "@/lib/types";
import {
  composeRawInput,
  intakeSchema,
  type IntakeFormValues
} from "@/lib/validators";

const seedModes: { label: string; value: string; rawInput: string; mode: CaseMode; icon: typeof HeartPulse }[] = [
  {
    label: "Medical demo",
    value: "medical",
    rawInput: medicalSeedInput,
    mode: "medical_triage",
    icon: HeartPulse
  },
  {
    label: "Disaster demo",
    value: "disaster",
    rawInput: disasterSeedInput,
    mode: "disaster_response",
    icon: MountainSnow
  }
];

export function IntakeComposer() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [pending, setPending] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const form = useForm<IntakeFormValues>({
    resolver: zodResolver(intakeSchema),
    defaultValues: {
      mode: "auto_detect",
      narrative: "",
      voiceTranscript: "",
      mixedNotes: ""
    }
  });

  const submit = form.handleSubmit(async (values) => {
    setPending(true);
    setSubmitError(null);
    try {
      const raw_input = composeRawInput(values);
      const created = await createCase({ mode: values.mode, raw_input });
      for (const file of files) {
        await uploadCaseArtifact(created.id, file, file.type.startsWith("image/") ? "image" : "attachment");
      }
      startTransition(() => {
        router.push(`/analyze?caseId=${created.id}`);
      });
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : "Unable to launch analysis."
      );
    } finally {
      setPending(false);
    }
  });

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <div>
          <CardTitle>Emergency Intake</CardTitle>
          <CardDescription>
            Capture messy real-world information, then route it into structured action.
          </CardDescription>
        </div>
      </CardHeader>
      <form className="space-y-6" onSubmit={submit}>
        <div className="space-y-3">
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Mode</p>
          <ModeSwitcher
            value={form.watch("mode")}
            onChange={(value) => form.setValue("mode", value)}
          />
        </div>

        <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
          <div className="space-y-4">
            <label className="block space-y-2">
              <span className="text-sm font-medium text-white">Primary intake</span>
              <Textarea
                aria-label="Primary intake"
                placeholder="Describe the incident, symptoms, or field report."
                {...form.register("narrative")}
              />
              <FormError message={form.formState.errors.narrative?.message} />
            </label>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-2">
                <span className="text-sm font-medium text-white">Voice transcript</span>
                <Textarea
                  aria-label="Voice transcript"
                  placeholder="Paste live transcript or dictation."
                  className="min-h-[140px]"
                  {...form.register("voiceTranscript")}
                />
              </label>
              <label className="block space-y-2">
                <span className="text-sm font-medium text-white">Mixed notes</span>
                <Textarea
                  aria-label="Mixed notes"
                  placeholder="Add fragmented notes, dispatch snippets, or witness details."
                  className="min-h-[140px]"
                  {...form.register("mixedNotes")}
                />
              </label>
            </div>
          </div>

          <div className="space-y-4">
            <FileDropzone files={files} onFilesChange={setFiles} />
            <div className="rounded-[24px] border border-white/10 bg-white/5 p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Seed demos</p>
              <div className="mt-4 grid gap-3">
                {seedModes.map((seed) => {
                  const Icon = seed.icon;
                  return (
                    <button
                      key={seed.value}
                      type="button"
                      onClick={() => {
                        form.reset({
                          mode: seed.mode,
                          narrative: seed.rawInput,
                          voiceTranscript: "",
                          mixedNotes: ""
                        });
                        setFiles([]);
                      }}
                      className="flex items-center gap-3 rounded-2xl border border-white/10 bg-ink/70 p-4 text-left transition hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan/70"
                    >
                      <div className="rounded-2xl border border-cyan/20 bg-cyan/10 p-3 text-cyan">
                        <Icon className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="font-medium text-white">{seed.label}</p>
                        <p className="line-clamp-2 text-sm text-slate-300">{seed.rawInput}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4 rounded-[24px] border border-white/10 bg-white/5 p-4">
          <div className="max-w-2xl">
            <p className="text-sm text-slate-300">
              Uploaded files remain backend-scoped. Severity and confidence are shown separately,
              and missing critical information is always surfaced before handoff.
            </p>
            {submitError ? <p className="mt-3 text-sm text-critical">{submitError}</p> : null}
          </div>
          <Button type="submit" size="lg" disabled={pending}>
            <Send className="h-4 w-4" />
            {pending ? "Creating case..." : "Launch analysis"}
          </Button>
        </div>
      </form>
    </Card>
  );
}

function FormError({ message }: { message?: string }) {
  if (!message) {
    return null;
  }

  return <p className="text-sm text-critical">{message}</p>;
}
