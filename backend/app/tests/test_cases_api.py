from __future__ import annotations

from app.seed import DISASTER_DEMO, MEDICAL_DEMO


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
