from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ArtifactInput:
    filename: str
    mime_type: str
    local_path: str | None
    content_excerpt: str | None
