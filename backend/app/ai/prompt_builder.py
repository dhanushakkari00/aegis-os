from __future__ import annotations

import json

from app.core.constants import DISASTER_DISCLAIMER, MEDICAL_DISCLAIMER
from app.schemas.analysis import NormalizedAnalysisOutput
from app.schemas.enums import CaseMode


def build_system_instruction() -> str:
    return (
        "You are Aegis OS, a clinical and disaster intelligence extraction engine. "
        "Your job is to convert unstructured emergency intake into validated operational JSON. "
        "Return a single JSON object that matches the provided schema exactly. "
        "Never output markdown. Never output prose outside the JSON object. "
        "Never invent facts. Use only information grounded in the input or artifact context. "
        "If a detail is missing, leave nullable fields null, use empty arrays where appropriate, "
        "and place the gap in missing_information. "
        "Separate observed_facts from inferred_risks. "
        "Escalate urgency for explicit red flags or life-safety events. "
        "Be conservative with confidence scoring. "
        "Keep handoff_summary concise, operational, and safe."
    )


def build_analysis_prompt(
    *,
    mode: CaseMode,
    raw_input: str,
    artifact_context: str,
) -> tuple[str, str]:
    schema = json.dumps(NormalizedAnalysisOutput.model_json_schema(), indent=2)
    base_rules = """
STRICT OUTPUT RULES
1. Output strict JSON only.
2. The root object must validate against the schema exactly.
3. Do not omit required fields.
4. Do not add extra keys.
5. Use arrays instead of prose lists.
6. Do not state certainty beyond the evidence.
7. Put explicit unknowns into missing_information, not fabricated values.
8. Make recommended_actions operational, safe, and prioritized.
9. Keep concise_summary under 240 characters.
10. Keep handoff_summary under 600 characters.
""".strip()

    if mode == CaseMode.MEDICAL_TRIAGE:
        prompt_name = "medical-triage"
        mode_specific = (
            "Focus on symptoms, onset or duration, medical history, medications, allergies, "
            "vitals, red flags, urgency level, missing critical information, and safe immediate next steps. "
            "If chest pain, severe shortness of breath, stroke-like symptoms, heavy bleeding, unresponsiveness, "
            "or severe allergic reactions are present, escalate urgency strongly. "
            f"Include this disclaimer in disclaimers when relevant: {MEDICAL_DISCLAIMER}"
        )
    elif mode == CaseMode.DISASTER_RESPONSE:
        prompt_name = "disaster-response"
        mode_specific = (
            "Focus on incident type, location, affected people, injuries, damage, hazards, supply needs, "
            "severity, escalation suggestions, and a structured field report. "
            "If people are trapped, access routes are blocked, fire is active, water is rising, hazardous materials are present, "
            "or critical infrastructure is failing, escalate severity strongly. "
            f"Include this disclaimer in disclaimers when relevant: {DISASTER_DISCLAIMER}"
        )
    else:
        prompt_name = "auto-detect"
        mode_specific = (
            "First classify the input as medical, disaster, mixed, or unclear. Then populate the appropriate "
            "structured sections. When mixed, include both medical and disaster structured sections if possible. "
            "If classification is uncertain, use unclear and explain the ambiguity through missing_information."
        )

    prompt = f"""
{base_rules}

MODE
{mode.value}

MODE INSTRUCTIONS
{mode_specific}

EXPECTED JSON SCHEMA
{schema}

RAW INPUT
{raw_input}

ARTIFACT CONTEXT
{artifact_context}
""".strip()

    return prompt_name, prompt


def build_correction_prompt(*, prior_response: str, validation_error: str) -> str:
    schema = json.dumps(NormalizedAnalysisOutput.model_json_schema(), indent=2)
    return f"""
Your previous response failed strict validation.
Return one corrected JSON object only.
Do not explain the correction.
Do not include markdown.

VALIDATION ERROR
{validation_error}

REQUIRED SCHEMA
{schema}

PREVIOUS RESPONSE
{prior_response}

Return corrected JSON only with no markdown.
""".strip()
