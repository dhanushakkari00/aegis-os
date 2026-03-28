from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.enums import CaseMode, DetectedCaseType, UrgencyLevel


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
    urgency_level: UrgencyLevel
    confidence: float = Field(ge=0.0, le=1.0)
    concise_summary: str
    handoff_summary: str
    observed_facts: list[ObservedFact] = Field(default_factory=list)
    inferred_risks: list[str] = Field(default_factory=list)
    missing_information: list[MissingInformationItem] = Field(default_factory=list)
    recommended_actions: list[RecommendedActionItem] = Field(default_factory=list)
    disclaimers: list[str] = Field(default_factory=list)
    structured: StructuredAnalysis = Field(default_factory=StructuredAnalysis)

    @field_validator("recommended_actions")
    @classmethod
    def sort_actions(cls, actions: list[RecommendedActionItem]) -> list[RecommendedActionItem]:
        return sorted(actions, key=lambda item: item.priority)

