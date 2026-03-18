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

write_recovery_state() {
  export OWNER_RECOVERY_STATUS="$1"
  export OWNER_RECOVERY_MESSAGE="${2:-}"
  python3 - <<'PY'
import json
import os
from pathlib import Path

payload = {
    "status": os.environ["OWNER_RECOVERY_STATUS"],
    "email": os.environ["OWNER_RECOVERY_EMAIL"],
    "password": os.environ["OWNER_RECOVERY_PASSWORD"],
}

message = os.environ.get("OWNER_RECOVERY_MESSAGE")
if message:
    payload["message"] = message

Path(os.environ["OWNER_RECOVERY_INFO"]).write_text(
    json.dumps(payload, ensure_ascii=True),
    encoding="utf-8",
)
PY
}

if [ ! -f "$OWNER_RECOVERY_MARKER" ]; then
  export OWNER_RECOVERY_PASSWORD="$(python3 - <<'PY'
import json
import os
import secrets
from pathlib import Path

info_path = Path(os.environ["OWNER_RECOVERY_INFO"])
if info_path.exists():
    try:
        payload = json.loads(info_path.read_text(encoding="utf-8"))
        password = payload.get("password")
        if password:
            print(password)
            raise SystemExit
    except Exception:
        pass

print("N8N-" + secrets.token_urlsafe(18))
PY
)"

  write_recovery_state "bootstrapping"

  python3 /app/scripts/owner_recovery_server.py "$OWNER_RECOVERY_INFO" "$N8N_PORT" &
  RECOVERY_SERVER_PID=$!

  write_recovery_state "resetting"
  if ! n8n user-management:reset; then
    write_recovery_state "error" "user-management-reset-failed"
    sleep 300
    exit 1
  fi

  write_recovery_state "starting_recovery_n8n"
  N8N_PORT=5679 N8N_HOST=127.0.0.1 n8n start &
  RECOVERY_N8N_PID=$!

  write_recovery_state "waiting_for_recovery_n8n"
  if ! python3 - <<'PY'
import json
import os
import time
import urllib.request

base = "http://127.0.0.1:5679"
deadline = time.time() + 600

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
PY
  then
    write_recovery_state "error" "recovery-n8n-timeout-or-owner-setup-failed"
    kill "$RECOVERY_N8N_PID" 2>/dev/null || true
    wait "$RECOVERY_N8N_PID" 2>/dev/null || true
    sleep 300
    exit 1
  fi

  write_recovery_state "ready"

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
