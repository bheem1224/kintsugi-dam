# Stage 1: Build Next.js frontend (using slim Debian-based Node image to match glibc of runtime)
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Build Python dependencies and compile Rust extensions
FROM python:3.12-slim AS backend-builder
WORKDIR /app/backend

RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libxml2-dev \
    libxmlsec1-dev \
    rustc \
    cargo \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --frozen

COPY backend/ ./
RUN uv pip install ./kintsugi_rs

# Stage 3: Production runtime image
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    imagemagick \
    jpeginfo \
    exiftool \
    libxmlsec1-openssl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && pip install uv \
    && rm -rf /var/lib/apt/lists/*

# Copy backend and its pre-compiled virtual environment
WORKDIR /app/backend
COPY --from=backend-builder /app/backend/.venv ./.venv
COPY backend/ ./

# Copy frontend build artifacts and configuration
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