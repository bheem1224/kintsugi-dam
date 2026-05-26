FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    imagemagick \
    jpeginfo \
    exiftool \
    build-essential \
    pkg-config \
    libxml2-dev \
    xmlsec1-dev \
    libxmlsec1-dev \
    libxmlsec1-openssl \
    rustc \
    cargo \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && pip install uv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --frozen

COPY backend/ ./
RUN uv pip install ./kintsugi_rs

WORKDIR /app/frontend

COPY --from=frontend-builder /app/frontend/package*.json ./
COPY --from=frontend-builder /app/frontend/node_modules ./node_modules
COPY --from=frontend-builder /app/frontend/.next ./.next
COPY --from=frontend-builder /app/frontend/public ./public
COPY --from=frontend-builder /app/frontend/next.config.ts ./ 2>/dev/null || true
COPY --from=frontend-builder /app/frontend/next.config.js ./ 2>/dev/null || true

WORKDIR /app
RUN echo '#!/bin/bash\n\
# FIX: Use uv run to execute uvicorn\n\
cd /app/backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &\n\
cd /app/frontend && npm start &\n\
wait -n\n\
exit $?\n\
' > start.sh && chmod +x start.sh

CMD ["./start.sh"]