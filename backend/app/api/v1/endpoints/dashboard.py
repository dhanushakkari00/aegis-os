from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.case import DashboardSummaryResponse
from app.services.case_service import CaseService
from app.services.dashboard_service import DashboardService

router = APIRouter()


def get_dashboard_service() -> DashboardService:
    case_service = CaseService(get_settings())
    return DashboardService(case_service)


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    db: Session = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummaryResponse:
    return service.summary(db)

