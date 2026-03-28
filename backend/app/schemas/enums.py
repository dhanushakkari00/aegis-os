from __future__ import annotations

from enum import Enum


class CaseMode(str, Enum):
    AUTO_DETECT = "auto_detect"
    MEDICAL_TRIAGE = "medical_triage"
    DISASTER_RESPONSE = "disaster_response"


class DetectedCaseType(str, Enum):
    MEDICAL = "medical"
    DISASTER = "disaster"
    MIXED = "mixed"
    UNCLEAR = "unclear"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class AnalysisRunStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class DecisionState(str, Enum):
    NEEDS_CLARIFICATION = "needs_clarification"
    PROVISIONAL = "provisional"
    FINAL = "final"
