from __future__ import annotations

APP_DESCRIPTION = (
    "Emergency intelligence platform for medical triage and disaster response."
)
API_TAGS = [
    {"name": "health", "description": "Service health and readiness checks."},
    {"name": "cases", "description": "Case intake, artifacts, analysis, and exports."},
    {"name": "dashboard", "description": "Command-center summary metrics."},
    {"name": "nearby", "description": "Nearby hospitals, clinics, and shelter routing resources."},
    {"name": "auth", "description": "Operator authentication endpoints."},
]

MEDICAL_DISCLAIMER = (
    "Aegis OS assists with triage support only and does not replace licensed medical care."
)
DISASTER_DISCLAIMER = (
    "Aegis OS provides decision support and does not replace local emergency command authority."
)
