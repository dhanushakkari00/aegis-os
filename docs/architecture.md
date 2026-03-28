# Aegis OS Architecture

## Overview

Aegis OS is split into two deployable services:

1. `frontend/` is a Next.js App Router application focused on emergency intake, case review, and operations dashboards.
2. `backend/` is a FastAPI API that handles validation, persistence, AI orchestration, exports, and artifact storage.

## Request Flow

1. The user submits intake text and selects a mode or Auto Detect.
2. Optional artifacts are uploaded to the backend, which validates MIME, size, and filename before storing metadata and uploading to Google Cloud Storage.
3. The analysis endpoint invokes the AI orchestration layer.
4. Prompt builders generate a strict JSON schema-oriented prompt for Gemini.
5. The response is parsed, validated with Pydantic, normalized, and retried once if malformed.
6. The backend persists the structured result, recommended actions, and analysis metadata.
7. The frontend renders the live analysis pipeline, handoff summary, charts, and exports.

## Backend Modules

- `app/core/`: configuration, security utilities, logging, and constants
- `app/db/`: SQLAlchemy engine/session setup
- `app/models/`: `Case`, `Artifact`, `AnalysisRun`, `RecommendedAction`
- `app/schemas/`: request/response models and normalized AI output contracts
- `app/services/`: case management, artifact storage, dashboard summaries, exports
- `app/ai/`: Gemini client, prompt builder, parser, and orchestration
- `app/api/v1/endpoints/`: API routes

## Frontend Modules

- `app/`: App Router routes for intake, analysis, dashboard, case details, and about
- `components/`: reusable command-center UI components
- `lib/`: API client, demo seeds, chart formatting, validation, and utilities
- `hooks/`: reduced-motion and local preference hooks

## Privacy and Safety

- Secrets never enter the browser bundle
- High-risk cases surface disclaimers and “observed vs inferred” separation
- Confidence and missing-information gaps are always displayed with non-color indicators
- Storage metadata avoids unnecessary duplication of uploaded raw content in logs

## Deployment Notes

- Frontend can deploy to Vercel, Cloud Run, or any Node host
- Backend can deploy to Cloud Run or another ASGI-compatible environment
- Database settings are Cloud SQL-compatible, including connector-based auth via instance connection name
- GCS integration is abstracted so signed URLs or direct uploads can be added later
