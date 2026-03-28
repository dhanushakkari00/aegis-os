from __future__ import annotations

import re
from pathlib import Path


FILENAME_SAFE_CHARS = re.compile(r"[^a-zA-Z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    cleaned = FILENAME_SAFE_CHARS.sub("-", Path(filename).name).strip(".-")
    return cleaned or "artifact"

