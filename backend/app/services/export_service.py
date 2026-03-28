from __future__ import annotations

import json

from app.models.case import Case


class ExportService:
    def export_json(self, case: Case) -> dict:
        return {
            "case_id": case.id,
            "payload": case.structured_result_json,
        }

    def export_handoff(self, case: Case) -> str:
        structured = case.structured_result_json or {}
        lines = [
            f"Aegis OS Handoff | Case {case.id}",
            f"Mode: {case.mode}",
            f"Detected Type: {case.detected_case_type}",
            f"Urgency: {case.urgency_level}",
            f"Confidence: {case.confidence:.2f}",
            "",
            "Summary:",
            case.handoff_summary or "No handoff summary available.",
        ]

        observed = structured.get("observed_facts", [])
        if observed:
            lines.extend(["", "Observed Facts:"])
            lines.extend([f"- {fact['label']}: {fact['value']}" for fact in observed])

        missing = structured.get("missing_information", [])
        if missing:
            lines.extend(["", "Missing Critical Information:"])
            lines.extend([f"- {item['item']}: {item['reason']}" for item in missing])

        actions = structured.get("recommended_actions", [])
        if actions:
            lines.extend(["", "Recommended Actions:"])
            lines.extend([f"- P{action['priority']} {action['title']}: {action['description']}" for action in actions])

        lines.extend(["", "Machine JSON:", json.dumps(structured, indent=2)])
        return "\n".join(lines)

