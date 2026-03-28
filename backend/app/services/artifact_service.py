"""Service for uploading, storing, and deleting case artifacts.

Artifacts are stored on Google Cloud Storage when ``GCS_BUCKET_NAME`` is
configured; otherwise files are persisted to a local ``storage/`` directory
as a development fallback.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.logging import get_logger
from app.core.security import sanitize_filename
from app.models.artifact import Artifact
from app.models.case import Case

logger = get_logger(__name__)


class ArtifactService:
    """Handles artifact lifecycle: upload, storage, signed-URL access, and deletion."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._gcs_bucket = self._init_gcs(settings)

    # ------------------------------------------------------------------
    # GCS helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _init_gcs(settings: Settings):
        """Return a GCS ``Bucket`` object or *None* when GCS is not configured."""
        if not settings.gcs_bucket_name:
            return None
        try:
            from google.cloud.storage import Client as GCSClient

            client = GCSClient(project=settings.google_cloud_project)
            bucket = client.bucket(settings.gcs_bucket_name)
            logger.info("GCS artifact storage enabled — bucket=%s", settings.gcs_bucket_name)
            return bucket
        except Exception as exc:
            logger.warning("GCS initialisation failed, falling back to local storage: %s", exc)
            return None

    def _upload_to_gcs(self, case_id: str, filename: str, contents: bytes, content_type: str) -> str:
        """Upload *contents* to GCS and return the ``gs://`` URI."""
        blob_path = f"cases/{case_id}/{filename}"
        blob = self._gcs_bucket.blob(blob_path)
        blob.upload_from_string(contents, content_type=content_type)
        logger.info("Uploaded artifact to GCS: gs://%s/%s", self._gcs_bucket.name, blob_path)
        return f"gs://{self._gcs_bucket.name}/{blob_path}"

    def _delete_from_gcs(self, storage_uri: str) -> None:
        """Delete an object from GCS given its ``gs://`` URI."""
        if not storage_uri.startswith("gs://"):
            return
        blob_path = storage_uri.split("/", 3)[-1]
        blob = self._gcs_bucket.blob(blob_path)
        blob.delete()
        logger.info("Deleted artifact from GCS: %s", storage_uri)

    def generate_signed_url(self, artifact: Artifact) -> str | None:
        """Return a time-limited signed URL for a GCS-backed artifact."""
        if not self._gcs_bucket or not artifact.storage_uri.startswith("gs://"):
            return None
        import datetime

        blob_path = artifact.storage_uri.split("/", 3)[-1]
        blob = self._gcs_bucket.blob(blob_path)
        return blob.generate_signed_url(
            expiration=datetime.timedelta(seconds=self.settings.gcs_signed_url_ttl_seconds),
            method="GET",
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def upload(
        self,
        *,
        db: Session,
        case: Case,
        file: UploadFile,
        artifact_type: str,
    ) -> Artifact:
        """Validate, store, and record an uploaded artifact."""
        content_type = self._normalize_mime_type(file.content_type)
        if content_type not in self.settings.allowed_upload_mime_types:
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

        # Determine storage backend.
        local_path: str | None = None
        if self._gcs_bucket:
            storage_provider = "gcs"
            storage_uri = self._upload_to_gcs(case.id, safe_name, contents, content_type)
        else:
            storage_provider = "local"
            local_path = self._store_locally(case.id, safe_name, contents)
            storage_uri = local_path

        excerpt = None
        if content_type == "text/plain":
            excerpt = contents.decode("utf-8", errors="ignore")[:1000]

        artifact = Artifact(
            case_id=case.id,
            filename=safe_name,
            mime_type=content_type,
            size_bytes=len(contents),
            artifact_type=artifact_type or self._infer_artifact_type(content_type),
            storage_provider=storage_provider,
            storage_uri=storage_uri,
            local_path=local_path,
            content_excerpt=excerpt,
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return artifact

    @staticmethod
    def _normalize_mime_type(content_type: str | None) -> str:
        """Collapse MIME values such as ``audio/webm;codecs=opus`` to ``audio/webm``."""
        if not content_type:
            return "application/octet-stream"
        return content_type.split(";", 1)[0].strip().lower()

    # ------------------------------------------------------------------
    # Local storage fallback
    # ------------------------------------------------------------------

    def _store_locally(self, case_id: str, filename: str, contents: bytes) -> str:
        """Persist *contents* to the local filesystem under ``storage/<case_id>/``."""
        storage_dir = Path(__file__).resolve().parents[2] / "storage" / case_id
        storage_dir.mkdir(parents=True, exist_ok=True)
        destination = storage_dir / filename
        destination.write_bytes(contents)
        return str(destination)

    @staticmethod
    def _infer_artifact_type(mime_type: str) -> str:
        """Map a MIME type to a human-friendly artifact category."""
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
        """Remove an artifact from both storage and the database."""
        if self._gcs_bucket and artifact.storage_uri.startswith("gs://"):
            try:
                self._delete_from_gcs(artifact.storage_uri)
            except Exception as exc:
                logger.warning("GCS delete failed for %s: %s", artifact.storage_uri, exc)

        if artifact.local_path:
            path = Path(artifact.local_path)
            if path.exists():
                path.unlink()

        db.delete(artifact)
        db.commit()
