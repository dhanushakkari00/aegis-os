"""Tests for the dashboard endpoint."""

from __future__ import annotations

from app.seed import DISASTER_DEMO, MEDICAL_DEMO


def test_dashboard_summary_empty(client) -> None:
    """Dashboard should return valid structure even with no cases."""
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["totals"][0]["label"] == "Active Cases"
    assert payload["totals"][0]["value"] == 0
    assert len(payload["severity_distribution"]) == 4
    assert payload["queue"] == []


def test_dashboard_summary_with_cases(client) -> None:
    """Dashboard metrics should reflect seeded and analyzed cases."""
    client.post("/api/v1/cases", json={"mode": "medical_triage", "raw_input": MEDICAL_DEMO})
    client.post("/api/v1/cases", json={"mode": "disaster_response", "raw_input": DISASTER_DEMO})

    cases = client.get("/api/v1/cases").json()
    for case in cases:
        client.post(f"/api/v1/cases/{case['id']}/analyze", json={})

    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["totals"][0]["value"] == 2
    assert len(payload["queue"]) == 2
    assert len(payload["incident_pulses"]) == 2


def test_dashboard_summary_includes_browser_coordinates(client) -> None:
    """Dashboard pulses should surface browser-shared coordinates for map rendering."""
    client.post(
        "/api/v1/cases",
        json={
            "mode": "auto_detect",
            "raw_input": (
                "Caller greeting.\n\nDevice location shared by browser: latitude 12.971599, "
                "longitude 77.594566, accuracy 8m, captured_at 2026-03-28T08:00:00Z."
            ),
        },
    )

    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["incident_pulses"][0]["lat"] == 12.971599
    assert payload["incident_pulses"][0]["lng"] == 77.594566
