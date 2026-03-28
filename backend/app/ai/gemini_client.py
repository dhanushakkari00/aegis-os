from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.ai.types import ArtifactInput
from app.core.config import Settings
from app.core.logging import get_logger
from app.schemas.analysis import NormalizedAnalysisOutput

logger = get_logger(__name__)


@dataclass
class GeminiResponse:
    text: str
    raw: dict


class GeminiClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.enabled = bool(settings.google_genai_api_key)

    def generate_json(
        self,
        *,
        prompt: str,
        system_instruction: str,
        artifacts: list[ArtifactInput],
    ) -> GeminiResponse:
        if not self.enabled:
            raise RuntimeError("Gemini API key is not configured.")

        try:
            from google import genai
            from google.genai.types import GenerateContentConfig
        except ImportError as exc:
            raise RuntimeError("google-genai dependency is unavailable.") from exc

        client = genai.Client(api_key=self.settings.google_genai_api_key)
        uploaded_files = []
        contents: list[object] = [prompt]
        try:
            for artifact in artifacts:
                if not artifact.local_path:
                    continue
                artifact_path = Path(artifact.local_path)
                if not artifact_path.exists():
                    continue
                uploaded = client.files.upload(file=str(artifact_path))
                uploaded_files.append(uploaded)
                contents.append(uploaded)

            response = client.models.generate_content(
                model=self.settings.google_genai_model,
                contents=contents,
                config=GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_json_schema=NormalizedAnalysisOutput.model_json_schema(),
                    temperature=0,
                    top_p=0.05,
                    candidate_count=1,
                    max_output_tokens=4096,
                    seed=7,
                ),
            )
        finally:
            for uploaded in uploaded_files:
                try:
                    client.files.delete(name=uploaded.name)
                except Exception as exc:
                    logger.warning("Failed to delete uploaded Gemini file %s: %s", uploaded.name, exc)
        text = getattr(response, "text", "") or ""
        raw = response.to_json_dict() if hasattr(response, "to_json_dict") else {"text": text}
        return GeminiResponse(text=text, raw=raw)
