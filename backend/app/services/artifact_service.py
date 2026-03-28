from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from google.cloud import storage
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import sanitize_filename
from app.models.artifact import Artifact
from app.models.case import Case


class ArtifactService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def upload(self, *, db: Session, case: Case, file: UploadFile, artifact_type: str) -> Artifact:
        if file.content_type not in self.settings.allowed_upload_mime_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type.",
            )

        contents = await file.read()
        max_size_bytes = self.settings.max_upload_size_mb * 1024 * 1024
        if len(contents) > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds {self.settings.max_upload_size_mb} MB limit.",
            )

        safe_name = sanitize_filename(file.filename or "artifact")
        storage_provider = "local"
        storage_uri = self._store_locally(case.id, safe_name, contents)

        if self.settings.gcs_bucket_name:
            try:
                storage_uri = self._store_in_gcs(case.id, safe_name, contents, file.content_type or "application/octet-stream")
                storage_provider = "gcs"
            except Exception:
                storage_provider = "local"

        excerpt = None
        if file.content_type == "text/plain":
            excerpt = contents.decode("utf-8", errors="ignore")[:1000]

        artifact = Artifact(
            case_id=case.id,
            filename=safe_name,
            mime_type=file.content_type or "application/octet-stream",
            size_bytes=len(contents),
            artifact_type=artifact_type or "attachment",
            storage_provider=storage_provider,
            storage_uri=storage_uri,
            content_excerpt=excerpt,
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return artifact

    def _store_locally(self, case_id: str, filename: str, contents: bytes) -> str:
        storage_dir = Path(__file__).resolve().parents[2] / "storage" / case_id
        storage_dir.mkdir(parents=True, exist_ok=True)
        destination = storage_dir / filename
        destination.write_bytes(contents)
        return str(destination)

    def _store_in_gcs(self, case_id: str, filename: str, contents: bytes, content_type: str) -> str:
        client = storage.Client(project=self.settings.google_cloud_project or None)
        bucket = client.bucket(self.settings.gcs_bucket_name)
        blob = bucket.blob(f"cases/{case_id}/{filename}")
        blob.upload_from_string(contents, content_type=content_type)
        return f"gs://{bucket.name}/{blob.name}"

