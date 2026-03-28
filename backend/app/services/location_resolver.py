"""Helpers for resolving case locations and coordinates."""

from __future__ import annotations

import re

_COORDINATE_PATTERN = re.compile(
    r"latitude\s+(-?\d+(?:\.\d+)?)\s*,?\s+longitude\s+(-?\d+(?:\.\d+)?)",
    flags=re.IGNORECASE,
)


def resolve_case_location(case) -> str | None:
    """Return the best available human-readable location for a case."""
    structured = case.structured_result_json or {}
    structured_section = structured.get("structured") or {}
    disaster_section = structured_section.get("disaster") or {}
    return structured.get("extracted_location") or disaster_section.get("location")


def resolve_case_coords(case) -> tuple[float, float] | None:
    """Return explicit or browser-shared coordinates for a case."""
    structured = case.structured_result_json or {}
    lat = structured.get("location_lat")
    lng = structured.get("location_lng")
    if isinstance(lat, int | float) and isinstance(lng, int | float):
        return float(lat), float(lng)

    raw_input = case.raw_input or ""
    match = _COORDINATE_PATTERN.search(raw_input)
    if match:
        return float(match.group(1)), float(match.group(2))

    return None
