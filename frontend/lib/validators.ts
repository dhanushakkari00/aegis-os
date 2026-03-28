import { z } from "zod";

export const caseModes = ["auto_detect", "medical_triage", "disaster_response"] as const;

export const intakeSchema = z
  .object({
    mode: z.enum(caseModes),
    narrative: z.string().trim().min(10, "Describe the incident or symptoms in more detail."),
    voiceTranscript: z.string().trim().optional(),
    mixedNotes: z.string().trim().optional()
  })
  .superRefine((values, ctx) => {
    if (!values.narrative && !values.voiceTranscript && !values.mixedNotes) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "At least one intake field is required.",
        path: ["narrative"]
      });
    }
  });

export type IntakeFormValues = z.infer<typeof intakeSchema>;

export function composeRawInput(values: IntakeFormValues) {
  const sections = [
    values.narrative ? `Primary Intake\n${values.narrative}` : "",
    values.voiceTranscript ? `Voice Transcript\n${values.voiceTranscript}` : "",
    values.mixedNotes ? `Mixed Notes\n${values.mixedNotes}` : ""
  ].filter(Boolean);

  return sections.join("\n\n").trim();
}

