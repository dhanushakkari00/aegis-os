from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, object]:
    settings = get_settings()
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "ok",
        "gemini_configured": bool(settings.google_genai_api_key),
        "cloud_sql_connector_enabled": settings.cloud_sql_use_connector,
        "model": settings.google_genai_model,
    }
