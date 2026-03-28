# Cloud Run Deployment

## Recommendation

Two deployment shapes are now supported:

- Single combined Cloud Run service using the repo-root [Dockerfile](/Users/malavikapj/Documents/aegonis/Dockerfile) with same-origin `/api/v1`
- Two separate Cloud Run services using [frontend/Dockerfile](/Users/malavikapj/Documents/aegonis/frontend/Dockerfile) and [backend/Dockerfile](/Users/malavikapj/Documents/aegonis/backend/Dockerfile)

Use the combined image when you need the fastest hackathon deployment. Use two services when you want independent scaling or separate release cadence.

## Important Constraint

The backend is now Postgres-first. On Cloud Run, use Cloud SQL Postgres for persistence and avoid filesystem-backed databases entirely.

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
```

For the frontend Dockerfile path, pass a build arg so browser requests go to the backend service directly:

```bash
docker build \
  -f frontend/Dockerfile \
  --build-arg NEXT_PUBLIC_API_BASE_URL=https://BACKEND_URL/api/v1 \
  -t asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/aegis-os/frontend:latest \
  ./frontend

docker push asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/aegis-os/frontend:latest
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

Cloud SQL-backed deployment:

```bash
gcloud run deploy aegis-os-backend \
  --image asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/aegis-os/backend:latest \
  --region asia-south1 \
  --platform managed \
  --allow-unauthenticated \
  --cpu 1 \
  --memory 1Gi \
  --set-env-vars APP_ENV=production,FRONTEND_ORIGIN=https://FRONTEND_URL_PLACEHOLDER,GOOGLE_GENAI_MODEL=gemini-2.5-flash,DATABASE_URL=postgresql+psycopg://DB_USER:DB_PASSWORD@DB_HOST:5432/DB_NAME \
  --set-secrets GOOGLE_GENAI_API_KEY=aegis-gemini-api-key:latest,GEMINI_API_KEY=aegis-gemini-api-key:latest
```

## Deploy Frontend

After backend deploy, build the frontend image with `NEXT_PUBLIC_API_BASE_URL=https://BACKEND_URL/api/v1`, then deploy it:

```bash
gcloud run deploy aegis-os-frontend \
  --image asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/aegis-os/frontend:latest \
  --region asia-south1 \
  --platform managed \
  --allow-unauthenticated \
  --cpu 1 \
  --memory 1Gi
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

That is the primary supported deployment path.

## Single-Service Option

The current repo-root Dockerfile already supports the single-service path.

Behavior:

- Frontend serves the UI
- nginx proxies `/api/*` to FastAPI inside the same container
- Browser requests stay same-origin using the default `/api/v1`

Build and deploy:

```bash
gcloud builds submit . --tag asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/aegis-os/combined:latest

gcloud run deploy aegis-os \
  --image asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/aegis-os/combined:latest \
  --region asia-south1 \
  --platform managed \
  --allow-unauthenticated \
  --cpu 1 \
  --memory 1Gi \
  --set-env-vars APP_ENV=production,DATABASE_URL=postgresql+psycopg://DB_USER:DB_PASSWORD@DB_HOST:5432/DB_NAME \
  --set-secrets GOOGLE_GENAI_API_KEY=aegis-gemini-api-key:latest,GEMINI_API_KEY=aegis-gemini-api-key:latest
```

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
