from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.api import api_router
from app.core.config import get_settings
from app.core.constants import API_TAGS, APP_DESCRIPTION
from app.core.logging import configure_logging, get_logger
from app.core.middleware import GeminiGuardMiddleware, RequestContextMiddleware
from app.db.base import Base
from app.db.session import engine

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    description=APP_DESCRIPTION,
    version="0.1.0",
    openapi_tags=API_TAGS,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "testserver", "*.vercel.app", "*.run.app"],
)
app.add_middleware(
    GeminiGuardMiddleware,
    gemini_configured=bool(settings.google_genai_api_key),
    allow_demo_fallback=settings.allow_demo_fallback,
)
app.add_middleware(RequestContextMiddleware)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info("Aegis OS backend started in %s mode", settings.app_env)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled backend error: %s", exc.__class__.__name__)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred."},
    )


app.include_router(api_router, prefix=settings.api_v1_prefix)
