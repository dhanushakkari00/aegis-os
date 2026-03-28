"""Tests for security headers and rate limiting."""

from __future__ import annotations

from app.core.security import sanitize_filename


def test_security_headers_present(client) -> None:
    """Every response should carry hardened security headers."""
    response = client.get("/api/v1/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "same-origin"
    assert "Content-Security-Policy" in response.headers
    assert "Strict-Transport-Security" in response.headers
    assert "X-Request-ID" in response.headers
    assert "X-Response-Time-Ms" in response.headers
    assert response.headers.get("Permissions-Policy") == "camera=(), microphone=(self), geolocation=(self)"


def test_csp_header_blocks_frames(client) -> None:
    """CSP should include frame-ancestors 'none'."""
    response = client.get("/api/v1/health")
    csp = response.headers.get("Content-Security-Policy", "")
    assert "frame-ancestors 'none'" in csp


def test_sanitize_filename_strips_dangerous_chars() -> None:
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("hello world.txt") == "hello-world.txt"
    assert sanitize_filename("") == "artifact"
    assert sanitize_filename("normal-file.pdf") == "normal-file.pdf"


def test_sanitize_filename_handles_path_traversal() -> None:
    assert sanitize_filename("/secret/../../../file.txt") == "file.txt"


def test_delete_case(client) -> None:
    """DELETE should remove the case and return confirmation."""
    create_response = client.post(
        "/api/v1/cases",
        json={"mode": "auto_detect", "raw_input": "Severe flooding reported in downtown area with multiple people trapped"},
    )
    case_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/v1/cases/{case_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    get_response = client.get(f"/api/v1/cases/{case_id}")
    assert get_response.status_code == 404


def test_update_case(client) -> None:
    """PATCH should update and return the modified case."""
    create_response = client.post(
        "/api/v1/cases",
        json={"mode": "auto_detect", "raw_input": "Patient reports severe headache for two hours"},
    )
    case_id = create_response.json()["id"]

    patch_response = client.patch(
        f"/api/v1/cases/{case_id}",
        json={"mode": "medical_triage"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["mode"] == "medical_triage"


def test_invalid_input_returns_422(client) -> None:
    """Creating a case with too-short input should return 422."""
    response = client.post("/api/v1/cases", json={"mode": "auto_detect", "raw_input": "   "})
    assert response.status_code == 422


def test_case_not_found_returns_404(client) -> None:
    """Requesting a non-existent case should return 404."""
    response = client.get("/api/v1/cases/nonexistent-id")
    assert response.status_code == 404
