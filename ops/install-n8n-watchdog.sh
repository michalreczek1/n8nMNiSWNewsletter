#!/usr/bin/env bash
# Run on the Proxmox host from a staged copy of this repository.
# Prepares files only; enabling the timer is an explicit deployment step.
set -euo pipefail
umask 077

release_root="$(cd "$(dirname "$0")/.." && pwd)"
app_dir=/opt/n8n-watchdog
install -d -m 700 "$app_dir" /etc/n8n-watchdog /var/lib/n8n-watchdog
backup_dir="$app_dir/backups/$(date -u +%Y%m%dT%H%M%SZ)"
install -d -m 700 "$backup_dir"
for previous in "$app_dir/n8n_watchdog.py" /etc/n8n-watchdog/config.json /etc/systemd/system/n8n-watchdog.service /etc/systemd/system/n8n-watchdog.timer; do
  if [ -f "$previous" ]; then cp "$previous" "$backup_dir/$(basename "$previous")"; fi
done

if [ ! -x "$app_dir/venv/bin/pip" ]; then
  python3 -m venv "$app_dir/venv"
fi
"$app_dir/venv/bin/pip" install -r "$release_root/requirements-watchdog.txt"
install -m 600 "$release_root/scripts/n8n_watchdog.py" "$app_dir/n8n_watchdog.py"
pct push 105 "$release_root/scripts/n8n_watchdog_probe.py" /opt/n8n-app/scripts/n8n_watchdog_probe.py
install -m 600 "$release_root/ops/n8n-watchdog.config.example.json" "$app_dir/config.example.json"

# Bootstrap the required-workflow list from workflows which are active now.
# Intentional archives are excluded. Subsequent deploys preserve this policy.
if [ ! -f /etc/n8n-watchdog/config.json ]; then
  "$app_dir/venv/bin/python" - <<'PY'
import sys,time
sys.path.insert(0,'/opt/n8n-watchdog')
from n8n_watchdog import read_json,write_json,collect_snapshot
config=read_json('/opt/n8n-watchdog/config.example.json')
snapshot=collect_snapshot(config,time.time()-48*3600)
if 'workflows' not in snapshot:
    raise SystemExit('Cannot establish the required workflow baseline')
config['required_workflows']={w['id']:w['name'] for w in snapshot['workflows'] if w['active'] and not w['isArchived']}
config['required_schedules']={w['id']:{n['id']:n['name'] for n in w['nodes'] if n['type'].endswith('.scheduleTrigger') and not n['disabled']}
                              for w in snapshot['workflows'] if w['active'] and not w['isArchived']}
write_json('/etc/n8n-watchdog/config.json',config)
print('Required workflow baseline:',len(config['required_workflows']))
PY
fi

"$app_dir/venv/bin/python" - <<'PY'
import sys,time
sys.path.insert(0,'/opt/n8n-watchdog')
from n8n_watchdog import read_json,write_json,collect_snapshot
config=read_json('/etc/n8n-watchdog/config.json')
if 'required_schedules' not in config:
    snapshot=collect_snapshot(config,time.time()-48*3600)
    if 'workflows' not in snapshot:
        raise SystemExit('Cannot establish the required schedule baseline')
    config['required_schedules']={w['id']:{n['id']:n['name'] for n in w['nodes'] if n['type'].endswith('.scheduleTrigger') and not n['disabled']}
                                  for w in snapshot['workflows'] if w['active'] and not w['isArchived']}
    write_json('/etc/n8n-watchdog/config.json',config)
PY

# Reuse the already authorized sending key; never print or store it in git.
if [ ! -f /etc/n8n-watchdog/mail.env ]; then
  "$app_dir/venv/bin/python" - <<'PY'
import json,os,subprocess,sys
sys.path.insert(0,'/opt/n8n-watchdog')
from n8n_watchdog import extract_resend_key
prefix=['pct','exec','105','--','docker','exec','n8n']
credential_file='/tmp/n8n-watchdog-resend-bootstrap.json'
try:
    subprocess.run(prefix+['sh','-c','umask 077; n8n export:credentials --id=MNiSWResend20261026 --decrypted --output=/tmp/n8n-watchdog-resend-bootstrap.json'],check=True,stdout=subprocess.DEVNULL)
    completed=subprocess.run(prefix+['cat',credential_file],capture_output=True,text=True,check=True)
    credential=json.loads(completed.stdout)[0]['data']
    secret=extract_resend_key(credential)
    descriptor=os.open('/etc/n8n-watchdog/mail.env',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(descriptor,'w') as handle:
        handle.write('RESEND_API_KEY='+secret+'\n')
    print('Independent mail credential configured (secret omitted)')
finally:
    subprocess.run(prefix+['rm','-f',credential_file],check=False,stdout=subprocess.DEVNULL)
PY
fi

install -m 644 "$release_root/ops/n8n-watchdog.service" /etc/systemd/system/n8n-watchdog.service
install -m 644 "$release_root/ops/n8n-watchdog.timer" /etc/systemd/system/n8n-watchdog.timer
systemctl daemon-reload
systemd-analyze verify /etc/systemd/system/n8n-watchdog.service /etc/systemd/system/n8n-watchdog.timer
"$app_dir/venv/bin/python" "$app_dir/n8n_watchdog.py" --dry-run --preview /var/lib/n8n-watchdog/preview.html
echo 'Prepared. Enable after verification: systemctl enable --now n8n-watchdog.timer'
