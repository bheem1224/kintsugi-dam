# ==========================================
# STAGE 1: Build the Next.js Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy frontend source and build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ==========================================
# STAGE 2: The Final Unified Image
# ==========================================
FROM python:3.12-slim
WORKDIR /app

# Install Node.js (Required to run the Next.js server) and Curl
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Setup the FastAPI Backend
WORKDIR /app/backend
COPY backend/pyproject.toml ./
# Install 'uv' and dependencies
RUN pip install uv && uv pip install --system -r pyproject.toml
COPY backend/ ./

# Bring in the compiled Frontend from Stage 1
WORKDIR /app/frontend
COPY --from=frontend-builder /app/frontend ./

# Expose both ports (3000 for UI, 8000 for API)
EXPOSE 3000 8000

# Create a startup script to run BOTH servers simultaneously
WORKDIR /app
RUN echo '#!/bin/bash\n\
# Start FastAPI backend in the background\n\
cd /app/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 &\n\
# Start Next.js frontend in the background\n\
cd /app/frontend && npm start &\n\
# Wait for any process to exit. If one crashes, the container restarts.\n\
wait -n\n\
exit $?\n\
' > start.sh && chmod +x start.sh

# Run the startup script
CMD ["./start.sh"]