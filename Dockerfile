FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

WORKDIR /app

# Install curl for container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python runtime dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application packages and configuration
COPY config.yaml .
COPY ingestion/ ./ingestion/
COPY processing/ ./processing/
COPY services/ ./services/
COPY api/ ./api/
COPY data/aoi/ ./data/aoi/
COPY data/processed/optimization/scenarios/ ./data/processed/optimization/scenarios/

# Create runtime non-root user and writeable cache directory for S3 runtime objects
RUN groupadd -r climora && useradd -r -g climora -d /app climora && \
    mkdir -p /tmp/climora_data_cache && \
    chown -R climora:climora /app /tmp/climora_data_cache

USER climora

EXPOSE 8000

# Health check instruction
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "api.app:create_app()"]
