# ============================================================
# Meridian API — Multi-stage Dockerfile
# ============================================================
# Stage 1: Builder — install dependencies
# Stage 2: Runtime — minimal production image
# ============================================================

# --- Builder stage ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system dependencies for building Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy package metadata first (cache layer)
COPY pyproject.toml README.md ./

# Install production dependencies only
RUN pip install --no-cache-dir --prefix=/install .

# --- Runtime stage ---
FROM python:3.12-slim AS runtime

# Security: run as non-root user
RUN groupadd --gid 1000 meridian && \
    useradd --uid 1000 --gid meridian --shell /bin/bash --create-home meridian

# Install runtime system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application code
COPY services/api-gateway/finance_assistant/ ./finance_assistant/

# Switch to non-root user
USER meridian

# Health check for ECS / Docker
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "finance_assistant.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info"]
