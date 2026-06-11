#!/bin/bash
# ---------------------------------------------------------------------------
# docker-entrypoint.sh — container startup script for tech-icons
#
# Usage:
#   SERVER_MODE=http   → MCP Streamable HTTP server  (default)
#   SERVER_MODE=web    → FastAPI web UI
#
# Extra env vars:
#   HOST      — bind address (default: 0.0.0.0)
#   PORT      — bind port    (default: 8765)
#   LOG_LEVEL — log level    (default: info)
# ---------------------------------------------------------------------------
set -euo pipefail

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8765}"
LOG_LEVEL="${LOG_LEVEL:-info}"
SERVER_MODE="${SERVER_MODE:-http}"

echo "==> tech-icons v$(python -c 'from importlib.metadata import version; print(version("tech-icons"))')"
echo "==> Mode: ${SERVER_MODE} | Host: ${HOST} | Port: ${PORT} | Log: ${LOG_LEVEL}"

case "${SERVER_MODE}" in
  web)
    exec tech-icons --web --host "${HOST}" --port "${PORT}" --log-level "${LOG_LEVEL}"
    ;;
  http)
    exec tech-icons --transport http --host "${HOST}" --port "${PORT}" --log-level "${LOG_LEVEL}"
    ;;
  *)
    echo "ERROR: Unknown SERVER_MODE '${SERVER_MODE}'. Valid: http, web"
    exit 1
    ;;
esac
