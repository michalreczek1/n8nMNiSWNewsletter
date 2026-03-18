#!/bin/sh
set -eu

export GENERIC_TIMEZONE="${GENERIC_TIMEZONE:-Europe/Warsaw}"
export TZ="${TZ:-$GENERIC_TIMEZONE}"
export N8N_PORT="${N8N_PORT:-${PORT:-5678}}"
export N8N_HOST="${N8N_HOST:-0.0.0.0}"
export RCL_HELPER_HOST="${RCL_HELPER_HOST:-127.0.0.1}"
export RCL_HELPER_PORT="${RCL_HELPER_PORT:-8765}"
export OWNER_RECOVERY_EMAIL="${OWNER_RECOVERY_EMAIL:-wiktor0021@wp.pl}"
export OWNER_RECOVERY_FIRST_NAME="${OWNER_RECOVERY_FIRST_NAME:-Wiktor}"
export OWNER_RECOVERY_LAST_NAME="${OWNER_RECOVERY_LAST_NAME:-Wiktorowicz}"

OWNER_RECOVERY_MARKER="/home/node/.n8n/.owner-recovery-20260318.done"
OWNER_RECOVERY_INFO="/home/node/.n8n/.owner-recovery-20260318.json"
export OWNER_RECOVERY_MARKER
export OWNER_RECOVERY_INFO

mkdir -p /home/node/.n8n

if [ ! -f "$OWNER_RECOVERY_MARKER" ]; then
  export OWNER_RECOVERY_PASSWORD="$(python3 - <<'PY'
import secrets
print("N8N-" + secrets.token_urlsafe(18))
PY
)"

  python3 - <<'PY'
import json
import os
from pathlib import Path

Path(os.environ["OWNER_RECOVERY_INFO"]).write_text(json.dumps({
    "status": "bootstrapping",
    "email": os.environ["OWNER_RECOVERY_EMAIL"],
    "password": os.environ["OWNER_RECOVERY_PASSWORD"]
}, ensure_ascii=True), encoding="utf-8")
PY

  python3 /app/scripts/owner_recovery_server.py "$OWNER_RECOVERY_INFO" "$N8N_PORT" &
  RECOVERY_SERVER_PID=$!

  n8n user-management:reset

  N8N_PORT=5679 N8N_HOST=127.0.0.1 n8n start &
  RECOVERY_N8N_PID=$!

  python3 - <<'PY'
import json
import os
import time
import urllib.error
import urllib.request

base = "http://127.0.0.1:5679"
deadline = time.time() + 120

while time.time() < deadline:
    try:
        with urllib.request.urlopen(base + "/rest/settings", timeout=5) as response:
            if response.status == 200:
                break
    except Exception:
        time.sleep(2)
else:
    raise SystemExit("Timed out waiting for recovery n8n")

payload = json.dumps({
    "email": os.environ["OWNER_RECOVERY_EMAIL"],
    "firstName": os.environ["OWNER_RECOVERY_FIRST_NAME"],
    "lastName": os.environ["OWNER_RECOVERY_LAST_NAME"],
    "password": os.environ["OWNER_RECOVERY_PASSWORD"]
}).encode("utf-8")

request = urllib.request.Request(
    base + "/rest/owner/setup",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(request, timeout=15) as response:
    response.read()

with open(os.environ["OWNER_RECOVERY_INFO"], "w", encoding="utf-8") as handle:
    json.dump({
        "status": "ready",
        "email": os.environ["OWNER_RECOVERY_EMAIL"],
        "password": os.environ["OWNER_RECOVERY_PASSWORD"]
    }, handle)
PY

  kill "$RECOVERY_N8N_PID" 2>/dev/null || true
  wait "$RECOVERY_N8N_PID" 2>/dev/null || true

  # Leave the bootstrap endpoint up briefly so the operator can read the new password.
  sleep 45

  touch "$OWNER_RECOVERY_MARKER"
  kill "$RECOVERY_SERVER_PID" 2>/dev/null || true
  wait "$RECOVERY_SERVER_PID" 2>/dev/null || true
fi

/opt/venv/bin/python /app/scripts/rcl_extract_service.py &
HELPER_PID=$!

cleanup() {
  kill "$HELPER_PID" 2>/dev/null || true
}

trap cleanup INT TERM EXIT

n8n start &
N8N_PID=$!
wait "$N8N_PID"
