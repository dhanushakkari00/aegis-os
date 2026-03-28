from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile, status
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
        local_path = self._store_locally(case.id, safe_name, contents)
        storage_provider = "local"
        storage_uri = local_path

        excerpt = None
        if file.content_type == "text/plain":
            excerpt = contents.decode("utf-8", errors="ignore")[:1000]

        artifact = Artifact(
            case_id=case.id,
            filename=safe_name,
            mime_type=file.content_type or "application/octet-stream",
            size_bytes=len(contents),
            artifact_type=artifact_type or self._infer_artifact_type(file.content_type or ""),
            storage_provider=storage_provider,
            storage_uri=storage_uri,
            local_path=local_path,
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

    def _infer_artifact_type(self, mime_type: str) -> str:
        if mime_type.startswith("image/"):
            return "image"
        if mime_type.startswith("audio/"):
            return "audio"
        if mime_type == "application/pdf":
            return "document"
        if mime_type.startswith("text/"):
            return "text"
        return "attachment"

    def delete(self, *, db: Session, artifact: Artifact) -> None:
        if artifact.local_path:
            path = Path(artifact.local_path)
            if path.exists():
                path.unlink()
        db.delete(artifact)
        db.commit()
