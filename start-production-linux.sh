#!/usr/bin/env bash
set -euo pipefail

export APP_ENV="${APP_ENV:-production}"
export SEED_DEMO_DATA="${SEED_DEMO_DATA:-false}"
export AUTO_CREATE_DB="${AUTO_CREATE_DB:-false}"
export WEB_CONCURRENCY="${WEB_CONCURRENCY:-4}"
export GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-60}"
export GUNICORN_KEEP_ALIVE="${GUNICORN_KEEP_ALIVE:-5}"

python -m gunicorn backend.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers "$WEB_CONCURRENCY" \
  --bind 0.0.0.0:8000 \
  --timeout "$GUNICORN_TIMEOUT" \
  --keep-alive "$GUNICORN_KEEP_ALIVE" \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile - \
  --error-logfile -
