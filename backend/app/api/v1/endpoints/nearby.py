"""Nearby facility lookup endpoints.

Provides hospital/emergency facility search using Google Maps Places API,
either by case ID (using the AI-extracted location) or a raw location string.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.services.case_service import CaseService
from app.services.nearby_service import NearbyPlace, NearbyService

router = APIRouter()


class NearbyPlaceResponse(BaseModel):
    """Single nearby facility."""

    name: str
    address: str
    lat: float
    lng: float
    place_id: str
    rating: float | None = None
    open_now: bool | None = None


class NearbySearchResponse(BaseModel):
    """Response containing the search location and results."""

    query_location: str
    lat: float | None = None
    lng: float | None = None
    hospitals: list[NearbyPlaceResponse]


def get_nearby_service() -> NearbyService:
    """Return a NearbyService instance."""
    return NearbyService(get_settings())


def get_case_service() -> CaseService:
    """Return a CaseService instance."""
    return CaseService(get_settings())


def _to_response(place: NearbyPlace) -> NearbyPlaceResponse:
    return NearbyPlaceResponse(
        name=place.name,
        address=place.address,
        lat=place.lat,
        lng=place.lng,
        place_id=place.place_id,
        rating=place.rating,
        open_now=place.open_now,
    )


@router.get("/cases/{case_id}/nearby-hospitals", response_model=NearbySearchResponse)
def case_nearby_hospitals(
    case_id: str,
    db: Session = Depends(get_db),
    case_service: CaseService = Depends(get_case_service),
    nearby_service: NearbyService = Depends(get_nearby_service),
) -> NearbySearchResponse:
    """Find hospitals near the AI-extracted location for a given case."""
    try:
        case = case_service.get_case(db, case_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    structured = case.structured_result_json or {}
    location = (
        structured.get("extracted_location")
        or (structured.get("structured", {}).get("disaster", {}) or {}).get("location")
    )
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No location could be extracted from this case.",
        )

    coords = nearby_service.geocode(location)
    hospitals = nearby_service.find_nearby_hospitals(coords[0], coords[1]) if coords else []

    return NearbySearchResponse(
        query_location=location,
        lat=coords[0] if coords else None,
        lng=coords[1] if coords else None,
        hospitals=[_to_response(h) for h in hospitals],
    )


@router.get("/nearby", response_model=NearbySearchResponse)
def search_nearby(
    location: str = Query(..., min_length=2, description="Location to search near"),
    nearby_service: NearbyService = Depends(get_nearby_service),
) -> NearbySearchResponse:
    """Search for hospitals near a given location string."""
    coords = nearby_service.geocode(location)
    hospitals = nearby_service.find_nearby_hospitals(coords[0], coords[1]) if coords else []

    return NearbySearchResponse(
        query_location=location,
        lat=coords[0] if coords else None,
        lng=coords[1] if coords else None,
        hospitals=[_to_response(h) for h in hospitals],
    )
