from __future__ import annotations

import json

from pydantic import ValidationError

from app.schemas.analysis import NormalizedAnalysisOutput


class OutputParserError(ValueError):
    """Raised when AI output cannot be normalized into the expected schema."""


def extract_json_payload(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json\n", "", 1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise OutputParserError("No JSON object found in model response.")
    return text[start : end + 1]


def parse_analysis_output(raw_text: str) -> NormalizedAnalysisOutput:
    try:
        payload = extract_json_payload(raw_text)
        json.loads(payload)
        return NormalizedAnalysisOutput.model_validate_json(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise OutputParserError(str(exc)) from exc

