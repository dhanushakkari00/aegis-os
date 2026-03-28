"""Tests for the health endpoint."""

from __future__ import annotations


def test_health_returns_ok(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "services" in payload
    assert payload["services"]["database"] == "ok"


def test_health_reports_gemini_status(client) -> None:
    response = client.get("/api/v1/health")
    payload = response.json()
    assert payload["services"]["gemini"] in ("configured", "not_configured")


def test_health_reports_gcs_status(client) -> None:
    response = client.get("/api/v1/health")
    payload = response.json()
    assert payload["services"]["gcs_artifact_storage"] in ("ok", "not_configured", "error")
