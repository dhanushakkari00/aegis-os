from __future__ import annotations

from unittest.mock import patch

from app.core.config import Settings
from app.services.nearby_service import NearbyService


def test_find_nearby_hospitals_maps_response_to_resource_shape() -> None:
    service = NearbyService(Settings(google_maps_api_key="TEST_KEY"))

    with patch("httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "places": [
                {
                    "id": "place_123",
                    "displayName": {"text": "Apollo Hospital"},
                    "location": {"latitude": 12.97, "longitude": 77.59},
                    "formattedAddress": "123 Main St",
                    "nationalPhoneNumber": "1234567890",
                    "rating": 4.5,
                }
            ]
        }

        results = service.find_nearby_hospitals(lat=12.97, lng=77.59)

    assert len(results) == 1
    assert results[0].name == "Apollo Hospital"
    assert results[0].phone_number == "1234567890"


def test_find_nearby_hospitals_returns_empty_when_google_maps_errors() -> None:
    service = NearbyService(Settings(google_maps_api_key="TEST_KEY"))

    with patch("httpx.post") as mock_post:
        mock_post.return_value.status_code = 500
        results = service.find_nearby_hospitals(lat=12.97, lng=77.59)

    assert results == []
