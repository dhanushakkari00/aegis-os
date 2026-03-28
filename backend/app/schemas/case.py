from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.analysis import NormalizedAnalysisOutput, RecommendedActionItem
from app.schemas.enums import CaseMode, DetectedCaseType, UrgencyLevel


class CaseCreate(BaseModel):
    mode: CaseMode = CaseMode.AUTO_DETECT
    raw_input: str = Field(min_length=10, max_length=8000)

    @field_validator("raw_input")
    @classmethod
    def normalize_input(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 10:
            raise ValueError("Case intake must contain at least 10 characters.")
        return normalized


class CaseUpdate(BaseModel):
    mode: CaseMode | None = None
    raw_input: str | None = Field(default=None, min_length=10, max_length=8000)

    @field_validator("raw_input")
    @classmethod
    def normalize_optional_input(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if len(normalized) < 10:
            raise ValueError("Case intake must contain at least 10 characters.")
        return normalized


class ArtifactResponse(BaseModel):
    id: str
    filename: str
    mime_type: str
    size_bytes: int
    artifact_type: str
    storage_provider: str
    storage_uri: str
    local_path: str | None = None
    content_excerpt: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisRunResponse(BaseModel):
    id: str
    status: str
    mode_used: str
    model_name: str
    prompt_name: str
    error_message: str | None = None
    latency_ms: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CaseSummaryResponse(BaseModel):
    id: str
    mode: CaseMode
    detected_case_type: DetectedCaseType
    urgency_level: UrgencyLevel
    confidence: float
    handoff_summary: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseDetailResponse(CaseSummaryResponse):
    raw_input: str
    structured_result_json: NormalizedAnalysisOutput | None = None
    artifacts: list[ArtifactResponse] = Field(default_factory=list)
    analysis_runs: list[AnalysisRunResponse] = Field(default_factory=list)
    recommended_actions: list[RecommendedActionItem] = Field(default_factory=list)


class AnalyzeCaseRequest(BaseModel):
    mode_override: CaseMode | None = None


class CaseDeleteResponse(BaseModel):
    id: str
    deleted: bool


class ExportJSONResponse(BaseModel):
    case_id: str
    payload: NormalizedAnalysisOutput | None


class DashboardMetric(BaseModel):
    label: str
    value: int


class SeverityBucket(BaseModel):
    level: UrgencyLevel
    count: int


class QueueCase(BaseModel):
    id: str
    mode: CaseMode
    detected_case_type: DetectedCaseType
    urgency_level: UrgencyLevel
    confidence: float
    handoff_summary: str | None = None
    created_at: datetime


class LocationPulse(BaseModel):
    label: str
    severity: UrgencyLevel
    note: str


class DashboardSummaryResponse(BaseModel):
    totals: list[DashboardMetric]
    severity_distribution: list[SeverityBucket]
    queue: list[QueueCase]
    incident_pulses: list[LocationPulse]
