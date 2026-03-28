import type {
  CaseDetail,
  CaseMode,
  DashboardSummary,
  DetectedCaseType,
  NormalizedAnalysisOutput,
  RecommendedActionItem,
  UrgencyLevel
} from "@/lib/types";

const MEDICAL_DISCLAIMER =
  "Aegis OS supports triage workflows only and does not replace licensed medical care.";
const DISASTER_DISCLAIMER =
  "Aegis OS provides emergency intelligence support and does not replace local incident command.";

export const medicalSeedInput =
  "58-year-old diabetic male with chest pain, sweating, and shortness of breath for 20 minutes.";
export const disasterSeedInput =
  "Flooding in Sector 9, 12 people trapped, one elderly injured, roads blocked, water above knee height.";

function createAction(
  priority: number,
  title: string,
  description: string,
  category: string,
  rationale: string
): RecommendedActionItem {
  return {
    priority,
    title,
    description,
    category,
    rationale,
    is_immediate: true
  };
}

export function simulateAnalysis(rawInput: string, mode: CaseMode): NormalizedAnalysisOutput {
  const lowered = rawInput.toLowerCase();
  const medicalLike =
    mode === "medical_triage" ||
    (mode === "auto_detect" &&
      ["chest pain", "shortness of breath", "diabetic", "fever", "allergy"].some((term) =>
        lowered.includes(term)
      ));
  const disasterLike =
    mode === "disaster_response" ||
    (mode === "auto_detect" &&
      ["flood", "trapped", "blocked", "fire", "evacuate"].some((term) => lowered.includes(term)));

  if (medicalLike && !disasterLike) {
    return {
      schema_version: "1.0",
      mode_used: mode,
      case_type: "medical",
      urgency_level: "critical",
      confidence: 0.9,
      concise_summary: "Potential cardiac emergency with red-flag symptoms.",
      handoff_summary:
        "Adult patient with diabetes reporting chest pain, sweating, and shortness of breath for around 20 minutes. Treat as high-acuity chest pain until ruled out by emergency care.",
      observed_facts: [
        { label: "Symptoms", value: "Chest pain, sweating, shortness of breath", source: "user_text", confidence: 0.94 },
        { label: "History", value: "Diabetes", source: "user_text", confidence: 0.86 },
        { label: "Duration", value: "20 minutes", source: "user_text", confidence: 0.9 }
      ],
      inferred_risks: ["Possible acute coronary syndrome or other cardiopulmonary emergency."],
      missing_information: [
        { item: "Current vitals", reason: "Needed to assess instability.", criticality: "high" },
        { item: "Medications and allergies", reason: "Improves safe handoff.", criticality: "medium" }
      ],
      recommended_actions: [
        createAction(1, "Escalate immediately", "Advise urgent EMS or emergency department evaluation.", "medical", "Red-flag chest pain cluster."),
        createAction(2, "Limit exertion", "Keep the patient resting while waiting for professional care.", "safety", "May reduce symptom worsening."),
        createAction(3, "Prepare handoff", "Confirm symptom onset time, history, medications, and allergies.", "information", "Supports emergency clinicians.")
      ],
      disclaimers: [MEDICAL_DISCLAIMER],
      structured: {
        medical: {
          symptoms: ["Chest pain", "Sweating", "Shortness of breath"],
          onset_or_duration: "20 minutes",
          medical_history: ["Diabetes"],
          medications: [],
          allergies: [],
          vitals: {},
          red_flags: ["Chest pain", "Shortness of breath", "Diaphoresis"]
        },
        disaster: null
      }
    };
  }

  if (disasterLike && !medicalLike) {
    return {
      schema_version: "1.0",
      mode_used: mode,
      case_type: "disaster",
      urgency_level: "critical",
      confidence: 0.93,
      concise_summary: "Active flooding with trapped civilians and blocked access routes.",
      handoff_summary:
        "Flooding reported in Sector 9 with 12 people trapped, one elderly person injured, roads blocked, and water above knee height. Treat as an active life-safety rescue event.",
      observed_facts: [
        { label: "Incident type", value: "Flooding", source: "user_text", confidence: 0.95 },
        { label: "Location", value: "Sector 9", source: "user_text", confidence: 0.9 },
        { label: "Affected people", value: "12 trapped", source: "user_text", confidence: 0.94 },
        { label: "Injury", value: "One elderly injured", source: "user_text", confidence: 0.89 }
      ],
      inferred_risks: [
        "Access may deteriorate further as water rises.",
        "Medical needs may escalate for trapped civilians."
      ],
      missing_information: [
        { item: "Exact landmark or coordinates", reason: "Needed for dispatch precision.", criticality: "high" },
        { item: "Floodwater trend", reason: "Needed to judge rescue timing.", criticality: "high" }
      ],
      recommended_actions: [
        createAction(1, "Dispatch rescue assets", "Notify local emergency response with trapped count, injury, and blocked-road details.", "dispatch", "Immediate life-safety risk."),
        createAction(2, "Confirm safe approach", "Verify high-ground or alternate access before committing teams into moving water.", "safety", "Protects responders."),
        createAction(3, "Stage medical support", "Prepare care for the injured elderly person and cold-exposure complications.", "medical", "Improves rescue handoff.")
      ],
      disclaimers: [DISASTER_DISCLAIMER],
      structured: {
        medical: null,
        disaster: {
          incident_type: "Flooding",
          location: "Sector 9",
          affected_people: "12 trapped people",
          injuries: ["One elderly injured person"],
          infrastructure_damage: ["Roads blocked"],
          hazards: ["Water above knee height", "Possible rising floodwater"],
          supply_needs: ["Rescue access equipment", "Medical support"],
          structured_field_report: [
            "Incident: Flooding",
            "Location: Sector 9",
            "Affected: 12 trapped, one elderly injured",
            "Access: roads blocked"
          ]
        }
      }
    };
  }

  return {
    schema_version: "1.0",
    mode_used: mode,
    case_type: medicalLike && disasterLike ? "mixed" : "unclear",
    urgency_level: medicalLike && disasterLike ? "high" : "moderate",
    confidence: medicalLike && disasterLike ? 0.68 : 0.42,
    concise_summary: medicalLike && disasterLike ? "Mixed emergency context with both safety and medical needs." : "Input is incomplete or ambiguous.",
    handoff_summary:
      "More detail is needed to determine the incident category, exact location, and immediate life threats.",
    observed_facts: [{ label: "Raw intake", value: rawInput, source: "user_text", confidence: 0.55 }],
    inferred_risks: ["Incomplete intake may conceal urgent needs."],
    missing_information: [
      { item: "Location", reason: "Needed for any dispatch or follow-up.", criticality: "high" },
      { item: "Primary hazard or symptom cluster", reason: "Needed to classify the case.", criticality: "high" }
    ],
    recommended_actions: [
      createAction(1, "Clarify the situation", "Collect exact location, immediate danger, and the main complaint or incident type.", "information", "Confidence is currently limited.")
    ],
    disclaimers: [MEDICAL_DISCLAIMER, DISASTER_DISCLAIMER],
    structured: {
      medical: medicalLike ? { symptoms: [], onset_or_duration: null, medical_history: [], medications: [], allergies: [], vitals: {}, red_flags: [] } : null,
      disaster: disasterLike ? { incident_type: null, location: null, affected_people: null, injuries: [], infrastructure_damage: [], hazards: [], supply_needs: [], structured_field_report: [] } : null
    }
  };
}

function createCase(id: string, mode: CaseMode, rawInput: string, createdAt: string): CaseDetail {
  const structured_result_json = simulateAnalysis(rawInput, mode);
  return {
    id,
    mode,
    raw_input: rawInput,
    detected_case_type: structured_result_json.case_type,
    urgency_level: structured_result_json.urgency_level,
    confidence: structured_result_json.confidence,
    handoff_summary: structured_result_json.handoff_summary,
    structured_result_json,
    artifacts: [],
    analysis_runs: [
      {
        id: `${id}-run`,
        status: "succeeded",
        mode_used: mode,
        model_name: "demo-fallback",
        prompt_name: "seed",
        created_at: createdAt,
        latency_ms: 80
      }
    ],
    recommended_actions: structured_result_json.recommended_actions,
    created_at: createdAt,
    updated_at: createdAt
  };
}

export function demoCases(): CaseDetail[] {
  return [
    createCase("demo-medical", "medical_triage", medicalSeedInput, "2026-03-28T04:45:00.000Z"),
    createCase("demo-disaster", "disaster_response", disasterSeedInput, "2026-03-28T05:10:00.000Z")
  ];
}

export function buildDemoDashboard(cases: CaseDetail[]): DashboardSummary {
  const counts = cases.reduce<Record<UrgencyLevel, number>>(
    (acc, current) => {
      acc[current.urgency_level] += 1;
      return acc;
    },
    { low: 0, moderate: 0, high: 0, critical: 0 }
  );

  return {
    totals: [
      { label: "Active Cases", value: cases.length },
      { label: "Critical", value: counts.critical },
      {
        label: "High Confidence",
        value: cases.filter((caseItem) => caseItem.confidence >= 0.8).length
      }
    ],
    severity_distribution: [
      { level: "low", count: counts.low },
      { level: "moderate", count: counts.moderate },
      { level: "high", count: counts.high },
      { level: "critical", count: counts.critical }
    ],
    queue: cases.map((caseItem) => ({
      id: caseItem.id,
      mode: caseItem.mode,
      detected_case_type: caseItem.detected_case_type as DetectedCaseType,
      urgency_level: caseItem.urgency_level,
      confidence: caseItem.confidence,
      handoff_summary: caseItem.handoff_summary,
      created_at: caseItem.created_at
    })),
    incident_pulses: cases.map((caseItem) => ({
      label:
        caseItem.structured_result_json?.structured.disaster?.location ??
        (caseItem.detected_case_type === "medical" ? "Medical Intake" : "Unknown"),
      severity: caseItem.urgency_level,
      note: caseItem.handoff_summary ?? caseItem.raw_input
    }))
  };
}

