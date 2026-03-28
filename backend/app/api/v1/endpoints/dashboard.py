from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.case import DashboardSummaryResponse
from app.services.case_service import CaseService
from app.services.dashboard_service import DashboardService
from app.services.nearby_service import IncidentMapPoint, NearbyService

router = APIRouter()


def get_dashboard_service() -> DashboardService:
    case_service = CaseService(get_settings())
    return DashboardService(case_service)


def get_nearby_service() -> NearbyService:
    return NearbyService(get_settings())


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    db: Session = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummaryResponse:
    return service.summary(db)


@router.get("/incident-map")
def dashboard_incident_map(
    db: Session = Depends(get_db),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    nearby_service: NearbyService = Depends(get_nearby_service),
) -> Response:
    summary = dashboard_service.summary(db)
    points = [
        IncidentMapPoint(
            label=pulse.label,
            severity=pulse.severity.value if hasattr(pulse.severity, "value") else str(pulse.severity),
            lat=float(pulse.lat),
            lng=float(pulse.lng),
        )
        for pulse in summary.incident_pulses
        if pulse.lat is not None and pulse.lng is not None
    ]
    if not points:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No incident coordinates available for the dashboard map.",
        )

    try:
        image_bytes, content_type = nearby_service.fetch_incident_overview_map(points)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to generate dashboard incident map.",
        ) from exc

    return Response(content=image_bytes, media_type=content_type)
