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
2. Start the backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

The default local path uses SQLite and creates the tables automatically on startup. The backend reads the repository-root `.env`, so the same file works whether you run from the repo root or from `backend/`.

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

Seed example text is surfaced in the UI as quick-start input, but the application always uses the persisted backend path for execution.

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
- Frontend uses the repo-defined `/api/v1` path by default in the combined deployment path

See [docs/architecture.md](/Users/malavikapj/Documents/aegonis/docs/architecture.md) for the system design overview.
Cloud Run steps are in [docs/cloud-run.md](/Users/malavikapj/Documents/aegonis/docs/cloud-run.md).
# aegis-os
