"""HTTP middleware stack for Aegis OS.

Provides:
* **RequestContextMiddleware** — attaches a request ID, measures latency,
  and emits structured request-complete logs.  Also sets hardened security
  headers (CSP, HSTS, X-Frame-Options, etc.).
* **GeminiGuardMiddleware** — blocks ``/analyze`` routes when Gemini is
  unavailable and demo-fallback is disabled.
* **RateLimitMiddleware** — protects expensive AI endpoints with a simple
  in-memory token-bucket rate limiter.
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------
_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cache-Control": "no-store",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    ),
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach request IDs, measure latency, and emit structured logs."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process every inbound request."""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        started_at = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - started_at) * 1000)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        for header, value in _SECURITY_HEADERS.items():
            response.headers[header] = value

        logger.info(
            "request_complete method=%s path=%s status=%s request_id=%s duration_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            request_id,
            duration_ms,
        )
        return response


class GeminiGuardMiddleware(BaseHTTPMiddleware):
    """Block ``/analyze`` routes when Gemini is unavailable and demo mode is off."""

    def __init__(self, app, *, gemini_configured: bool, allow_demo_fallback: bool) -> None:
        super().__init__(app)
        self.gemini_configured = gemini_configured
        self.allow_demo_fallback = allow_demo_fallback

    async def dispatch(self, request: Request, call_next) -> Response:
        """Guard AI-dependent endpoints."""
        is_analysis_route = (
            request.method.upper() == "POST"
            and request.url.path.endswith("/analyze")
        )
        if is_analysis_route and not self.gemini_configured and not self.allow_demo_fallback:
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Gemini is required for analysis and is not configured on the backend."
                },
            )
        response = await call_next(request)
        response.headers["X-AI-Provider"] = "gemini" if self.gemini_configured else "demo-fallback"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory token-bucket rate limiter for ``/analyze`` routes.

    Limits each client IP to ``max_requests`` within ``window_seconds``.
    """

    def __init__(self, app, *, max_requests: int = 15, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Enforce rate limits on analysis endpoints."""
        is_analysis_route = (
            request.method.upper() == "POST"
            and request.url.path.endswith("/analyze")
        )
        if not is_analysis_route:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window_start = now - self.window_seconds

        # Clean old entries and check limit.
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > window_start
        ]

        if len(self._requests[client_ip]) >= self.max_requests:
            logger.warning("Rate limit exceeded for %s on %s", client_ip, request.url.path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)
