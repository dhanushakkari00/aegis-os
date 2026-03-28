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
- Optional Gmail handoff delivery for stored case contact emails
- Google Cloud Storage upload scaffold
- Exportable JSON and human-readable handoff summaries
- Accessible dashboard, case queue, severity charts, and live analysis pipeline

## Quick Start

1. Copy `.env.example` to `.env` and set backend secrets.
2. Start the backend with Postgres:

```bash
docker compose up postgres -d
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

The default local path is Postgres-first. The backend reads the repository-root `.env`, so the same file works whether you run from the repo root or from `backend/`. Tables are created automatically on startup.

3. Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

4. Open `http://localhost:3000`.

## Docker Compose Postgres

Use Docker Compose when you want the full local stack:

```bash
docker compose up --build
```

That path now wires:

- `postgres` for persistence
- `backend` with `DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/aegis_os`
- `frontend` with an internal `/api/*` proxy to the backend container

## Sample Intakes

- Medical: `58-year-old diabetic male with chest pain, sweating, and shortness of breath for 20 minutes.`
- Disaster: `Flooding in Sector 9, 12 people trapped, one elderly injured, roads blocked, water above knee height.`

These sample texts are useful for verification and backend seeding, but the app itself always runs through the persisted production path.

## Security Notes

- Gemini credentials remain server-side only
- Gmail OAuth credentials remain server-side only
- `SECRET_KEY` is required explicitly in production for auth token signing
- Keep `.env` local only. Do not commit it to GitHub. Use Cloud Run env vars and Secret Manager for deployed services.
- File MIME and size validation are enforced in the backend
- Structured outputs are schema-validated before persistence
- Logs avoid raw sensitive payload dumping
- Public-facing UI includes medical/public safety disclaimers and uncertainty labeling

## Testing

- Frontend: Vitest + Testing Library component coverage
- Backend: pytest for schema validation, API routes, and parser logic
- Smoke coverage: Playwright for the live landing flow

Install Playwright browsers once before running E2E:

```bash
cd frontend
npx playwright install chromium
npm run test:e2e
```

## Deployment

- Frontend and backend are deployable independently
- Backend is configured for Cloud SQL-compatible Postgres and Google Cloud Storage
- Frontend defaults to same-origin `/api/v1`, but also supports `NEXT_PUBLIC_API_BASE_URL` for separate frontend/backend deployment
- Frontend container builds support `INTERNAL_API_ORIGIN` for reverse-proxy deployments such as Docker Compose or single-service ingress

See [docs/architecture.md](/Users/malavikapj/Documents/aegonis/docs/architecture.md) for the system design overview.
Cloud Run steps are in [docs/cloud-run.md](/Users/malavikapj/Documents/aegonis/docs/cloud-run.md).
