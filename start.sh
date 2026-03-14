#!/bin/sh
set -eu

export GENERIC_TIMEZONE="${GENERIC_TIMEZONE:-Europe/Warsaw}"
export TZ="${TZ:-$GENERIC_TIMEZONE}"
export N8N_PORT="${N8N_PORT:-${PORT:-5678}}"
export N8N_HOST="${N8N_HOST:-0.0.0.0}"
export RCL_HELPER_HOST="${RCL_HELPER_HOST:-127.0.0.1}"
export RCL_HELPER_PORT="${RCL_HELPER_PORT:-8765}"

/opt/venv/bin/python /app/scripts/rcl_extract_service.py &
HELPER_PID=$!

cleanup() {
  kill "$HELPER_PID" 2>/dev/null || true
}

trap cleanup INT TERM EXIT

n8n start &
N8N_PID=$!
wait "$N8N_PID"
