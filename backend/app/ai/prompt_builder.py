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
        "3. Extract location only when it is explicit in text, transcript, document content, or "
        "reliable artifact metadata. NEVER invent or guess an address. If missing, set "
        "'extracted_location' to null and add a targeted follow-up question.\n"
        "4. Separate observed_facts from inferred_risks. Facts require evidence; risks are derived.\n"
        "5. Escalate urgency for explicit red flags or life-safety events aggressively.\n"
        "6. Be conservative with confidence scoring — never exceed evidence certainty.\n"
        "7. Keep handoff_summary concise, operational, and safe for human operators.\n"
        "8. Populate missing_information only for the highest-yield unknowns.\n"
        "9. follow_up_questions must be short, operator-ready, and phrased as direct questions.\n"
        "10. Keep recommended action rationales concrete and non-empty when possible.\n"
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
    previous_analysis_context: str,
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
10. assistant_response must sound like a calm, concise operator-facing chatbot reply.
    If the case is unclear or incomplete, assistant_response should ask for the next best details.
    If the case is urgent, assistant_response should clearly tell the user what to do now.
11. final_verdict should be null until enough evidence exists for a useful operational decision.
12. decision_state must be one of: needs_clarification, provisional, final.
13. follow_up_questions must contain at most 3 concise questions. Only include questions that
    materially change dispatch, triage, or safety decisions.
14. For low/moderate sparse intakes, keep missing_information to the top 3 highest-yield gaps.
    Do not ask for generic demographics or exhaustive medical history unless clearly relevant.
15. For high/critical events, missing_information may include up to 5 items.
16. Only populate extracted_location when the source explicitly provides a location or trustworthy
    artifact metadata. Never guess a location from context alone.
17. If coordinates (lat/lng) are available (e.g., from GPS or explicit mention), populate
    location_lat and location_lng. Browser-shared device coordinates in the raw input count as
    explicit GPS evidence and should be copied exactly.
18. If the user's latest message is only a greeting or generic chat, set case_type to unclear,
    decision_state to needs_clarification, and assistant_response should politely ask whether this
    is a medical or disaster emergency and request the location.
19. Every recommended action should have a short, concrete rationale when supported by evidence.
20. When decision_state is final, final_verdict must be a crisp operational conclusion plus the
    immediate next responder action.
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
            "• If the intake is sparse and non-red-flag, ask only the 2-3 most decision-relevant "
            "follow-up questions rather than producing a broad checklist\n"
            "• If enough red-flag evidence exists, set decision_state to final and provide a "
            "clear final_verdict\n"
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
            "• Ask only the most important follow-up questions needed for rescue routing, "
            "dispatch, or public safety messaging\n"
            "• If enough incident data exists for an operational conclusion, set decision_state "
            "to final and provide a clear final_verdict\n"
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
If the intake is sparse, use follow_up_questions to ask for the next best operator prompts.
If previous_analysis_context is present, use it to continue the same case rather than restarting.

EXPECTED JSON SCHEMA
{schema}

RAW INPUT
{raw_input}

ARTIFACT CONTEXT
{artifact_context}

PREVIOUS ANALYSIS CONTEXT
{previous_analysis_context}
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
