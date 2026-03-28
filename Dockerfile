# ──────────────────────────────────────────────
#  Aegis OS – Combined Cloud Run Dockerfile
#  Runs Next.js frontend + FastAPI backend
#  behind nginx on a single $PORT (Cloud Run)
# ──────────────────────────────────────────────

# ── Stage 1: Build the Next.js frontend ──────
FROM node:22-alpine AS frontend-build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
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
COPY backend/ /app/backend/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .[dev]

# ── Frontend setup ───────────────────────────
WORKDIR /app/frontend
COPY --from=frontend-build /app/.next ./.next
COPY --from=frontend-build /app/public ./public
COPY --from=frontend-build /app/package.json ./package.json
COPY --from=frontend-build /app/node_modules ./node_modules
COPY --from=frontend-build /app/next.config.ts ./next.config.ts

# ── Nginx config ─────────────────────────────
COPY nginx.conf /etc/nginx/nginx.conf

# ── Startup script ───────────────────────────
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

WORKDIR /app
EXPOSE 8080

CMD ["/app/start.sh"]
