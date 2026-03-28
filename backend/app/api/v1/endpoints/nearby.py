"""Nearby resource lookup endpoints for medical and disaster cases."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.enums import DetectedCaseType
from app.services.case_service import CaseService
from app.services.location_resolver import resolve_case_coords, resolve_case_location
from app.services.nearby_service import NearbyPlace, NearbyService, ResourceBundle

router = APIRouter()


class NearbyResourceResponse(BaseModel):
    """Single nearby facility or shelter."""

    name: str
    address: str
    lat: float
    lng: float
    place_id: str
    google_maps_uri: str | None = None
    resource_type: str
    phone_number: str | None = None
    rating: float | None = None
    open_now: bool | None = None
    primary_type: str | None = None


class NearbyResourcesResponse(BaseModel):
    """Grouped resource payload for operator routing."""

    query_location: str
    case_type: DetectedCaseType
    lat: float | None = None
    lng: float | None = None
    hospitals: list[NearbyResourceResponse]
    clinics: list[NearbyResourceResponse]
    ambulance_services: list[NearbyResourceResponse]
    safe_houses: list[NearbyResourceResponse]


def get_nearby_service() -> NearbyService:
    return NearbyService(get_settings())


def get_case_service() -> CaseService:
    return CaseService(get_settings())


def _to_response(place: NearbyPlace) -> NearbyResourceResponse:
    return NearbyResourceResponse(
        name=place.name,
        address=place.address,
        lat=place.lat,
        lng=place.lng,
        place_id=place.place_id,
        google_maps_uri=place.google_maps_uri,
        resource_type=place.resource_type,
        phone_number=place.phone_number,
        rating=place.rating,
        open_now=place.open_now,
        primary_type=place.primary_type,
    )


def _bundle_response(
    *,
    query_location: str,
    case_type: DetectedCaseType,
    coords: tuple[float, float] | None,
    bundle: ResourceBundle,
) -> NearbyResourcesResponse:
    return NearbyResourcesResponse(
        query_location=query_location,
        case_type=case_type,
        lat=coords[0] if coords else None,
        lng=coords[1] if coords else None,
        hospitals=[_to_response(item) for item in bundle.hospitals],
        clinics=[_to_response(item) for item in bundle.clinics],
        ambulance_services=[_to_response(item) for item in bundle.ambulance_services],
        safe_houses=[_to_response(item) for item in bundle.safe_houses],
    )


@router.get("/cases/{case_id}/nearby-resources", response_model=NearbyResourcesResponse)
def case_nearby_resources(
    case_id: str,
    db: Session = Depends(get_db),
    case_service: CaseService = Depends(get_case_service),
    nearby_service: NearbyService = Depends(get_nearby_service),
) -> NearbyResourcesResponse:
    """Find routing resources near the analyzed case location."""
    try:
        case = case_service.get_case(db, case_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    location = resolve_case_location(case)
    coords = resolve_case_coords(case)
    if not location and not coords:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No usable location could be extracted from this case.",
        )

    case_type = DetectedCaseType(case.detected_case_type)
    resolved_coords = coords or (nearby_service.geocode(location) if location else None)
    bundle = (
        nearby_service.find_case_resources(
            lat=resolved_coords[0],
            lng=resolved_coords[1],
            case_type=case_type,
        )
        if resolved_coords
        else ResourceBundle(hospitals=[], clinics=[], ambulance_services=[], safe_houses=[])
    )
    return _bundle_response(
        query_location=location or f"{resolved_coords[0]:.5f}, {resolved_coords[1]:.5f}",
        case_type=case_type,
        coords=resolved_coords,
        bundle=bundle,
    )


@router.get("/cases/{case_id}/nearby-hospitals", response_model=NearbyResourcesResponse)
def case_nearby_hospitals(
    case_id: str,
    db: Session = Depends(get_db),
    case_service: CaseService = Depends(get_case_service),
    nearby_service: NearbyService = Depends(get_nearby_service),
) -> NearbyResourcesResponse:
    """Backward-compatible alias for case nearby resources."""
    return case_nearby_resources(
        case_id=case_id,
        db=db,
        case_service=case_service,
        nearby_service=nearby_service,
    )


@router.get("/nearby", response_model=NearbyResourcesResponse)
def search_nearby(
    location: str = Query(..., min_length=2, description="Location to search near"),
    case_type: DetectedCaseType = Query(
        default=DetectedCaseType.UNCLEAR,
        description="Case type used to decide which resource groups matter most.",
    ),
    nearby_service: NearbyService = Depends(get_nearby_service),
) -> NearbyResourcesResponse:
    """Search for hospitals, clinics, and shelters near a location string."""
    coords = nearby_service.geocode(location)
    bundle = nearby_service.search(location_text=location, case_type=case_type)
    return _bundle_response(
        query_location=location,
        case_type=case_type,
        coords=coords,
        bundle=bundle,
    )


@router.get("/cases/{case_id}/resource-map")
def case_resource_map(
    case_id: str,
    db: Session = Depends(get_db),
    case_service: CaseService = Depends(get_case_service),
    nearby_service: NearbyService = Depends(get_nearby_service),
) -> Response:
    """Return a backend-proxied static map preview for the case and its resources."""
    try:
        case = case_service.get_case(db, case_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    coords = resolve_case_coords(case)
    location = resolve_case_location(case)
    resolved_coords = coords or (nearby_service.geocode(location) if location else None)
    if not resolved_coords:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No usable location could be extracted from this case.",
        )

    case_type = DetectedCaseType(case.detected_case_type)
    bundle = nearby_service.find_case_resources(
        lat=resolved_coords[0],
        lng=resolved_coords[1],
        case_type=case_type,
    )
    try:
        image_bytes, content_type = nearby_service.fetch_static_map(
            incident_lat=resolved_coords[0],
            incident_lng=resolved_coords[1],
            bundle=bundle,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to generate resource map preview.",
        ) from exc

    return Response(content=image_bytes, media_type=content_type)
