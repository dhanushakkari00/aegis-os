from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.case import (
    AnalyzeCaseRequest,
    CaseCreate,
    CaseDetailResponse,
    CaseSummaryResponse,
    ExportJSONResponse,
)
from app.services.artifact_service import ArtifactService
from app.services.case_service import CaseService
from app.services.export_service import ExportService

router = APIRouter()


def get_case_service() -> CaseService:
    return CaseService(get_settings())


def get_artifact_service() -> ArtifactService:
    return ArtifactService(get_settings())


def get_export_service() -> ExportService:
    return ExportService()


@router.post("", response_model=CaseDetailResponse, status_code=status.HTTP_201_CREATED)
def create_case(payload: CaseCreate, db: Session = Depends(get_db), service: CaseService = Depends(get_case_service)) -> CaseDetailResponse:
    case = service.create_case(db, payload)
    return CaseDetailResponse.model_validate(_serialize_case(case))


@router.get("", response_model=list[CaseSummaryResponse])
def list_cases(db: Session = Depends(get_db), service: CaseService = Depends(get_case_service)) -> list[CaseSummaryResponse]:
    cases = service.list_cases(db)
    return [CaseSummaryResponse.model_validate(case) for case in cases]


@router.get("/{case_id}", response_model=CaseDetailResponse)
def get_case(case_id: str, db: Session = Depends(get_db), service: CaseService = Depends(get_case_service)) -> CaseDetailResponse:
    try:
        case = service.get_case(db, case_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CaseDetailResponse.model_validate(_serialize_case(case))


@router.post("/{case_id}/upload", response_model=CaseDetailResponse)
async def upload_artifact(
    case_id: str,
    file: UploadFile = File(...),
    artifact_type: str = Form(default="attachment"),
    db: Session = Depends(get_db),
    case_service: CaseService = Depends(get_case_service),
    artifact_service: ArtifactService = Depends(get_artifact_service),
) -> CaseDetailResponse:
    try:
        case = case_service.get_case(db, case_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    await artifact_service.upload(db=db, case=case, file=file, artifact_type=artifact_type)
    refreshed = case_service.get_case(db, case_id)
    return CaseDetailResponse.model_validate(_serialize_case(refreshed))


@router.post("/{case_id}/analyze", response_model=CaseDetailResponse)
def analyze_case(
    case_id: str,
    payload: AnalyzeCaseRequest | None = None,
    db: Session = Depends(get_db),
    service: CaseService = Depends(get_case_service),
) -> CaseDetailResponse:
    try:
        case = service.analyze_case(db, case_id, payload.mode_override if payload else None)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CaseDetailResponse.model_validate(_serialize_case(case))


@router.get("/{case_id}/export/json", response_model=ExportJSONResponse)
def export_json(
    case_id: str,
    db: Session = Depends(get_db),
    case_service: CaseService = Depends(get_case_service),
    export_service: ExportService = Depends(get_export_service),
) -> ExportJSONResponse:
    try:
        case = case_service.get_case(db, case_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ExportJSONResponse.model_validate(export_service.export_json(case))


@router.get("/{case_id}/export/handoff", response_class=PlainTextResponse)
def export_handoff(
    case_id: str,
    db: Session = Depends(get_db),
    case_service: CaseService = Depends(get_case_service),
    export_service: ExportService = Depends(get_export_service),
) -> str:
    try:
        case = case_service.get_case(db, case_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return export_service.export_handoff(case)


def _serialize_case(case) -> dict:
    structured = case.structured_result_json
    recommended_actions = structured.get("recommended_actions", []) if structured else []
    return {
        "id": case.id,
        "mode": case.mode,
        "raw_input": case.raw_input,
        "detected_case_type": case.detected_case_type,
        "urgency_level": case.urgency_level,
        "confidence": case.confidence,
        "structured_result_json": structured,
        "handoff_summary": case.handoff_summary,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
        "artifacts": case.artifacts,
        "analysis_runs": case.analysis_runs,
        "recommended_actions": recommended_actions,
    }

