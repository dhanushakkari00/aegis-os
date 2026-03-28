from __future__ import annotations

import time
import uuid

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        started_at = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - started_at) * 1000)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Response-Time-Ms"] = str(duration_ms)

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
    def __init__(self, app, *, gemini_configured: bool, allow_demo_fallback: bool) -> None:
        super().__init__(app)
        self.gemini_configured = gemini_configured
        self.allow_demo_fallback = allow_demo_fallback

    async def dispatch(self, request: Request, call_next) -> Response:
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
