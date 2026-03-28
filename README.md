# Aegis OS

Aegis OS is a hackathon-ready emergency intelligence platform for medical triage and disaster response. It accepts messy multi-modal intake, extracts structured facts, identifies urgency, highlights missing critical information, and produces a concise handoff with machine-readable JSON.

## Monorepo Layout

- `frontend/`: Next.js App Router client with a premium command-center UI
- `backend/`: FastAPI service with Gemini orchestration, Postgres models, and export endpoints
- `docs/`: architecture and product notes
- `.env.example`: environment template
- `docker-compose.yml`: local Postgres + app scaffolding

## Core Capabilities

- Intake for text, PDFs, images, transcripts, and mixed notes
- Case modes: Auto Detect, Medical Triage, Disaster Response
- AI output normalized to validated JSON with retry-on-parse-failure handling
- Secure backend-only Gemini access
- Google Cloud Storage upload scaffold
- Exportable JSON and human-readable handoff summaries
- Accessible dashboard, case queue, severity charts, and live analysis pipeline

## Quick Start

1. Copy `.env.example` to `.env` and set backend secrets.
2. Start Postgres with `docker compose up postgres -d`.
3. Start the backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
alembic upgrade head
uvicorn app.main:app --reload
```

For Google Cloud SQL, set `CLOUD_SQL_USE_CONNECTOR=true`, `CLOUD_SQL_CONNECTION_NAME`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` in `.env`. The backend can then connect through the Cloud SQL Python Connector without exposing secrets to the frontend.
The backend reads the repository-root `.env`, so the same file works whether you run from the repo root or from `backend/`.

4. Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

5. Open `http://localhost:3000`.

## Demo Seed Cases

- Medical: `58-year-old diabetic male with chest pain, sweating, and shortness of breath for 20 minutes.`
- Disaster: `Flooding in Sector 9, 12 people trapped, one elderly injured, roads blocked, water above knee height.`

Seed helpers are available in the backend and surfaced in the UI as quick-start examples.

## Security Notes

- Gemini credentials remain server-side only
- File MIME and size validation are enforced in the backend
- Structured outputs are schema-validated before persistence
- Logs avoid raw sensitive payload dumping
- Public-facing UI includes medical/public safety disclaimers and uncertainty labeling

## Testing

- Frontend: Vitest + Testing Library component coverage
- Backend: pytest for schema validation, API routes, and parser logic
- Smoke coverage: minimal end-to-end flow assertions against the API and core UI

## Deployment

- Frontend and backend are deployable independently
- Backend is configured for Cloud SQL-compatible Postgres and Google Cloud Storage
- Frontend reads only the public API base URL from environment

See [docs/architecture.md](/Users/malavikapj/Documents/aegonis/docs/architecture.md) for the system design overview.
# aegis-os
