"""Tests for the health endpoint."""

from __future__ import annotations

from types import SimpleNamespace


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


def test_health_reports_google_maps_status(client) -> None:
    response = client.get("/api/v1/health")
    payload = response.json()
    assert payload["services"]["google_maps"] in ("configured", "not_configured")


def test_health_reports_gmail_status(client, monkeypatch) -> None:
    fake_settings = SimpleNamespace(
        google_genai_api_key="set",
        google_maps_api_key="set",
        gmail_client_id="client",
        gmail_client_secret="secret",
        gmail_refresh_token="refresh",
        gmail_from_email="alerts@example.com",
        gmail_send_case_notifications=True,
        gcs_bucket_name=None,
        cloud_sql_use_connector=False,
        google_cloud_project=None,
        google_genai_model="gemini-2.5-flash",
    )

    monkeypatch.setattr("app.api.v1.endpoints.health.get_settings", lambda: fake_settings)

    response = client.get("/api/v1/health")
    payload = response.json()
    assert payload["services"]["gmail"] == "configured"
