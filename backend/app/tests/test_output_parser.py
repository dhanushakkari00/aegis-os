from __future__ import annotations

import pytest

from app.ai.output_parser import OutputParserError, parse_analysis_output


def test_parse_analysis_output_handles_markdown_wrapped_json() -> None:
    payload = """
    ```json
    {
      "schema_version": "1.0",
      "mode_used": "medical_triage",
      "case_type": "medical",
      "urgency_level": "high",
      "confidence": 0.82,
      "concise_summary": "Summary",
      "handoff_summary": "Handoff",
      "observed_facts": [],
      "inferred_risks": [],
      "missing_information": [],
      "recommended_actions": [],
      "disclaimers": [],
      "structured": {
        "medical": {
          "symptoms": [],
          "onset_or_duration": null,
          "medical_history": [],
          "medications": [],
          "allergies": [],
          "vitals": {},
          "red_flags": []
        },
        "disaster": null
      }
    }
    ```
    """
    parsed = parse_analysis_output(payload)
    assert parsed.mode_used == "medical_triage"
    assert parsed.case_type == "medical"


def test_parse_analysis_output_rejects_invalid_payload() -> None:
    with pytest.raises(OutputParserError):
        parse_analysis_output('{"mode_used":"medical_triage"}')

