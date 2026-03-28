"""Backend-only Google Maps resource lookup for Aegis OS.

Uses Geocoding plus the Places API (New) to locate nearby hospitals,
medical clinics, and disaster-safe shelter options without exposing
the Maps API key to the frontend.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import httpx

from app.core.config import Settings
from app.core.logging import get_logger
from app.schemas.enums import DetectedCaseType

logger = get_logger(__name__)

_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
_PLACES_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
_PLACES_TEXT_URL = "https://places.googleapis.com/v1/places:searchText"
_STATIC_MAP_URL = "https://maps.googleapis.com/maps/api/staticmap"
_PLACES_FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.googleMapsUri",
        "places.rating",
        "places.nationalPhoneNumber",
        "places.internationalPhoneNumber",
        "places.currentOpeningHours.openNow",
        "places.primaryType",
    ]
)


@dataclass
class NearbyPlace:
    """Normalized place record returned to the API layer."""

    name: str
    address: str
    lat: float
    lng: float
    place_id: str
    google_maps_uri: str | None
    resource_type: str
    phone_number: str | None = None
    rating: float | None = None
    open_now: bool | None = None
    primary_type: str | None = None


@dataclass
class ResourceBundle:
    """Grouped resource search result."""

    hospitals: list[NearbyPlace]
    clinics: list[NearbyPlace]
    ambulance_services: list[NearbyPlace]
    safe_houses: list[NearbyPlace]


@dataclass
class IncidentMapPoint:
    """Single dashboard incident marker."""

    label: str
    severity: str
    lat: float
    lng: float


class NearbyService:
    """Finds nearby hospitals, clinics, and shelters via Google Maps."""

    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.google_maps_api_key
        self.enabled = bool(self.api_key)

    def geocode(self, location_text: str) -> tuple[float, float] | None:
        """Convert a location string to ``(latitude, longitude)``."""
        if not self.enabled:
            logger.warning("Google Maps API key not configured — skipping geocode.")
            return None

        try:
            response = httpx.get(
                _GEOCODE_URL,
                params={"address": location_text, "key": self.api_key},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "OK" or not data.get("results"):
                logger.info("Geocoding returned no results for: %s", location_text)
                return None
            location = data["results"][0]["geometry"]["location"]
            return (location["lat"], location["lng"])
        except Exception as exc:
            logger.warning("Geocoding failed for '%s': %s", location_text, exc)
            return None

    def find_case_resources(
        self,
        *,
        lat: float,
        lng: float,
        case_type: DetectedCaseType,
    ) -> ResourceBundle:
        """Return grouped resources tailored to the analyzed case type."""
        hospitals = self.find_nearby_hospitals(lat=lat, lng=lng)
        clinics = self.find_nearby_clinics(lat=lat, lng=lng)
        ambulance_services = self.find_nearby_ambulance_services(lat=lat, lng=lng)
        safe_houses = (
            self.find_nearby_safe_houses(lat=lat, lng=lng)
            if case_type in {DetectedCaseType.DISASTER, DetectedCaseType.MIXED}
            else []
        )
        return ResourceBundle(
            hospitals=self._dedupe_places(hospitals),
            clinics=self._dedupe_places(clinics),
            ambulance_services=self._dedupe_places(ambulance_services),
            safe_houses=self._dedupe_places(safe_houses),
        )

    def find_nearby_hospitals(
        self,
        *,
        lat: float,
        lng: float,
        radius_m: int = 8000,
        max_results: int = 5,
    ) -> list[NearbyPlace]:
        places = self._search_nearby(
            lat=lat,
            lng=lng,
            included_types=["hospital"],
            radius_m=radius_m,
            max_results=max_results,
        )
        return [self._to_nearby_place(place, resource_type="hospital") for place in places]

    def find_nearby_clinics(
        self,
        *,
        lat: float,
        lng: float,
        radius_m: int = 8000,
        max_results: int = 5,
    ) -> list[NearbyPlace]:
        places = self._search_text(
            lat=lat,
            lng=lng,
            text_query="medical clinic urgent care",
            included_type="doctor",
            radius_m=radius_m,
            max_results=max_results,
        )
        return [self._to_nearby_place(place, resource_type="clinic") for place in places]

    def find_nearby_safe_houses(
        self,
        *,
        lat: float,
        lng: float,
        radius_m: int = 10000,
        max_results: int = 5,
    ) -> list[NearbyPlace]:
        primary_results = self._search_text(
            lat=lat,
            lng=lng,
            text_query="emergency shelter",
            included_type="lodging",
            radius_m=radius_m,
            max_results=max_results,
        )
        if primary_results:
            return [self._to_nearby_place(place, resource_type="safe_house") for place in primary_results]

        fallback_results = self._search_text(
            lat=lat,
            lng=lng,
            text_query="relief shelter safe shelter",
            included_type="lodging",
            radius_m=radius_m,
            max_results=max_results,
        )
        return [self._to_nearby_place(place, resource_type="safe_house") for place in fallback_results]

    def find_nearby_ambulance_services(
        self,
        *,
        lat: float,
        lng: float,
        radius_m: int = 10000,
        max_results: int = 5,
    ) -> list[NearbyPlace]:
        places = self._search_text(
            lat=lat,
            lng=lng,
            text_query="ambulance service emergency transport",
            included_type=None,
            radius_m=radius_m,
            max_results=max_results,
        )
        return [self._to_nearby_place(place, resource_type="ambulance_service") for place in places]

    def search(self, location_text: str, case_type: DetectedCaseType = DetectedCaseType.UNCLEAR) -> ResourceBundle:
        """Convenience wrapper for location-text lookup."""
        coords = self.geocode(location_text)
        if coords is None:
            return ResourceBundle(hospitals=[], clinics=[], ambulance_services=[], safe_houses=[])
        return self.find_case_resources(lat=coords[0], lng=coords[1], case_type=case_type)

    def fetch_static_map(
        self,
        *,
        incident_lat: float,
        incident_lng: float,
        bundle: ResourceBundle,
    ) -> tuple[bytes, str]:
        """Return a static map image for the incident and nearby resources."""
        if not self.enabled:
            raise RuntimeError("Google Maps API key not configured.")

        params: list[tuple[str, str]] = [
            ("size", "1200x720"),
            ("scale", "2"),
            ("maptype", "roadmap"),
            ("key", self.api_key or ""),
            ("markers", f"color:red|label:I|{incident_lat},{incident_lng}"),
        ]
        for resource in bundle.hospitals[:4]:
            params.append(("markers", f"color:blue|label:H|{resource.lat},{resource.lng}"))
        for resource in bundle.clinics[:4]:
            params.append(("markers", f"color:green|label:C|{resource.lat},{resource.lng}"))
        for resource in bundle.ambulance_services[:4]:
            params.append(("markers", f"color:orange|label:A|{resource.lat},{resource.lng}"))
        for resource in bundle.safe_houses[:4]:
            params.append(("markers", f"color:purple|label:S|{resource.lat},{resource.lng}"))

        response = httpx.get(_STATIC_MAP_URL, params=params, timeout=15)
        response.raise_for_status()
        return response.content, response.headers.get("content-type", "image/png")

    def fetch_incident_overview_map(self, points: Sequence[IncidentMapPoint]) -> tuple[bytes, str]:
        """Return a static dashboard map for active incidents."""
        if not self.enabled:
            raise RuntimeError("Google Maps API key not configured.")
        if not points:
            raise RuntimeError("No incident coordinates available.")

        center_lat = sum(point.lat for point in points) / len(points)
        center_lng = sum(point.lng for point in points) / len(points)
        params: list[tuple[str, str]] = [
            ("size", "1400x820"),
            ("scale", "2"),
            ("maptype", "roadmap"),
            ("zoom", "11"),
            ("center", f"{center_lat},{center_lng}"),
            ("key", self.api_key or ""),
        ]
        for point in points[:12]:
            params.append(
                (
                    "markers",
                    f"color:{self._severity_marker_color(point.severity)}|label:{self._severity_marker_label(point.severity)}|{point.lat},{point.lng}",
                )
            )

        response = httpx.get(_STATIC_MAP_URL, params=params, timeout=15)
        response.raise_for_status()
        return response.content, response.headers.get("content-type", "image/png")

    def _search_nearby(
        self,
        *,
        lat: float,
        lng: float,
        included_types: list[str],
        radius_m: int,
        max_results: int,
    ) -> list[dict]:
        if not self.enabled:
            return []

        payload = {
            "includedTypes": included_types,
            "maxResultCount": max_results,
            "rankPreference": "DISTANCE",
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lng,
                    },
                    "radius": float(radius_m),
                }
            },
        }
        return self._post_places(_PLACES_NEARBY_URL, payload)

    def _search_text(
        self,
        *,
        lat: float,
        lng: float,
        text_query: str,
        included_type: str | None,
        radius_m: int,
        max_results: int,
    ) -> list[dict]:
        if not self.enabled:
            return []

        payload: dict[str, object] = {
            "textQuery": text_query,
            "maxResultCount": max_results,
            "rankPreference": "DISTANCE",
            "locationBias": {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lng,
                    },
                    "radius": float(radius_m),
                }
            },
        }
        if included_type:
            payload["includedType"] = included_type
        return self._post_places(_PLACES_TEXT_URL, payload)

    def _post_places(self, url: str, payload: dict[str, object]) -> list[dict]:
        try:
            response = httpx.post(
                url,
                json=payload,
                headers={
                    "X-Goog-Api-Key": self.api_key or "",
                    "X-Goog-FieldMask": _PLACES_FIELD_MASK,
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            response.raise_for_status()
            return response.json().get("places", [])
        except Exception as exc:
            logger.warning("Google Places lookup failed: %s", exc)
            return []

    @staticmethod
    def _to_nearby_place(place: dict, *, resource_type: str) -> NearbyPlace:
        display_name = place.get("displayName", {}) or {}
        location = place.get("location", {}) or {}
        opening = place.get("currentOpeningHours", {}) or {}
        return NearbyPlace(
            name=display_name.get("text", "Unknown"),
            address=place.get("formattedAddress", ""),
            lat=location.get("latitude", 0.0),
            lng=location.get("longitude", 0.0),
            place_id=place.get("id", ""),
            google_maps_uri=place.get("googleMapsUri"),
            resource_type=resource_type,
            phone_number=place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber"),
            rating=place.get("rating"),
            open_now=opening.get("openNow"),
            primary_type=place.get("primaryType"),
        )

    @staticmethod
    def _dedupe_places(places: list[NearbyPlace]) -> list[NearbyPlace]:
        unique: list[NearbyPlace] = []
        seen: set[str] = set()
        for place in places:
            key = place.place_id or f"{place.name}|{place.address}"
            if key in seen:
                continue
            seen.add(key)
            unique.append(place)
        return unique

    @staticmethod
    def _severity_marker_color(severity: str) -> str:
        if severity == "critical":
            return "red"
        if severity == "high":
            return "orange"
        if severity == "moderate":
            return "yellow"
        return "blue"

    @staticmethod
    def _severity_marker_label(severity: str) -> str:
        return severity[:1].upper() if severity else "I"
