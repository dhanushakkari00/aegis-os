from __future__ import annotations

from app.seed import DISASTER_DEMO, MEDICAL_DEMO
from app.services.gmail_service import EmailDeliveryResult, GmailService


def test_create_and_analyze_medical_case(client) -> None:
    create_response = client.post(
        "/api/v1/cases",
        json={"mode": "medical_triage", "raw_input": MEDICAL_DEMO},
    )
    assert create_response.status_code == 201
    case_id = create_response.json()["id"]

    analyze_response = client.post(f"/api/v1/cases/{case_id}/analyze", json={})
    assert analyze_response.status_code == 200
    data = analyze_response.json()
    assert data["urgency_level"] in {"high", "critical"}
    assert data["structured_result_json"]["case_type"] == "medical"
    assert len(data["recommended_actions"]) >= 1

    export_response = client.get(f"/api/v1/cases/{case_id}/export/json")
    assert export_response.status_code == 200
    assert export_response.json()["payload"]["handoff_summary"]


def test_upload_text_artifact(client) -> None:
    create_response = client.post(
        "/api/v1/cases",
        json={"mode": "auto_detect", "raw_input": DISASTER_DEMO},
    )
    case_id = create_response.json()["id"]

    upload_response = client.post(
        f"/api/v1/cases/{case_id}/upload",
        files={"file": ("notes.txt", b"Water still rising near school entrance", "text/plain")},
        data={"artifact_type": "field_note"},
    )
    assert upload_response.status_code == 200
    artifacts = upload_response.json()["artifacts"]
    assert artifacts[0]["artifact_type"] == "field_note"
    assert "Water still rising" in artifacts[0]["content_excerpt"]


def test_upload_recorded_audio_artifact(client) -> None:
    create_response = client.post(
        "/api/v1/cases",
        json={"mode": "medical_triage", "raw_input": MEDICAL_DEMO},
    )
    case_id = create_response.json()["id"]

    upload_response = client.post(
        f"/api/v1/cases/{case_id}/upload",
        files={"file": ("voice-note.webm", b"fake-webm-audio", "audio/webm;codecs=opus")},
        data={"artifact_type": "audio"},
    )
    assert upload_response.status_code == 200
    artifact = upload_response.json()["artifacts"][0]
    assert artifact["artifact_type"] == "audio"
    assert artifact["mime_type"] == "audio/webm"


def test_dashboard_summary(client) -> None:
    client.post("/api/v1/cases", json={"mode": "medical_triage", "raw_input": MEDICAL_DEMO})
    client.post("/api/v1/cases", json={"mode": "disaster_response", "raw_input": DISASTER_DEMO})

    list_response = client.get("/api/v1/cases")
    for case in list_response.json():
        client.post(f"/api/v1/cases/{case['id']}/analyze", json={})

    summary_response = client.get("/api/v1/dashboard/summary")
    assert summary_response.status_code == 200
    payload = summary_response.json()
    assert len(payload["totals"]) == 3
    assert len(payload["severity_distribution"]) == 4


def test_analyze_case_sends_gmail_handoff_when_contact_email_exists(client, monkeypatch) -> None:
    deliveries: list[tuple[str, str]] = []

    monkeypatch.setattr(GmailService, "is_configured", lambda self: True)

    def fake_send(self, *, case, recipient_email):
        deliveries.append((case.id, recipient_email))
        return EmailDeliveryResult(delivered=True, provider_message_id="gmail-message-id")

    monkeypatch.setattr(GmailService, "send_case_summary", fake_send)

    create_response = client.post(
        "/api/v1/cases",
        json={
            "mode": "medical_triage",
            "raw_input": MEDICAL_DEMO,
            "contact_email": "ops@example.com",
        },
    )
    case_id = create_response.json()["id"]

    analyze_response = client.post(f"/api/v1/cases/{case_id}/analyze", json={})
    assert analyze_response.status_code == 200
    payload = analyze_response.json()
    assert payload["contact_email"] == "ops@example.com"
    assert payload["last_notification_sent_at"] is not None
    assert payload["last_notification_error"] is None
    assert deliveries == [(case_id, "ops@example.com")]


def test_notify_email_endpoint_resends_case_handoff(client, monkeypatch) -> None:
    deliveries: list[str] = []

    monkeypatch.setattr(GmailService, "is_configured", lambda self: True)

    def fake_send(self, *, case, recipient_email):
        deliveries.append(recipient_email)
        return EmailDeliveryResult(delivered=True, provider_message_id="gmail-message-id")

    monkeypatch.setattr(GmailService, "send_case_summary", fake_send)

    create_response = client.post(
        "/api/v1/cases",
        json={
            "mode": "medical_triage",
            "raw_input": MEDICAL_DEMO,
            "contact_email": "ops@example.com",
        },
    )
    case_id = create_response.json()["id"]
    client.post(f"/api/v1/cases/{case_id}/analyze", json={})

    resend_response = client.post(f"/api/v1/cases/{case_id}/notify/email", json={})
    assert resend_response.status_code == 200
    payload = resend_response.json()
    assert payload["last_notification_sent_at"] is not None
    assert deliveries == ["ops@example.com", "ops@example.com"]


def test_notify_email_endpoint_requires_recipient_email(client) -> None:
    create_response = client.post(
        "/api/v1/cases",
        json={"mode": "medical_triage", "raw_input": MEDICAL_DEMO},
    )
    case_id = create_response.json()["id"]

    resend_response = client.post(f"/api/v1/cases/{case_id}/notify/email", json={})
    assert resend_response.status_code == 400
    assert resend_response.json()["detail"] == "No recipient email is stored for this case."
