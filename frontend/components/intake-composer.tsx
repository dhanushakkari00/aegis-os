"use client";

import { startTransition, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Send } from "lucide-react";

import { FileDropzone } from "@/components/file-dropzone";
import { ModeSwitcher } from "@/components/mode-switcher";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createCase, uploadCaseArtifact } from "@/lib/api";
import {
  composeRawInput,
  intakeSchema,
  type IntakeFormValues
} from "@/lib/validators";

export function IntakeComposer() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [pending, setPending] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const form = useForm<IntakeFormValues>({
    resolver: zodResolver(intakeSchema),
    defaultValues: {
      mode: "auto_detect",
      contactEmail: "",
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
      const created = await createCase({
        mode: values.mode,
        raw_input,
        contact_email: values.contactEmail?.trim() || null
      });
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
            <label className="block space-y-2">
              <span className="text-sm font-medium text-white">Notification email</span>
              <Input
                type="email"
                aria-label="Notification email"
                placeholder="Optional responder or patient contact"
                {...form.register("contactEmail")}
              />
              <FormError message={form.formState.errors.contactEmail?.message} />
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
              <p className="text-xs uppercase tracking-[0.24em] text-cyan">Production Intake</p>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                This surface only launches real cases. Use the narrative, transcript, mixed notes,
                and uploaded evidence to start a production analysis flow.
              </p>
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
