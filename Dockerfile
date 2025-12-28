# ===========================================
# FarMora AI - Unified Docker Image
# Frontend (React/Vite) + Backend (FastAPI)
# ===========================================

# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY farmora-frontend/farmora-chatbot/package*.json ./

# Install dependencies with clean slate (ignore package-lock for cross-platform compatibility)
RUN rm -f package-lock.json && npm install --legacy-peer-deps

# Copy frontend source (excluding node_modules via .dockerignore)
COPY farmora-frontend/farmora-chatbot/ ./

# Build for production
RUN npm run build

# ===========================================
# Stage 2: Final Production Image
# ===========================================
FROM python:3.11-slim

# Install nginx, supervisor, and curl for health check
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy Python requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code (including .env)
COPY farmora_backend/ ./farmora_backend/

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Create directory for nginx pid
RUN mkdir -p /run/nginx

# Expose port 80 (nginx will handle both frontend and API proxy)
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/api/health || exit 1

# Start services using supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
