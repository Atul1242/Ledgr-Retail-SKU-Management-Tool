# Ledgr — Demand-forecasting SaaS for FMCG distributors
# Single-image build: serves the Flask web app via gunicorn (the scheduler
# container in docker-compose reuses this image and overrides the CMD).

FROM python:3.12-slim AS runtime

# Faster, predictable Python in containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=5000

# System packages: libgomp is required by lightgbm; curl is used by HEALTHCHECK.
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgomp1 curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first so changes to source don't bust the layer cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Run as non-root (created with a fixed UID/GID for predictable volume permissions)
RUN groupadd --system --gid 1001 ledgr && \
    useradd  --system --uid 1001 --gid ledgr --create-home ledgr && \
    mkdir -p /app/logs /app/data/processed /app/data/uploads && \
    chown -R ledgr:ledgr /app
USER ledgr

EXPOSE 5000

# Container-level health probe — gives docker-compose's depends_on
# (condition: service_healthy) something to wait on for the web container.
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/login" >/dev/null || exit 1

# --preload: import the app once in the master process (which runs
#   init_db, _seed_if_empty, _ensure_gst_columns, init_csrf) before
#   forking workers. Without this, both workers race the seed step
#   and one crashes on FK conflicts the first time.
# --access-logfile=- streams request logs to stdout.
# --timeout 120 covers the 45-60s pipeline auto-run on first boot.
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", \
     "--preload", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "--timeout", "120", "app:app"]
