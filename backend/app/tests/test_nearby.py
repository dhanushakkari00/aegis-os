"""Tests for the nearby hospitals endpoint."""

from __future__ import annotations

from app.seed import MEDICAL_DEMO


def test_nearby_hospitals_no_location(client) -> None:
    """When a case has no extracted location, endpoint returns 404."""
    create_response = client.post(
        "/api/v1/cases",
        json={"mode": "medical_triage", "raw_input": MEDICAL_DEMO},
    )
    case_id = create_response.json()["id"]

    response = client.get(f"/api/v1/cases/{case_id}/nearby-hospitals")
    assert response.status_code == 404


def test_standalone_nearby_requires_location(client) -> None:
    """The standalone /nearby endpoint requires a location query param."""
    response = client.get("/api/v1/nearby")
    assert response.status_code == 422


def test_standalone_nearby_with_location(client) -> None:
    """The standalone /nearby responds with the right structure."""
    response = client.get("/api/v1/nearby?location=New+York")
    assert response.status_code == 200
    payload = response.json()
    assert payload["query_location"] == "New York"
    assert "hospitals" in payload
