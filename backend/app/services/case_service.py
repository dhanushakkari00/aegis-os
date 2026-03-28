from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ai.orchestrator import AIOrchestrator, serialize_analysis_output
from app.core.config import Settings
from app.models.analysis_run import AnalysisRun
from app.models.case import Case
from app.models.recommended_action import RecommendedAction
from app.schemas.analysis import NormalizedAnalysisOutput
from app.schemas.case import CaseCreate
from app.schemas.enums import AnalysisRunStatus, CaseMode, DetectedCaseType, UrgencyLevel


class CaseService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.orchestrator = AIOrchestrator(settings)

    def create_case(self, db: Session, payload: CaseCreate) -> Case:
        case = Case(
            mode=payload.mode.value,
            raw_input=payload.raw_input,
            detected_case_type=DetectedCaseType.UNCLEAR.value,
            urgency_level=UrgencyLevel.MODERATE.value,
            confidence=0.0,
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        return self.get_case(db, case.id)

    def get_case(self, db: Session, case_id: str) -> Case:
        statement = (
            select(Case)
            .options(
                selectinload(Case.artifacts),
                selectinload(Case.analysis_runs),
                selectinload(Case.recommended_actions),
            )
            .where(Case.id == case_id)
        )
        case = db.scalar(statement)
        if case is None:
            raise LookupError("Case not found.")
        return case

    def list_cases(self, db: Session) -> list[Case]:
        statement = (
            select(Case)
            .options(selectinload(Case.recommended_actions))
            .order_by(Case.created_at.desc())
        )
        return list(db.scalars(statement).unique())

    def analyze_case(self, db: Session, case_id: str, mode_override: CaseMode | None = None) -> Case:
        case = self.get_case(db, case_id)
        mode = mode_override or CaseMode(case.mode)

        artifact_lines = []
        for artifact in case.artifacts:
            summary = f"{artifact.filename} ({artifact.mime_type}, {artifact.size_bytes} bytes)"
            if artifact.content_excerpt:
                summary += f" excerpt={artifact.content_excerpt[:280]}"
            artifact_lines.append(summary)
        artifact_context = "\n".join(artifact_lines) if artifact_lines else "No uploaded artifacts."

        try:
            prompt_name, latency_ms, raw_response, output = self.orchestrator.analyze(
                mode=mode,
                raw_input=case.raw_input,
                artifact_context=artifact_context,
            )
        except Exception as exc:
            db.add(
                AnalysisRun(
                    case_id=case.id,
                    status=AnalysisRunStatus.FAILED.value,
                    mode_used=mode.value,
                    model_name=self.settings.google_genai_model,
                    prompt_name="analysis",
                    error_message=str(exc),
                )
            )
            db.commit()
            raise

        run = AnalysisRun(
            case_id=case.id,
            status=AnalysisRunStatus.SUCCEEDED.value,
            mode_used=output.mode_used.value,
            model_name=self.settings.google_genai_model,
            prompt_name=prompt_name,
            raw_response_json=raw_response,
            normalized_output_json=serialize_analysis_output(output),
            latency_ms=latency_ms,
        )
        db.add(run)

        case.mode = output.mode_used.value
        case.detected_case_type = output.case_type.value
        case.urgency_level = output.urgency_level.value
        case.confidence = output.confidence
        case.structured_result_json = serialize_analysis_output(output)
        case.handoff_summary = output.handoff_summary

        self._replace_recommended_actions(db, case, output)
        db.commit()
        return self.get_case(db, case.id)

    def seed_case(self, db: Session, *, mode: CaseMode, raw_input: str) -> Case:
        created = self.create_case(db, CaseCreate(mode=mode, raw_input=raw_input))
        return self.analyze_case(db, created.id)

    def _replace_recommended_actions(
        self,
        db: Session,
        case: Case,
        output: NormalizedAnalysisOutput,
    ) -> None:
        for action in list(case.recommended_actions):
            db.delete(action)
        db.flush()

        for action in output.recommended_actions:
            db.add(
                RecommendedAction(
                    case_id=case.id,
                    priority=action.priority,
                    title=action.title,
                    description=action.description,
                    category=action.category,
                    rationale=action.rationale,
                    is_immediate=action.is_immediate,
                )
            )
