"""One complete n8n inspection every 47 hours, running on the Proxmox host.

The small state file contains audit timestamps/counters and mail deduplication,
not a separate execution collector. The n8n database is never modified.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from croniter import croniter


HOUR = 3600
INTERVAL = 47 * HOUR
PRODUCTION_MODES = {"trigger", "webhook", "integrated", "internal", "error"}
FAILED_STATUSES = {"error", "crashed", "canceled"}
VERSION_URL = "https://registry.npmjs.org/-/package/n8n/dist-tags"
RELEASE_NOTES = "https://docs.n8n.io/changelog/release-notes-2.x/"


def timestamp(value):
    if not value:
        return 0.0
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).timestamp()


def local_time(value):
    return datetime.fromtimestamp(value, ZoneInfo("Europe/Warsaw")).strftime("%d.%m.%Y %H:%M %Z")


def issue(key, title, detail, workflow=None):
    return {"key": key, "title": title, "detail": detail, "workflow_id": workflow}


def read_json(path, default=None):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else default


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temporary = handle.name
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def collect_snapshot(config, since):
    command = ["pct", "exec", str(config["container_id"]), "--", "python3",
               config["probe_path"], "--since", str(since)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=150, check=True)
    return json.loads(completed.stdout)


def fetch_stable_version():
    with urlopen(Request(VERSION_URL, headers={"User-Agent": "n8n-watchdog/1.0"}), timeout=20) as response:
        tags = json.load(response)
    version = tags.get("stable") or tags.get("latest")
    version_tuple(version)  # Reject beta/rc/invalid versions, never advertise them as stable.
    return version


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d+\.\d+\.\d+", value):
        raise ValueError("Brak jednoznacznej stabilnej wersji n8n")
    return tuple(map(int, value.split(".")))


def execution_evidence(snapshot):
    """Join workflow and node events by execution ID; manual/CLI runs cannot mask a missing schedule."""
    runs = {}
    for event in snapshot.get("events", []):
        execution_id = event["execution_id"]
        run = runs.setdefault(execution_id, {"id": execution_id, "workflow_id": event["workflow_id"], "nodes": set()})
        name, when = event["event"], event["time"]
        if event.get("mode"):
            run["mode"] = event["mode"]
        if name == "n8n.workflow.started":
            run["started"] = when
        elif name == "n8n.workflow.success":
            run.update(status="success", stopped=when)
        elif name in {"n8n.workflow.failed", "n8n.workflow.canceled"}:
            run.update(status="error", stopped=when)
        if event.get("node"):
            run["nodes"].add(event["node"])
    for row in snapshot.get("executions", []):
        execution_id = str(row["id"])
        run = runs.setdefault(execution_id, {"id": execution_id, "nodes": set()})
        run.update(workflow_id=row["workflowId"], mode=row["mode"], status=row["status"],
                   started=timestamp(row["startedAt"]), stopped=timestamp(row["stoppedAt"]),
                   wait_till=timestamp(row.get("waitTill")))
    return list(runs.values())


def schedule_plan(rule):
    """Cron for calendar rules; conservative gap limits for n8n's anchored multi-day intervals."""
    field = rule.get("field", "days")
    minute = int(rule.get("triggerAtMinute", 0))
    hour = int(rule.get("triggerAtHour", 0))
    if not 0 <= minute <= 59 or not 0 <= hour <= 23:
        raise ValueError("Nieprawidłowa godzina harmonogramu")
    if field == "cronExpression":
        expression = rule.get("expression", "")
        if len(expression.split()) not in {5, 6}:
            raise ValueError("Nieprawidłowa liczba pól cron")
        return expression, None
    if field in {"seconds", "minutes", "hours"}:
        amount = int(rule.get(f"{field}Interval", 30 if field == "minutes" else 1))
        if amount <= 0:
            raise ValueError("Interwał musi być dodatni")
        return None, amount * {"seconds": 1, "minutes": 60, "hours": HOUR}[field]
    if field == "days":
        days = int(rule.get("daysInterval", 1))
        if days <= 0:
            raise ValueError("Interwał musi być dodatni")
        return (f"{minute} {hour} * * *", None) if days == 1 else (None, days * 24 * HOUR)
    if field == "weeks":
        weeks = int(rule.get("weeksInterval", 1))
        weekdays = rule.get("triggerAtDay", [0])
        if weeks <= 0 or not weekdays or any(int(day) not in range(7) for day in weekdays):
            raise ValueError("Nieprawidłowy harmonogram tygodniowy")
        return (f"{minute} {hour} * * {','.join(map(str, weekdays))}", None) if weeks == 1 else (None, weeks * 7 * 24 * HOUR)
    raise ValueError(f"Nieobsługiwany typ harmonogramu: {field}")


def last_due(expression, now, timezone_name):
    moment = datetime.fromtimestamp(now, ZoneInfo(timezone_name))
    iterator = croniter(expression, moment, second_at_beginning=len(expression.split()) == 6)
    return iterator.get_prev(datetime).timestamp()


def evaluate(snapshot, config, state, now):
    problems = list(snapshot.get("problems", []))
    workflows = {workflow["id"]: workflow for workflow in snapshot.get("workflows", [])}
    if "workflows" not in snapshot:
        return problems, dict(state.get("trigger_success", {}))
    runs = execution_evidence(snapshot)
    required = config.get("required_workflows", {})
    ignored = set(config.get("ignored_workflows", []))
    credentials = set(snapshot.get("credential_ids", []))
    statistics = {(row["workflowId"], row["name"]): row for row in snapshot.get("statistics", [])}
    trigger_status = {(row["workflowId"], row["nodeId"]): row for row in snapshot.get("triggers", [])}
    cached_success = dict(state.get("trigger_success", {}))
    since = state.get("last_check", now - INTERVAL)
    for workflow_id, name in required.items():
        if workflow_id in ignored:
            continue
        workflow = workflows.get(workflow_id)
        if not workflow or not workflow["active"] or workflow["isArchived"]:
            problems.append(issue(f"inactive/{workflow_id}", f"Wymagany workflow jest wyłączony: {name}",
                                  "Workflow z listy wymaganych został wyłączony, zarchiwizowany albo usunięty.", workflow_id))
    for workflow_id, workflow in workflows.items():
        if not workflow["active"] or workflow["isArchived"] or workflow_id in ignored:
            continue
        name = workflow["name"]
        if not workflow["activeVersionId"] or not workflow.get("published_version_found", False):
            problems.append(issue(f"unpublished/{workflow_id}", f"Brak opublikowanej wersji: {name}",
                                  "Workflow jest aktywny, ale nie ma dostępnej wersji produkcyjnej.", workflow_id))
            continue
        nodes = {node["name"]: node for node in workflow["nodes"]}
        connections = workflow["connections"]
        nodes_by_id = {node["id"]: node for node in nodes.values()}
        for node_id, schedule_name in config.get("required_schedules", {}).get(workflow_id, {}).items():
            expected = nodes_by_id.get(node_id)
            if not expected or expected["disabled"] or not expected["type"].endswith(".scheduleTrigger"):
                problems.append(issue(f"required-schedule/{workflow_id}/{node_id}", f"Wymagany harmonogram jest wyłączony: {name}",
                                      f"Nieaktywny lub usunięty harmonogram „{schedule_name}”.", workflow_id))
        for source, outputs in connections.items():
            targets = [edge["node"] for branches in outputs.values() for branch in branches for edge in branch]
            missing = [node for node in [source, *targets] if node not in nodes]
            if missing:
                problems.append(issue(f"graph/{workflow_id}/{source}", f"Uszkodzone połączenie: {name}",
                                      f"Połączenie wskazuje nieistniejący węzeł: {', '.join(missing)}.", workflow_id))
        for node in nodes.values():
            if node["disabled"]:
                continue
            missing_credentials = set(node.get("credential_ids", [])) - credentials
            if missing_credentials:
                problems.append(issue(f"credentials/{workflow_id}/{node['id']}", f"Brak poświadczenia: {name}",
                                      f"Węzeł „{node['name']}” odwołuje się do usuniętego poświadczenia.", workflow_id))
        schedules = [node for node in nodes.values() if node["type"].endswith(".scheduleTrigger") and not node["disabled"]]
        if not schedules and any(node["type"].endswith(".scheduleTrigger") for node in nodes.values()):
            problems.append(issue(f"disabled-schedules/{workflow_id}", f"Wszystkie harmonogramy są wyłączone: {name}",
                                  "Aktywny workflow ma wyłączone wszystkie węzły harmonogramu.", workflow_id))
        production = [run for run in runs if run["workflow_id"] == workflow_id and run.get("mode") in PRODUCTION_MODES]
        for run in production:
            if run.get("status") in FAILED_STATUSES and max(run.get("stopped", 0), run.get("started", 0)) >= since:
                if str(run["id"]) not in state.get("notified_executions", []):
                    problems.append(issue(f"execution/{run['id']}", f"Błąd wykonania: {name}",
                                          f"Wykonanie #{run['id']}, status: {run['status']}, {local_time(run.get('stopped') or run.get('started') or now)}.", workflow_id))
            if run.get("status") in {"running", "new"} and now - run.get("started", now) > config.get("max_runtime_hours", 2) * HOUR:
                problems.append(issue(f"stuck/{run['id']}", f"Zbyt długie wykonanie: {name}",
                                      f"Wykonanie #{run['id']} trwa ponad dopuszczalny czas.", workflow_id))
            if run.get("status") == "waiting" and run.get("wait_till") and now - run["wait_till"] > HOUR:
                problems.append(issue(f"waiting/{run['id']}", f"Nie wznowiono wykonania: {name}",
                                      f"Wykonanie #{run['id']} czeka ponad godzinę po zaplanowanym wznowieniu.", workflow_id))
        error_stats = statistics.get((workflow_id, "production_error"))
        if error_stats:
            previous = state.get("error_counts", {}).get(workflow_id)
            latest_error = timestamp(error_stats["latestEvent"])
            # n8n counts CLI runs under production_* statistics too. Do not
            # relabel known diagnostic failures as failures of the scheduler.
            excluded = [run for run in runs if run["workflow_id"] == workflow_id
                        and run.get("mode") not in PRODUCTION_MODES and run.get("status") in FAILED_STATUSES
                        and max(run.get("stopped", 0), run.get("started", 0)) >= since]
            latest_is_diagnostic = any(abs((run.get("stopped") or run.get("started") or 0) - latest_error) < 5 for run in excluded)
            recent = latest_error >= since and not latest_is_diagnostic
            increased = previous is not None and error_stats["count"] - previous > len(excluded)
            if (recent or increased) and not any(p["key"].startswith("execution/") and p.get("workflow_id") == workflow_id for p in problems):
                problems.append(issue(f"error-counter/{workflow_id}/{error_stats['count']}", f"Odnotowano błędy produkcyjne: {name}",
                                      f"Statystyki n8n potwierdzają błąd z {local_time(timestamp(error_stats['latestEvent']))}. "
                                      "Szczegóły wykonania mogą być już usunięte przez retencję.", workflow_id))
        for schedule in schedules:
            key = f"{workflow_id}/{schedule['id']}"
            edges = [edge["node"] for branch in connections.get(schedule["name"], {}).get("main", []) for edge in branch]
            if not edges:
                problems.append(issue(f"disconnected/{key}", f"Odłączony harmonogram: {name}",
                                      f"Węzeł „{schedule['name']}” nie uruchamia żadnego następnego kroku.", workflow_id))
                continue
            activation = trigger_status.get((workflow_id, schedule["id"]))
            if not activation or activation["versionId"] != workflow["activeVersionId"] or activation["status"] != "activated":
                problems.append(issue(f"trigger/{key}", f"Harmonogram nie jest zarejestrowany: {name}",
                                      f"Brak potwierdzenia aktywacji „{schedule['name']}” dla opublikowanej wersji.", workflow_id))
            candidates = [run.get("stopped", 0) for run in production if run.get("status") == "success"
                          and ({schedule["name"], *edges} & run["nodes"])]
            latest = max([cached_success.get(key, 0), *candidates])
            if len(schedules) == 1:
                stat = statistics.get((workflow_id, "production_success"))
                stat_time = timestamp(stat["latestEvent"]) if stat else 0
                diagnostic_success = any(run["workflow_id"] == workflow_id and run.get("mode") not in PRODUCTION_MODES
                                         and run.get("status") == "success"
                                         and abs((run.get("stopped") or run.get("started") or 0) - stat_time) < 5 for run in runs)
                latest = max(latest, stat_time if not diagnostic_success else 0)
            cached_success[key] = latest
            baseline = max(timestamp(workflow["updatedAt"]), state.get("monitor_started", now),
                           timestamp(activation["updatedAt"]) if activation else 0)
            rules = schedule.get("parameters", {}).get("rule", {}).get("interval", [])
            if not rules:
                problems.append(issue(f"schedule/{key}", f"Pusty harmonogram: {name}", schedule["name"], workflow_id))
            for index, rule in enumerate(rules):
                try:
                    expression, gap = schedule_plan(rule)
                    grace = config.get("schedule_grace_minutes", 120) * 60
                    if expression:
                        due = last_due(expression, now - grace, workflow["timezone"])
                        missed = due >= baseline and latest < due
                    else:
                        due = max(latest, baseline) + gap
                        missed = now > due + grace
                    running = any(run.get("status") in {"running", "waiting", "new"} and run.get("started", 0) >= due for run in production)
                    if missed and not running:
                        problems.append(issue(f"silent/{key}/{index}", f"Brak oczekiwanego wykonania: {name}",
                                              f"Harmonogram „{schedule['name']}”: brak potwierdzonego sukcesu po {local_time(due)}. "
                                              f"Tolerancja opóźnienia: {grace // 60} minut.", workflow_id))
                except (ValueError, KeyError, TypeError) as exc:
                    problems.append(issue(f"schedule/{key}/{index}", f"Nie można zweryfikować harmonogramu: {name}", str(exc), workflow_id))
    return problems, cached_success


def render_report(problems, config, now, current_version=None):
    escaped = html.escape
    sections = []
    text_sections = []
    base_url = config.get("editor_url", "https://n8n.familyos.pl").rstrip("/")
    for problem in problems:
        workflow_id = problem.get("workflow_id")
        link = f"{base_url}/workflow/{quote(workflow_id, safe='')}" if workflow_id else None
        sections.append(f'<section><h2>{escaped(problem["title"])}</h2><p>{escaped(problem["detail"])}</p>'
                        + (f'<a href="{escaped(link)}">Otwórz workflow</a>' if link else "") + '</section>')
        text_sections.append(f"{problem['title']}\n{problem['detail']}" + (f"\n{link}" if link else ""))
    heading = f"n8n — raport wymagający uwagi ({len(problems)})"
    document = '''<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;padding:24px 16px;background:#f1f5f9;font:15px/1.65 Arial,sans-serif;color:#1e293b}
main{max-width:760px;margin:auto}header{background:#172554;color:white;padding:28px;border-radius:16px}
h1{font-size:25px;line-height:1.3;margin:8px 0}header p{margin:8px 0;color:#dbeafe}
section{background:white;border:1px solid #cbd5e1;border-left:5px solid #d97706;padding:20px;margin-top:16px;border-radius:12px;overflow-wrap:anywhere}
h2{font-size:18px;margin:0 0 8px}p{margin:8px 0}a{color:#1d4ed8;font-weight:bold}footer{font-size:12px;color:#64748b;margin:20px 0}</style>
</head><body><main><header><div>KONTROLA N8N · TYLKO NIEPRAWIDŁOWOŚCI</div><h1>''' + escaped(heading) + '</h1><p>' + escaped(local_time(now)) + '</p></header>'
    document += ''.join(sections)
    document += '<footer>Kontrola co 47 godzin na hoście Proxmox, poza kontenerem n8n. Poprawne statusy nie są wysyłane.'
    document += f' Wersja uruchomiona: {escaped(current_version or "nieznana")}.</footer></main></body></html>'
    return {"from": config["from_email"], "to": config["to_emails"], "subject": heading,
            "html": document, "text": heading + "\n" + local_time(now) + "\n\n" + "\n\n".join(text_sections)}


def send_report(payload, idempotency_key):
    secret = os.environ.get("RESEND_API_KEY", "")
    if not secret:
        raise RuntimeError("Brak RESEND_API_KEY dla monitora")
    request = Request("https://api.resend.com/emails", data=json.dumps(payload).encode("utf-8"), method="POST",
                      headers={"Authorization": f"Bearer {secret}", "Content-Type": "application/json",
                               "User-Agent": "n8n-watchdog/1.0",
                               "Idempotency-Key": idempotency_key})
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if not result.get("id"):
        raise RuntimeError("Resend nie potwierdził przyjęcia raportu")
    return result["id"]


def extract_resend_key(credential):
    """Existing n8n Header Auth credentials may store a bare key or a Bearer value."""
    if credential.get("name", "").strip().lower() != "authorization":
        raise ValueError("Unexpected sending credential type")
    value = credential.get("value", "").strip()
    secret = value[7:].strip() if value.lower().startswith("bearer ") else value
    if not re.fullmatch(r"re_[A-Za-z0-9_]+", secret):
        raise ValueError("Unexpected sending key format")
    return secret


def inspect(config, state, now, snapshot, stable=None, update_error=None):
    problems, trigger_success = evaluate(snapshot, config, state, now)
    if state.get("last_check") and now - state["last_check"] >= 48 * HOUR:
        problems.append(issue("monitor/gap", "Przerwa w kontroli przekroczyła retencję historii",
                              "Od poprzedniej kontroli minęło co najmniej 48 godzin. Część szczegółów wykonań mogła zniknąć."))
    if snapshot.get("disk_used_percent", 0) >= 90:
        problems.append(issue("disk/container", "Mało miejsca w kontenerze n8n", f"Zajęte miejsce: {snapshot['disk_used_percent']}%."))
    current = snapshot.get("version")
    if update_error:
        problems.append(issue("version/check", "Nie można sprawdzić aktualizacji n8n", update_error))
    elif current and stable:
        if version_tuple(stable) > version_tuple(current) and state.get("notified_update") != stable:
            problems.append(issue(f"update/{stable}", f"Dostępna stabilna aktualizacja n8n: {stable}",
                                  f"Uruchomiona wersja: {current}. Stabilna wersja w oficjalnym rejestrze npm: {stable}. "
                                  f"Zalecane: backup, test aktualizacji i przebudowanie obrazu z poprawką base path. "
                                  f"Monitor nie instaluje aktualizacji. Opis zmian: {RELEASE_NOTES}"))
    next_state = {**state, "monitor_started": state.get("monitor_started", now), "last_check": now,
                  "trigger_success": trigger_success,
                  "error_counts": {row["workflowId"]: row["count"] for row in snapshot.get("statistics", []) if row["name"] == "production_error"}}
    return problems, next_state


def deliver_outbox(state_path, outbox_path, outbox):
    """Retry the exact same body/key, including after a crash following acceptance."""
    state = read_json(state_path, {})
    key = outbox["key"]
    if state.get("last_delivery", {}).get("key") != key:
        resend_id = send_report(outbox["payload"], key)
        next_state = outbox["next_state"]
        next_state["last_delivery"] = {"id": resend_id, "at": outbox["at"], "key": key,
                                       "issues": outbox["issues"]}
        write_json(state_path, next_state)
    Path(outbox_path).unlink(missing_ok=True)


def run(config_path, state_path, *, dry_run=False, preview=None):
    config = read_json(config_path)
    state = read_json(state_path, {})
    outbox_path = Path(state_path).with_suffix(".outbox.json")
    outbox = read_json(outbox_path)
    if outbox and not dry_run:
        deliver_outbox(state_path, outbox_path, outbox)
        return {"mail_sent": True, "retried_delivery": True, "issues": outbox["issues"]}
    now = datetime.now(timezone.utc).timestamp()
    # Look back 48h on the first inspection, then overlap the previous check by 60s.
    since = state.get("last_check", now - 48 * HOUR) - 60
    try:
        snapshot = collect_snapshot(config, since)
    except (OSError, ValueError, subprocess.SubprocessError):
        snapshot = {"problems": [issue("container/unreachable", "Brak dostępu do kontenera n8n",
                                       f"Nie powiodła się kontrola LXC {config['container_id']}. Sprawdź stan kontenera na Proxmoxie.")]}
    stable, update_error = None, None
    try:
        stable = fetch_stable_version()
    except Exception as exc:
        update_error = f"Odczyt oficjalnego rejestru wersji nie powiódł się ({type(exc).__name__})."
    problems, next_state = inspect(config, state, now, snapshot, stable, update_error)
    if problems:
        payload = render_report(problems, config, now, snapshot.get("version"))
        if preview:
            Path(preview).write_text(payload["html"], encoding="utf-8")
        if not dry_run:
            signature = json.dumps({"previous_check": state.get("last_check"), "keys": sorted(p["key"] for p in problems)}, sort_keys=True)
            key = "n8n-watchdog/" + hashlib.sha256(signature.encode()).hexdigest()
            for problem in problems:
                if problem["key"].startswith("update/"):
                    next_state["notified_update"] = stable
            notified = set(state.get("notified_executions", []))
            notified.update(p["key"].split("/", 1)[1] for p in problems if p["key"].startswith("execution/"))
            next_state["notified_executions"] = sorted(notified, key=lambda item: int(item))[-2000:]
            outbox = {"payload": payload, "key": key, "next_state": next_state, "at": now,
                      "issues": [p["key"] for p in problems]}
            write_json(outbox_path, outbox)
            deliver_outbox(state_path, outbox_path, outbox)
    if not dry_run and not problems:
        write_json(state_path, next_state)
    summary = {"dry_run": dry_run, "issues": [{k: v for k, v in p.items()} for p in problems],
               "mail_sent": bool(problems) and not dry_run, "checked_at": local_time(now),
               "current_version": snapshot.get("version"), "stable_version": stable,
               "active_workflows": sum(bool(w["active"] and not w["isArchived"]) for w in snapshot.get("workflows", []))}
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="/etc/n8n-watchdog/config.json")
    parser.add_argument("--state", default="/var/lib/n8n-watchdog/state.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preview")
    args = parser.parse_args()
    print(json.dumps(run(args.config, args.state, dry_run=args.dry_run, preview=args.preview), ensure_ascii=True))
