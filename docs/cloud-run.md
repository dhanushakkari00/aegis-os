# Cloud Run Deployment

## Recommendation

Deploy `frontend` and `backend` as two separate Cloud Run services.

Why:

- The current frontend calls the backend from the browser using `NEXT_PUBLIC_API_BASE_URL`.
- That means the backend needs its own public URL.
- A single Cloud Run service only works cleanly if the frontend proxies all `/api/*` calls internally.

## Important Constraint

The backend currently defaults to SQLite. On Cloud Run, the writable filesystem is ephemeral and does not persist across instance restarts.

Use SQLite on Cloud Run only for a throwaway demo. For any persistent deployment, switch the backend to Cloud SQL Postgres.

## Minimal Two-Service Setup

Assumptions:

- Project ID: `YOUR_PROJECT_ID`
- Region: `asia-south1` or another region you prefer
- Artifact Registry repo: `aegis-os`
- Frontend service: `aegis-os-frontend`
- Backend service: `aegis-os-backend`

## One-Time Setup

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
gcloud artifacts repositories create aegis-os --repository-format=docker --location=asia-south1
```

## Build and Push Images

From the repo root:

```bash
gcloud builds submit ./backend --tag asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/aegis-os/backend:latest
gcloud builds submit ./frontend --tag asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/aegis-os/frontend:latest
```

## Store Backend Secret

```bash
printf '%s' 'YOUR_GEMINI_API_KEY' | gcloud secrets create aegis-gemini-api-key --data-file=-
```

If the secret already exists:

```bash
printf '%s' 'YOUR_GEMINI_API_KEY' | gcloud secrets versions add aegis-gemini-api-key --data-file=-
```

## Deploy Backend

Demo-only SQLite deployment:

```bash
gcloud run deploy aegis-os-backend \
  --image asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/aegis-os/backend:latest \
  --region asia-south1 \
  --platform managed \
  --allow-unauthenticated \
  --cpu 1 \
  --memory 1Gi \
  --min-instances 1 \
  --max-instances 1 \
  --concurrency 1 \
  --set-env-vars APP_ENV=production,FRONTEND_ORIGIN=https://FRONTEND_URL_PLACEHOLDER,GOOGLE_GENAI_MODEL=gemini-2.5-flash,DATABASE_URL=sqlite:///./aegis_os.db \
  --set-secrets GOOGLE_GENAI_API_KEY=aegis-gemini-api-key:latest,GEMINI_API_KEY=aegis-gemini-api-key:latest
```

Notes:

- `min-instances=1`, `max-instances=1`, and `concurrency=1` reduce SQLite corruption risk.
- Data still disappears on restart or revision change.

## Deploy Frontend

After backend deploy, get the backend URL and plug it into `NEXT_PUBLIC_API_BASE_URL`:

```bash
gcloud run deploy aegis-os-frontend \
  --image asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/aegis-os/frontend:latest \
  --region asia-south1 \
  --platform managed \
  --allow-unauthenticated \
  --cpu 1 \
  --memory 1Gi \
  --set-env-vars NEXT_PUBLIC_API_BASE_URL=https://BACKEND_URL/api/v1,NEXT_PUBLIC_APP_NAME='Aegis OS'
```

## Update Backend CORS

Redeploy the backend once you know the frontend URL:

```bash
gcloud run services update aegis-os-backend \
  --region asia-south1 \
  --set-env-vars FRONTEND_ORIGIN=https://FRONTEND_URL
```

## Recommended Production Shape

Use two Cloud Run services plus Cloud SQL Postgres:

- `frontend`: public Cloud Run service
- `backend`: public Cloud Run service
- `Cloud SQL`: Postgres for persistence
- `Secret Manager`: Gemini key

That removes the SQLite persistence problem and is the correct upgrade path.

## Single-Service Option

A single Cloud Run service is not the best fit for the current codebase.

To make one service work, you would need to:

1. Run the frontend as the ingress container.
2. Run the backend as a sidecar container.
3. Proxy all frontend `/api/*` traffic internally to the sidecar on `localhost`.
4. Remove the browser-direct `NEXT_PUBLIC_API_BASE_URL` dependency.

Without that refactor, use two services.

## Useful Commands

Get service URL:

```bash
gcloud run services describe aegis-os-backend --region asia-south1 --format='value(status.url)'
gcloud run services describe aegis-os-frontend --region asia-south1 --format='value(status.url)'
```

Stream logs:

```bash
gcloud run services logs tail aegis-os-backend --region asia-south1
gcloud run services logs tail aegis-os-frontend --region asia-south1
```
