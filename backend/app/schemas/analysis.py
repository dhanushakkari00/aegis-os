from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.enums import CaseMode, DecisionState, DetectedCaseType, UrgencyLevel


class ObservedFact(BaseModel):
    label: str
    value: str
    source: str = Field(description="Where the fact came from, e.g. user text, transcript, artifact.")
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)


class MissingInformationItem(BaseModel):
    item: str
    reason: str
    criticality: str = Field(default="medium", description="low, medium, or high")


class RecommendedActionItem(BaseModel):
    priority: int = Field(ge=1, le=10)
    title: str
    description: str
    category: str
    rationale: str | None = None
    is_immediate: bool = True


class MedicalStructuredData(BaseModel):
    symptoms: list[str] = Field(default_factory=list)
    onset_or_duration: str | None = None
    medical_history: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    vitals: dict[str, str] = Field(default_factory=dict)
    red_flags: list[str] = Field(default_factory=list)


class DisasterStructuredData(BaseModel):
    incident_type: str | None = None
    location: str | None = None
    affected_people: str | None = None
    injuries: list[str] = Field(default_factory=list)
    infrastructure_damage: list[str] = Field(default_factory=list)
    hazards: list[str] = Field(default_factory=list)
    supply_needs: list[str] = Field(default_factory=list)
    structured_field_report: list[str] = Field(default_factory=list)


class StructuredAnalysis(BaseModel):
    medical: MedicalStructuredData | None = None
    disaster: DisasterStructuredData | None = None


class NormalizedAnalysisOutput(BaseModel):
    schema_version: str = "1.0"
    mode_used: CaseMode
    case_type: DetectedCaseType
    decision_state: DecisionState = DecisionState.NEEDS_CLARIFICATION
    urgency_level: UrgencyLevel
    confidence: float = Field(ge=0.0, le=1.0)
    concise_summary: str
    handoff_summary: str
    assistant_response: str = Field(
        description="What Aegis OS should say back to the user or caller right now.",
    )
    final_verdict: str | None = Field(
        default=None,
        description="Operational conclusion when enough evidence exists for a decision.",
    )
    extracted_location: str | None = Field(
        default=None,
        description="Best available location string for geocoding (address, landmark, or area name).",
    )
    location_lat: float | None = Field(default=None, description="Latitude if explicitly provided.")
    location_lng: float | None = Field(default=None, description="Longitude if explicitly provided.")
    observed_facts: list[ObservedFact] = Field(default_factory=list)
    inferred_risks: list[str] = Field(default_factory=list)
    missing_information: list[MissingInformationItem] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    recommended_actions: list[RecommendedActionItem] = Field(default_factory=list)
    disclaimers: list[str] = Field(default_factory=list)
    structured: StructuredAnalysis = Field(default_factory=StructuredAnalysis)

    @field_validator("recommended_actions")
    @classmethod
    def sort_actions(cls, actions: list[RecommendedActionItem]) -> list[RecommendedActionItem]:
        return sorted(actions, key=lambda item: item.priority)

    @model_validator(mode="after")
    def normalize_density(self) -> NormalizedAnalysisOutput:
        def dedupe_strings(values: list[str]) -> list[str]:
            seen: set[str] = set()
            normalized: list[str] = []
            for value in values:
                cleaned = value.strip()
                if not cleaned:
                    continue
                key = cleaned.casefold()
                if key in seen:
                    continue
                seen.add(key)
                normalized.append(cleaned)
            return normalized

        def dedupe_missing(values: list[MissingInformationItem]) -> list[MissingInformationItem]:
            seen: set[str] = set()
            normalized: list[MissingInformationItem] = []
            for item in values:
                key = item.item.strip().casefold()
                if not key or key in seen:
                    continue
                seen.add(key)
                normalized.append(item)
            return normalized

        self.inferred_risks = dedupe_strings(self.inferred_risks)[:3]
        self.follow_up_questions = dedupe_strings(self.follow_up_questions)[:3]
        self.disclaimers = dedupe_strings(self.disclaimers)
        self.missing_information = dedupe_missing(self.missing_information)

        missing_limit = 5 if self.urgency_level in {"high", "critical"} else 3
        self.missing_information = self.missing_information[:missing_limit]
        self.recommended_actions = self.recommended_actions[:4]
        if self.decision_state == DecisionState.FINAL and not self.final_verdict:
            self.final_verdict = self.concise_summary
        return self
