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
      "decision_state": "final",
      "urgency_level": "high",
      "confidence": 0.82,
      "concise_summary": "Summary",
      "handoff_summary": "Handoff",
      "assistant_response": "Call emergency services now and share the exact location.",
      "final_verdict": "Probable acute medical emergency.",
      "observed_facts": [],
      "inferred_risks": [],
      "missing_information": [],
      "follow_up_questions": [],
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


def test_parse_analysis_output_normalizes_sparse_case_density() -> None:
    payload = """
    {
      "schema_version": "1.0",
      "mode_used": "auto_detect",
      "case_type": "medical",
      "decision_state": "needs_clarification",
      "urgency_level": "moderate",
      "confidence": 0.55,
      "concise_summary": "Summary",
      "handoff_summary": "Handoff",
      "assistant_response": "Tell me what symptoms are happening now and where the patient is located.",
      "final_verdict": null,
      "observed_facts": [],
      "inferred_risks": ["risk 1", "risk 2", "risk 3", "risk 4"],
      "missing_information": [
        {"item": "A", "reason": "1", "criticality": "high"},
        {"item": "B", "reason": "2", "criticality": "high"},
        {"item": "C", "reason": "3", "criticality": "medium"},
        {"item": "D", "reason": "4", "criticality": "low"}
      ],
      "follow_up_questions": ["Q1", "Q2", "Q3", "Q4"],
      "recommended_actions": [
        {"priority": 4, "title": "D", "description": "D", "category": "info", "rationale": "D", "is_immediate": false},
        {"priority": 2, "title": "B", "description": "B", "category": "info", "rationale": "B", "is_immediate": true},
        {"priority": 1, "title": "A", "description": "A", "category": "info", "rationale": "A", "is_immediate": true},
        {"priority": 3, "title": "C", "description": "C", "category": "info", "rationale": "C", "is_immediate": true},
        {"priority": 5, "title": "E", "description": "E", "category": "info", "rationale": "E", "is_immediate": false}
      ],
      "disclaimers": ["note", "note"],
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
    """
    parsed = parse_analysis_output(payload)
    assert len(parsed.missing_information) == 3
    assert len(parsed.follow_up_questions) == 3
    assert len(parsed.inferred_risks) == 3
    assert len(parsed.recommended_actions) == 4
    assert parsed.recommended_actions[0].priority == 1
    assert parsed.decision_state == "needs_clarification"


def test_parse_analysis_output_rejects_invalid_payload() -> None:
    with pytest.raises(OutputParserError):
        parse_analysis_output('{"mode_used":"medical_triage"}')
