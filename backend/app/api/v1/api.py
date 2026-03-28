from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import auth, cases, dashboard, health, nearby

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(nearby.router, tags=["nearby"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

