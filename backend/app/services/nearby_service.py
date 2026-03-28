"""Google Maps Places API service for nearby facility lookup.

Provides geocoding of location strings and nearby hospital/emergency
facility search using the Google Maps Places (New) API.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"


@dataclass
class NearbyPlace:
    """A nearby facility returned by the Places API."""

    name: str
    address: str
    lat: float
    lng: float
    place_id: str
    rating: float | None = None
    open_now: bool | None = None
    types: list[str] | None = None


class NearbyService:
    """Finds nearby hospitals and emergency facilities via Google Maps."""

    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.google_maps_api_key
        self.enabled = bool(self.api_key)

    def geocode(self, location_text: str) -> tuple[float, float] | None:
        """Convert a location string to (latitude, longitude).

        Returns *None* when the API is not configured or geocoding fails.
        """
        if not self.enabled:
            logger.warning("Google Maps API key not configured — skipping geocode.")
            return None

        try:
            response = httpx.get(
                _GEOCODE_URL,
                params={"address": location_text, "key": self.api_key},
                timeout=10,
            )
            data = response.json()
            if data.get("status") != "OK" or not data.get("results"):
                logger.info("Geocoding returned no results for: %s", location_text)
                return None
            loc = data["results"][0]["geometry"]["location"]
            return (loc["lat"], loc["lng"])
        except Exception as exc:
            logger.warning("Geocoding failed for '%s': %s", location_text, exc)
            return None

    def find_nearby_hospitals(
        self,
        lat: float,
        lng: float,
        radius_m: int = 5000,
        max_results: int = 5,
    ) -> list[NearbyPlace]:
        """Search for nearby hospitals within *radius_m* metres of the given coordinates."""
        if not self.enabled:
            return []

        try:
            response = httpx.get(
                _NEARBY_URL,
                params={
                    "location": f"{lat},{lng}",
                    "radius": radius_m,
                    "type": "hospital",
                    "key": self.api_key,
                },
                timeout=10,
            )
            data = response.json()
            if data.get("status") not in ("OK", "ZERO_RESULTS"):
                logger.warning("Nearby search status: %s", data.get("status"))
                return []

            places: list[NearbyPlace] = []
            for result in data.get("results", [])[:max_results]:
                loc = result.get("geometry", {}).get("location", {})
                places.append(
                    NearbyPlace(
                        name=result.get("name", "Unknown"),
                        address=result.get("vicinity", ""),
                        lat=loc.get("lat", 0),
                        lng=loc.get("lng", 0),
                        place_id=result.get("place_id", ""),
                        rating=result.get("rating"),
                        open_now=result.get("opening_hours", {}).get("open_now"),
                        types=result.get("types"),
                    )
                )
            return places
        except Exception as exc:
            logger.warning("Nearby hospital search failed: %s", exc)
            return []

    def search(self, location_text: str) -> list[NearbyPlace]:
        """Convenience: geocode a string then find nearby hospitals."""
        coords = self.geocode(location_text)
        if coords is None:
            return []
        return self.find_nearby_hospitals(coords[0], coords[1])
