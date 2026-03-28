from __future__ import annotations

import json
from time import perf_counter

from app.ai.gemini_client import GeminiClient
from app.ai.output_parser import OutputParserError, parse_analysis_output
from app.ai.prompt_builder import (
    build_analysis_prompt,
    build_correction_prompt,
    build_system_instruction,
)
from app.ai.types import ArtifactInput
from app.core.constants import DISASTER_DISCLAIMER, MEDICAL_DISCLAIMER
from app.core.config import Settings
from app.schemas.analysis import (
    DisasterStructuredData,
    MedicalStructuredData,
    MissingInformationItem,
    NormalizedAnalysisOutput,
    ObservedFact,
    RecommendedActionItem,
    StructuredAnalysis,
)
from app.schemas.enums import CaseMode, DetectedCaseType, UrgencyLevel


class AIOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = GeminiClient(settings)

    def analyze(
        self,
        *,
        mode: CaseMode,
        raw_input: str,
        artifact_context: str,
        artifacts: list[ArtifactInput],
    ) -> tuple[str, int, dict, NormalizedAnalysisOutput]:
        prompt_name, prompt = build_analysis_prompt(
            mode=mode,
            raw_input=raw_input,
            artifact_context=artifact_context,
        )
        system_instruction = build_system_instruction()

        started = perf_counter()
        if not self.client.enabled:
            if not self.settings.allow_demo_fallback:
                raise RuntimeError("Gemini API key is required for analysis in this environment.")
            output = self._demo_fallback(mode=mode, raw_input=raw_input)
            latency_ms = int((perf_counter() - started) * 1000)
            return prompt_name, latency_ms, {"demo_fallback": True}, output

        response = self.client.generate_json(
            prompt=prompt,
            system_instruction=system_instruction,
            artifacts=artifacts,
        )
        try:
            output = parse_analysis_output(response.text)
            latency_ms = int((perf_counter() - started) * 1000)
            return prompt_name, latency_ms, response.raw, output
        except OutputParserError as exc:
            correction_prompt = build_correction_prompt(
                prior_response=response.text,
                validation_error=str(exc),
            )
            correction_response = self.client.generate_json(
                prompt=correction_prompt,
                system_instruction=system_instruction,
                artifacts=artifacts,
            )
            output = parse_analysis_output(correction_response.text)
            latency_ms = int((perf_counter() - started) * 1000)
            combined_raw = {
                "initial": response.raw,
                "correction": correction_response.raw,
            }
            return prompt_name, latency_ms, combined_raw, output

    def _demo_fallback(self, *, mode: CaseMode, raw_input: str) -> NormalizedAnalysisOutput:
        lowered = raw_input.lower()
        looks_medical = any(keyword in lowered for keyword in ["pain", "breath", "diabetic", "symptom", "fever"])
        looks_disaster = any(keyword in lowered for keyword in ["flood", "trapped", "roads", "fire", "hazard"])

        if mode == CaseMode.MEDICAL_TRIAGE or (mode == CaseMode.AUTO_DETECT and looks_medical and not looks_disaster):
            return self._medical_demo(mode, raw_input)
        if mode == CaseMode.DISASTER_RESPONSE or (mode == CaseMode.AUTO_DETECT and looks_disaster and not looks_medical):
            return self._disaster_demo(mode, raw_input)
        if looks_medical and looks_disaster:
            return self._mixed_demo(mode, raw_input)

        return NormalizedAnalysisOutput(
            mode_used=mode,
            case_type=DetectedCaseType.UNCLEAR,
            urgency_level=UrgencyLevel.MODERATE,
            confidence=0.44,
            concise_summary="Input is incomplete and cannot be confidently classified.",
            handoff_summary="Unclear incident. Need caller location, immediate hazards, number of affected people, and major symptoms.",
            observed_facts=[ObservedFact(label="Reported input", value=raw_input, source="user_text", confidence=0.5)],
            inferred_risks=["Insufficient information may hide urgent medical or safety concerns."],
            missing_information=[
                MissingInformationItem(
                    item="Primary complaint or incident type",
                    reason="Needed to determine the correct response pathway.",
                    criticality="high",
                ),
                MissingInformationItem(
                    item="Location or callback context",
                    reason="Required for dispatch or follow-up.",
                    criticality="high",
                ),
            ],
            recommended_actions=[
                RecommendedActionItem(
                    priority=1,
                    title="Clarify the situation",
                    description="Obtain the caller's exact issue, location, and any immediate danger or red-flag symptoms.",
                    category="information",
                    rationale="Analysis confidence is too low for a more specific recommendation.",
                    is_immediate=True,
                )
            ],
            disclaimers=[MEDICAL_DISCLAIMER, DISASTER_DISCLAIMER],
            structured=StructuredAnalysis(),
        )

    def _medical_demo(self, mode: CaseMode, raw_input: str) -> NormalizedAnalysisOutput:
        chest_pain = "chest pain" in raw_input.lower()
        critical = chest_pain and "shortness of breath" in raw_input.lower()
        return NormalizedAnalysisOutput(
            mode_used=mode,
            case_type=DetectedCaseType.MEDICAL,
            urgency_level=UrgencyLevel.CRITICAL if critical else UrgencyLevel.HIGH,
            confidence=0.89,
            concise_summary="Medical triage indicates a potentially time-sensitive cardiac emergency.",
            handoff_summary=(
                "58-year-old diabetic male with chest pain, sweating, and shortness of breath for 20 minutes. "
                "Treat as high-acuity chest pain with red-flag features pending immediate clinician/EMS escalation."
            ),
            observed_facts=[
                ObservedFact(label="Age/sex", value="58-year-old male", source="user_text", confidence=0.88),
                ObservedFact(label="Medical history", value="Diabetes", source="user_text", confidence=0.87),
                ObservedFact(label="Symptoms", value="Chest pain, sweating, shortness of breath", source="user_text", confidence=0.92),
                ObservedFact(label="Duration", value="20 minutes", source="user_text", confidence=0.9),
            ],
            inferred_risks=["Possible acute coronary syndrome or other cardiopulmonary emergency."],
            missing_information=[
                MissingInformationItem(item="Current vitals", reason="Needed to assess immediate instability.", criticality="high"),
                MissingInformationItem(item="Medication list and allergies", reason="Useful for safe handoff and treatment planning.", criticality="medium"),
            ],
            recommended_actions=[
                RecommendedActionItem(priority=1, title="Escalate to emergency care", description="Advise immediate EMS or emergency department evaluation for red-flag chest pain symptoms.", category="medical", rationale="Chest pain with dyspnea and diaphoresis is a high-risk pattern.", is_immediate=True),
                RecommendedActionItem(priority=2, title="Limit exertion", description="Keep the patient seated or resting while waiting for professional care, unless this conflicts with clinician advice.", category="safety", rationale="Reducing exertion may help limit worsening symptoms.", is_immediate=True),
                RecommendedActionItem(priority=3, title="Collect critical handoff details", description="Confirm onset time, medical history, medications, allergies, and any worsening symptoms.", category="information", rationale="Improves ED or EMS handoff quality.", is_immediate=True),
            ],
            disclaimers=[MEDICAL_DISCLAIMER],
            structured=StructuredAnalysis(
                medical=MedicalStructuredData(
                    symptoms=["Chest pain", "Sweating", "Shortness of breath"],
                    onset_or_duration="20 minutes",
                    medical_history=["Diabetes"],
                    red_flags=["Chest pain", "Shortness of breath", "Diaphoresis"],
                )
            ),
        )

    def _disaster_demo(self, mode: CaseMode, raw_input: str) -> NormalizedAnalysisOutput:
        return NormalizedAnalysisOutput(
            mode_used=mode,
            case_type=DetectedCaseType.DISASTER,
            urgency_level=UrgencyLevel.CRITICAL,
            confidence=0.91,
            concise_summary="Flooding incident with trapped civilians, access blockage, and likely ongoing risk escalation.",
            handoff_summary=(
                "Flooding reported in Sector 9. Twelve people trapped, one elderly person injured, roads blocked, "
                "water above knee height. Treat as active life-safety event requiring coordinated rescue and route assessment."
            ),
            observed_facts=[
                ObservedFact(label="Incident type", value="Flooding", source="user_text", confidence=0.96),
                ObservedFact(label="Location", value="Sector 9", source="user_text", confidence=0.88),
                ObservedFact(label="Affected people", value="12 people trapped", source="user_text", confidence=0.94),
                ObservedFact(label="Injury", value="One elderly person injured", source="user_text", confidence=0.9),
                ObservedFact(label="Access", value="Roads blocked", source="user_text", confidence=0.91),
            ],
            inferred_risks=["Rising water may worsen entrapment and delay medical access.", "Road blockage may require alternate rescue routing."],
            missing_information=[
                MissingInformationItem(item="Exact coordinates or landmark", reason="Needed for dispatch precision.", criticality="high"),
                MissingInformationItem(item="Water rise trend", reason="Impacts urgency of rescue method.", criticality="high"),
                MissingInformationItem(item="Available shelter or high ground", reason="Useful for immediate public safety guidance.", criticality="medium"),
            ],
            recommended_actions=[
                RecommendedActionItem(priority=1, title="Escalate rescue response", description="Notify flood rescue or local emergency services with trapped-person count, injury, and blocked-road status.", category="dispatch", rationale="Active entrapment and injury create immediate life-safety risk.", is_immediate=True),
                RecommendedActionItem(priority=2, title="Identify safe access route", description="Confirm alternate road, boat, or high-clearance vehicle access before dispatching teams into moving water.", category="safety", rationale="Reduces responder exposure to flood hazards.", is_immediate=True),
                RecommendedActionItem(priority=3, title="Prepare medical support", description="Stage medical support for the injured elderly person and potential hypothermia or fall-related complications.", category="medical", rationale="Improves rescue-to-care handoff.", is_immediate=True),
            ],
            disclaimers=[DISASTER_DISCLAIMER],
            structured=StructuredAnalysis(
                disaster=DisasterStructuredData(
                    incident_type="Flooding",
                    location="Sector 9",
                    affected_people="12 trapped people",
                    injuries=["One elderly injured person"],
                    infrastructure_damage=["Roads blocked"],
                    hazards=["Water above knee height", "Potential rising floodwater"],
                    structured_field_report=[
                        "Incident: Flooding",
                        "Location: Sector 9",
                        "Affected: 12 trapped, one elderly injured",
                        "Access: roads blocked",
                    ],
                )
            ),
        )

    def _mixed_demo(self, mode: CaseMode, raw_input: str) -> NormalizedAnalysisOutput:
        payload = self._disaster_demo(mode, raw_input).model_copy(deep=True)
        payload.case_type = DetectedCaseType.MIXED
        payload.structured.medical = MedicalStructuredData(red_flags=["Possible injury among affected civilians"])
        payload.disclaimers = [MEDICAL_DISCLAIMER, DISASTER_DISCLAIMER]
        payload.inferred_risks.append("Mixed medical and incident-management needs require unified command handoff.")
        return payload


def serialize_analysis_output(output: NormalizedAnalysisOutput) -> dict:
    return json.loads(output.model_dump_json())
