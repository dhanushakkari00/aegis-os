from __future__ import annotations

import base64
from dataclasses import dataclass
from email.message import EmailMessage

import httpx

from app.core.config import Settings
from app.core.logging import get_logger
from app.models.case import Case

logger = get_logger(__name__)

_GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105
_GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


@dataclass
class EmailDeliveryResult:
    delivered: bool
    provider_message_id: str | None = None
    error: str | None = None


def _mask_email(email: str) -> str:
    local_part, _, domain = email.partition("@")
    if not domain:
        return "***"
    prefix = local_part[:2] if local_part else "*"
    return f"{prefix}***@{domain}"


class GmailService:
    def __init__(self, settings: Settings) -> None:
        self.client_id = settings.gmail_client_id
        self.client_secret = settings.gmail_client_secret
        self.refresh_token = settings.gmail_refresh_token
        self.from_email = settings.gmail_from_email
        self.from_name = settings.gmail_from_name
        self.notifications_enabled = settings.gmail_send_case_notifications

    def is_configured(self) -> bool:
        return self.notifications_enabled and all(
            [
                self.client_id,
                self.client_secret,
                self.refresh_token,
                self.from_email,
            ]
        )

    def send_case_summary(self, *, case: Case, recipient_email: str) -> EmailDeliveryResult:
        if not self.is_configured():
            return EmailDeliveryResult(delivered=False, error="Gmail notifications are not configured.")

        if not case.structured_result_json:
            return EmailDeliveryResult(
                delivered=False,
                error="Case analysis is not available yet. Run analysis before sending email.",
            )

        try:
            access_token = self._fetch_access_token()
            message = self._build_case_message(case=case, recipient_email=recipient_email)
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode().rstrip("=")

            response = httpx.post(
                _GMAIL_SEND_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={"raw": raw_message},
                timeout=15,
            )
            response.raise_for_status()
            payload = response.json()
            logger.info(
                "Sent case handoff email for case=%s to=%s",
                case.id,
                _mask_email(recipient_email),
            )
            return EmailDeliveryResult(delivered=True, provider_message_id=payload.get("id"))
        except Exception as exc:
            logger.warning(
                "Failed to send Gmail handoff for case=%s to=%s: %s",
                case.id,
                _mask_email(recipient_email),
                exc.__class__.__name__,
            )
            return EmailDeliveryResult(delivered=False, error=str(exc))

    def _fetch_access_token(self) -> str:
        response = httpx.post(
            _GOOGLE_OAUTH_TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        access_token = payload.get("access_token")
        if not access_token:
            raise RuntimeError("Gmail OAuth token response did not include an access token.")
        return access_token

    def _build_case_message(self, *, case: Case, recipient_email: str) -> EmailMessage:
        structured = case.structured_result_json or {}
        subject = (
            f"Aegis OS Update | {case.urgency_level.title()} "
            f"{case.detected_case_type.replace('_', ' ').title()} | {case.id[:8]}"
        )
        assistant_response = structured.get("assistant_response") or case.handoff_summary or "No summary available."
        final_verdict = structured.get("final_verdict") or "No final verdict yet."
        concise_summary = structured.get("concise_summary") or case.handoff_summary or case.raw_input[:240]
        recommendations = structured.get("recommended_actions") or []
        follow_ups = structured.get("follow_up_questions") or []
        disclaimers = structured.get("disclaimers") or []

        text_lines = [
            f"Aegis OS case update for case {case.id}",
            "",
            f"Urgency: {case.urgency_level}",
            f"Detected case type: {case.detected_case_type}",
            f"Confidence: {round(case.confidence * 100)}%",
            "",
            "Concise summary:",
            concise_summary,
            "",
            "Assistant response:",
            assistant_response,
            "",
            "Final verdict:",
            final_verdict,
            "",
            "Handoff summary:",
            case.handoff_summary or "No handoff summary available.",
        ]

        if recommendations:
            text_lines.extend(["", "Recommended next actions:"])
            for action in recommendations[:5]:
                immediate = "Immediate" if action.get("is_immediate") else "Planned"
                text_lines.append(
                    f"- P{action.get('priority', '?')} {action.get('title', 'Action')}: "
                    f"{action.get('description', '')} [{immediate}]"
                )

        if follow_ups:
            text_lines.extend(["", "Clarifications still needed:"])
            for question in follow_ups[:5]:
                text_lines.append(f"- {question}")

        if disclaimers:
            text_lines.extend(["", "Disclaimers:"])
            for disclaimer in disclaimers:
                text_lines.append(f"- {disclaimer}")

        message = EmailMessage()
        message["To"] = recipient_email
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["Subject"] = subject
        message.set_content("\n".join(text_lines))
        return message
