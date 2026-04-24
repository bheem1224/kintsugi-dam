# ==========================================
# STAGE 1: Build the Next.js Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ==========================================
# STAGE 2: The Final Unified Image
# ==========================================
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies, Node.js, and uv
RUN apt-get update && apt-get install -y \
    curl \
    imagemagick \
    jpeginfo \
    exiftool \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && pip install uv \
    && rm -rf /var/lib/apt/lists/*

# Setup the FastAPI Backend
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock* ./
# Install the python dependencies
RUN uv sync --frozen

# FIX: Actually copy the Python application code into the container
COPY backend/ ./

# Bring in the compiled Frontend from Stage 1
WORKDIR /app/frontend
COPY --from=frontend-builder /app/frontend ./

# Expose both ports
EXPOSE 3000 8000

# Create a startup script to run BOTH servers simultaneously
WORKDIR /app
RUN echo '#!/bin/bash\n\
# FIX: Use uv run to execute uvicorn\n\
cd /app/backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &\n\
cd /app/frontend && npm start &\n\
wait -n\n\
exit $?\n\
' > start.sh && chmod +x start.sh

CMD ["./start.sh"]