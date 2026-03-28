export type CaseMode = "auto_detect" | "medical_triage" | "disaster_response";
export type DetectedCaseType = "medical" | "disaster" | "mixed" | "unclear";
export type UrgencyLevel = "low" | "moderate" | "high" | "critical";
export type DecisionState = "needs_clarification" | "provisional" | "final";

export type ObservedFact = {
  label: string;
  value: string;
  source: string;
  confidence: number;
};

export type MissingInformationItem = {
  item: string;
  reason: string;
  criticality: string;
};

export type RecommendedActionItem = {
  priority: number;
  title: string;
  description: string;
  category: string;
  rationale?: string | null;
  is_immediate: boolean;
};

export type MedicalStructuredData = {
  symptoms: string[];
  onset_or_duration?: string | null;
  medical_history: string[];
  medications: string[];
  allergies: string[];
  vitals: Record<string, string>;
  red_flags: string[];
};

export type DisasterStructuredData = {
  incident_type?: string | null;
  location?: string | null;
  affected_people?: string | null;
  injuries: string[];
  infrastructure_damage: string[];
  hazards: string[];
  supply_needs: string[];
  structured_field_report: string[];
};

export type StructuredAnalysis = {
  medical?: MedicalStructuredData | null;
  disaster?: DisasterStructuredData | null;
};

export type NormalizedAnalysisOutput = {
  schema_version: string;
  mode_used: CaseMode;
  case_type: DetectedCaseType;
  decision_state: DecisionState;
  urgency_level: UrgencyLevel;
  confidence: number;
  concise_summary: string;
  handoff_summary: string;
  assistant_response: string;
  final_verdict?: string | null;
  extracted_location?: string | null;
  location_lat?: number | null;
  location_lng?: number | null;
  observed_facts: ObservedFact[];
  inferred_risks: string[];
  missing_information: MissingInformationItem[];
  follow_up_questions: string[];
  recommended_actions: RecommendedActionItem[];
  disclaimers: string[];
  structured: StructuredAnalysis;
};

export type Artifact = {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  artifact_type: string;
  storage_provider: string;
  storage_uri: string;
  content_excerpt?: string | null;
  created_at: string;
};

export type AnalysisRun = {
  id: string;
  status: string;
  mode_used: string;
  model_name: string;
  prompt_name: string;
  error_message?: string | null;
  latency_ms?: number | null;
  created_at: string;
};

export type CaseDetail = {
  id: string;
  mode: CaseMode;
  raw_input: string;
  contact_email?: string | null;
  detected_case_type: DetectedCaseType;
  urgency_level: UrgencyLevel;
  confidence: number;
  handoff_summary?: string | null;
  last_notification_sent_at?: string | null;
  last_notification_error?: string | null;
  structured_result_json?: NormalizedAnalysisOutput | null;
  artifacts: Artifact[];
  analysis_runs: AnalysisRun[];
  recommended_actions: RecommendedActionItem[];
  created_at: string;
  updated_at: string;
};

export type CaseSummary = Pick<
  CaseDetail,
  "id" | "mode" | "detected_case_type" | "urgency_level" | "confidence" | "handoff_summary" | "created_at" | "updated_at"
>;

export type DashboardMetric = {
  label: string;
  value: number;
};

export type SeverityBucket = {
  level: UrgencyLevel;
  count: number;
};

export type QueueCase = {
  id: string;
  mode: CaseMode;
  detected_case_type: DetectedCaseType;
  urgency_level: UrgencyLevel;
  confidence: number;
  handoff_summary?: string | null;
  created_at: string;
};

export type LocationPulse = {
  label: string;
  severity: UrgencyLevel;
  note: string;
  lat?: number | null;
  lng?: number | null;
};

export type DashboardSummary = {
  totals: DashboardMetric[];
  severity_distribution: SeverityBucket[];
  queue: QueueCase[];
  incident_pulses: LocationPulse[];
};
