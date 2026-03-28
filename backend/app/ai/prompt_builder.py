"""Prompt building for Gemini analysis.

Constructs the system instruction and per-case analysis prompts with
strict output rules, multimodal file-handling guidance, and mandatory
location extraction for dispatch readiness.
"""

from __future__ import annotations

import json

from app.core.constants import DISASTER_DISCLAIMER, MEDICAL_DISCLAIMER
from app.schemas.analysis import NormalizedAnalysisOutput
from app.schemas.enums import CaseMode


def build_system_instruction() -> str:
    """Return the system-level instruction for every Gemini call.

    This prompt establishes Aegis OS as a rigid, fact-only extraction
    engine that never invents data or outputs prose outside JSON.
    """
    return (
        "You are Aegis OS, a clinical and disaster intelligence extraction engine. "
        "Your mission is to convert unstructured emergency intake — text, images, audio, "
        "and PDF documents — into validated, operational JSON structures. "
        "\n\nCORE PRINCIPLES:\n"
        "1. OUTPUT STRICT JSON ONLY. Never output markdown, prose, or explanations.\n"
        "2. NEVER invent facts. Use only information grounded in the input or attachments.\n"
        "3. ALWAYS extract a specific location or address for dispatch. If none is explicit, "
        "infer the most likely location and set confidence accordingly. Put the best location "
        "string into 'extracted_location'. If coordinates are available, populate location_lat/lng.\n"
        "4. Separate observed_facts from inferred_risks. Facts require evidence; risks are derived.\n"
        "5. Escalate urgency for explicit red flags or life-safety events aggressively.\n"
        "6. Be conservative with confidence scoring — never exceed evidence certainty.\n"
        "7. Keep handoff_summary concise, operational, and safe for human operators.\n"
        "8. Populate missing_information for every critical unknown.\n"
        "\nMULTIMODAL FILE HANDLING:\n"
        "- Images: describe scene, injuries, hazards, signs, labels. Extract GPS EXIF if visible.\n"
        "- Audio: transcribe content verbatim, then extract medical/disaster facts from the transcript.\n"
        "- PDFs/Documents: extract key findings, patient records, incident reports, triage data.\n"
        "- Combine multimodal evidence with text input for maximum situational awareness.\n"
    )


def build_analysis_prompt(
    *,
    mode: CaseMode,
    raw_input: str,
    artifact_context: str,
) -> tuple[str, str]:
    """Build a mode-specific analysis prompt with the JSON schema.

    Returns ``(prompt_name, prompt_text)`` ready for the Gemini API.
    """
    schema = json.dumps(NormalizedAnalysisOutput.model_json_schema(), indent=2)
    base_rules = """
STRICT OUTPUT RULES
1. Output strict JSON only. No markdown. No prose outside JSON.
2. The root object must validate against the schema exactly.
3. Do not omit required fields. Do not add extra keys.
4. Use arrays instead of prose lists.
5. Do not state certainty beyond the evidence.
6. Put explicit unknowns into missing_information, not fabricated values.
7. Make recommended_actions operational, safe, and prioritized.
8. Keep concise_summary under 240 characters.
9. Keep handoff_summary under 600 characters.
10. ALWAYS populate extracted_location with a geocodable address, landmark, or area.
    If the input mentions a location, address, sector, region, hospital, or any place name,
    extract it. If none found, set extracted_location to null and add to missing_information.
11. If coordinates (lat/lng) are available (e.g., from GPS or explicit mention), populate
    location_lat and location_lng.
""".strip()

    if mode == CaseMode.MEDICAL_TRIAGE:
        prompt_name = "medical-triage"
        mode_specific = (
            "MEDICAL TRIAGE MODE — Extract and structure:\n"
            "• Symptoms with onset/duration\n"
            "• Medical history, current medications, known allergies\n"
            "• Vital signs if available\n"
            "• RED FLAGS: chest pain, severe SOB, stroke symptoms, heavy bleeding, "
            "unresponsiveness, severe allergic reactions, altered consciousness → ESCALATE urgency\n"
            "• Safe immediate next steps for the operator\n"
            "• Location of the patient/incident for ambulance dispatch\n"
            f"\nInclude this disclaimer: {MEDICAL_DISCLAIMER}"
        )
    elif mode == CaseMode.DISASTER_RESPONSE:
        prompt_name = "disaster-response"
        mode_specific = (
            "DISASTER RESPONSE MODE — Extract and structure:\n"
            "• Incident type, exact location/sector, affected area size\n"
            "• Number of affected/trapped people, injuries, fatalities\n"
            "• Infrastructure damage, hazards (fire, flood, hazmat, structural collapse)\n"
            "• Supply needs, access route status\n"
            "• RED FLAGS: people trapped, access blocked, active fire, rising water, "
            "hazmat exposure, critical infrastructure failure → ESCALATE severity\n"
            "• Structured field report for incident command\n"
            f"\nInclude this disclaimer: {DISASTER_DISCLAIMER}"
        )
    else:
        prompt_name = "auto-detect"
        mode_specific = (
            "AUTO-DETECT MODE — First classify input as medical, disaster, mixed, or unclear.\n"
            "Then populate the appropriate structured sections.\n"
            "When mixed, include both medical and disaster structured sections.\n"
            "If classification is uncertain, use 'unclear' and explain via missing_information."
        )

    prompt = f"""
{base_rules}

MODE
{mode.value}

MODE INSTRUCTIONS
{mode_specific}

MULTIMODAL EVIDENCE
If images, audio, or documents are attached, use them as primary evidence sources.
For images: describe visible injuries, scene conditions, signage, and hazards.
For audio: transcribe and extract critical facts.
For documents/PDFs: parse incident reports, medical records, and official communications.
Cross-reference all evidence sources against the text input.

EXPECTED JSON SCHEMA
{schema}

RAW INPUT
{raw_input}

ARTIFACT CONTEXT
{artifact_context}
""".strip()

    return prompt_name, prompt


def build_correction_prompt(*, prior_response: str, validation_error: str) -> str:
    """Build a correction prompt when a previous response fails validation."""
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
