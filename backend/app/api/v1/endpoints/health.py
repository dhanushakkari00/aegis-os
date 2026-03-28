"""Health and readiness checks for Aegis OS backend.

Reports the status of all connected Google Cloud services (database,
Gemini AI, GCS artifact storage, Cloud Logging) so operators and Cloud Run
health probes can quickly verify system readiness.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, object]:
    """Return a comprehensive service-health report.

    Checks:
    * **Database** — executes a trivial query to confirm connectivity.
    * **Gemini** — reports whether the API key is configured.
    * **Google Maps** — reports whether resource routing lookups are configured.
    * **Gmail** — reports whether operator handoff notifications are configured.
    * **GCS** — reports whether artifact storage is configured.
    * **Cloud SQL** — reports whether the managed connector is active.
    * **Cloud Logging** — reports whether the GCP project is set.
    """
    settings = get_settings()

    # Database check
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"

    # GCS check
    gcs_status = "not_configured"
    if settings.gcs_bucket_name:
        try:
            from google.cloud.storage import Client as GCSClient

            client = GCSClient(project=settings.google_cloud_project)
            bucket = client.bucket(settings.gcs_bucket_name)
            bucket.reload()
            gcs_status = "ok"
        except Exception:
            gcs_status = "error"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "services": {
            "database": db_status,
            "gemini": "configured" if settings.google_genai_api_key else "not_configured",
            "google_maps": "configured" if settings.google_maps_api_key else "not_configured",
            "gmail": (
                "configured"
                if all(
                    [
                        settings.gmail_client_id,
                        settings.gmail_client_secret,
                        settings.gmail_refresh_token,
                        settings.gmail_from_email,
                    ]
                ) and settings.gmail_send_case_notifications
                else "not_configured"
            ),
            "gcs_artifact_storage": gcs_status,
            "cloud_sql_connector": "enabled" if settings.cloud_sql_use_connector else "disabled",
            "cloud_logging": "enabled" if settings.google_cloud_project else "disabled",
        },
        "model": settings.google_genai_model,
    }
