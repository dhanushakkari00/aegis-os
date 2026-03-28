"""Logging configuration with optional Google Cloud Logging integration.

When ``GOOGLE_CLOUD_PROJECT`` is set, logs are emitted as structured JSON to
Cloud Logging so they appear in the Cloud Run **Logs** tab with severity
labels.  Otherwise, standard Python ``logging`` is used.
"""

from __future__ import annotations

import logging
import os
import sys


def configure_logging(level: str = "INFO") -> None:
    """Set up the root logger.

    Uses Google Cloud Logging when deployed on GCP (detected via the
    ``GOOGLE_CLOUD_PROJECT`` environment variable), otherwise falls back to
    the standard library ``logging`` with a structured format.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    if os.getenv("GOOGLE_CLOUD_PROJECT"):
        try:
            import google.cloud.logging as cloud_logging

            client = cloud_logging.Client()
            client.setup_logging(log_level=log_level)
            logging.getLogger().info("Cloud Logging integration active.")
            return
        except Exception:
            # Fall through to standard logging on any import / auth error.
            pass

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stderr,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger instance."""
    return logging.getLogger(name)
