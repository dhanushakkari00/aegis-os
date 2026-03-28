from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.schemas.analysis import NormalizedAnalysisOutput


@dataclass
class GeminiResponse:
    text: str
    raw: dict


class GeminiClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.enabled = bool(settings.google_genai_api_key)

    def generate_json(self, *, prompt: str, system_instruction: str) -> GeminiResponse:
        if not self.enabled:
            raise RuntimeError("Gemini API key is not configured.")

        try:
            from google import genai
            from google.genai.types import GenerateContentConfig
        except ImportError as exc:
            raise RuntimeError("google-genai dependency is unavailable.") from exc

        client = genai.Client(api_key=self.settings.google_genai_api_key)
        response = client.models.generate_content(
            model=self.settings.google_genai_model,
            contents=prompt,
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
        text = getattr(response, "text", "") or ""
        raw = response.to_json_dict() if hasattr(response, "to_json_dict") else {"text": text}
        return GeminiResponse(text=text, raw=raw)
