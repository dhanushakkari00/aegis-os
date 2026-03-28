# ──────────────────────────────────────────────
#  Aegis OS – Combined Cloud Run Dockerfile
#  Runs Next.js frontend + FastAPI backend
#  behind nginx on a single $PORT (Cloud Run)
# ──────────────────────────────────────────────

# ── Stage 1: Build the Next.js frontend ──────
FROM node:22-alpine AS frontend-build
WORKDIR /app
ARG NEXT_PUBLIC_API_BASE_URL=/api/v1
ARG INTERNAL_API_ORIGIN=http://127.0.0.1:8000
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
ENV INTERNAL_API_ORIGIN=${INTERNAL_API_ORIGIN}
ENV NEXT_PUBLIC_APP_NAME="Aegis OS"
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN mkdir -p /app/public && touch /app/public/.gitkeep
RUN npm run build

# ── Stage 2: Final runtime image ─────────────
FROM python:3.12-slim

# Install nginx and Node.js (needed for Next.js server)
RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx curl && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Backend setup ────────────────────────────
WORKDIR /app/backend
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY backend/ /app/backend/

# ── Frontend setup ───────────────────────────
WORKDIR /app/frontend
COPY --from=frontend-build /app/.next ./.next
COPY --from=frontend-build /app/public ./public
COPY --from=frontend-build /app/package.json ./package.json
COPY --from=frontend-build /app/node_modules ./node_modules
COPY --from=frontend-build /app/next.config.ts ./next.config.ts

# ── Nginx config ─────────────────────────────
COPY nginx.conf /etc/nginx/nginx.conf.template

# ── Startup script ───────────────────────────
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

WORKDIR /app
EXPOSE 8080

CMD ["/app/start.sh"]
