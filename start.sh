#!/bin/sh
set -e

echo "Starting Aegis OS (combined mode)..."

# Start FastAPI backend
cd /app/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 &

# Start Next.js frontend
cd /app/frontend
npm run start -- -p 3000 &

# Wait for both services to be ready
sleep 3

# Start nginx in the foreground (PID 1 for Cloud Run health checks)
nginx -g "daemon off;"
