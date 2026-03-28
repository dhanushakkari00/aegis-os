from __future__ import annotations

from collections import Counter

from sqlalchemy.orm import Session

from app.schemas.case import DashboardMetric, DashboardSummaryResponse, LocationPulse, QueueCase, SeverityBucket
from app.schemas.enums import UrgencyLevel
from app.services.case_service import CaseService


class DashboardService:
    def __init__(self, case_service: CaseService) -> None:
        self.case_service = case_service

    def summary(self, db: Session) -> DashboardSummaryResponse:
        cases = self.case_service.list_cases(db)
        severity_counts = Counter(case.urgency_level for case in cases)

        totals = [
            DashboardMetric(label="Active Cases", value=len(cases)),
            DashboardMetric(label="Critical", value=severity_counts.get(UrgencyLevel.CRITICAL.value, 0)),
            DashboardMetric(label="High Confidence", value=sum(1 for case in cases if case.confidence >= 0.8)),
        ]

        severity_distribution = [
            SeverityBucket(level=UrgencyLevel(level.value), count=severity_counts.get(level.value, 0))
            for level in UrgencyLevel
        ]

        queue = [
            QueueCase(
                id=case.id,
                mode=case.mode,
                detected_case_type=case.detected_case_type,
                urgency_level=case.urgency_level,
                confidence=case.confidence,
                handoff_summary=case.handoff_summary,
                created_at=case.created_at,
            )
            for case in cases[:8]
        ]

        incident_pulses = []
        for case in cases[:6]:
            location = "Unknown location"
            note = case.handoff_summary or case.raw_input[:120]
            structured = case.structured_result_json or {}
            structured_section = structured.get("structured") or {}
            disaster_section = structured_section.get("disaster") or {}
            disaster_location = (
                disaster_section.get("location")
            )
            if disaster_location:
                location = disaster_location
            incident_pulses.append(
                LocationPulse(label=location, severity=case.urgency_level, note=note[:120])
            )

        return DashboardSummaryResponse(
            totals=totals,
            severity_distribution=severity_distribution,
            queue=queue,
            incident_pulses=incident_pulses,
        )
