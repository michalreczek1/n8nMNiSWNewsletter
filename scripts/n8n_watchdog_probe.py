"""Read-only telemetry from LXC 105. No credentials or workflow input/output leave it."""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen


DATA_DIR = Path("/home/n8n/.n8n/data/.n8n")


def stamp(value):
    if not value:
        return 0.0
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).timestamp()


def health(url):
    try:
        with urlopen(url, timeout=5) as response:
            return response.status == 200
    except Exception:
        return False


def read_events(directory, since):
    events = []
    oldest = None
    malformed = 0
    files = list(Path(directory).glob("n8nEventLog*.log"))
    for path in files:
        try:
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        event = json.loads(line)
                        when = stamp(event.get("ts"))
                    except (ValueError, TypeError):
                        # n8n may still be writing the final line.
                        if line.endswith("\n"):
                            malformed += 1
                        continue
                    if not event.get("eventName"):
                        continue
                    oldest = when if oldest is None else min(oldest, when)
                    if when < since:
                        continue
                    name = event["eventName"]
                    if name not in {
                        "n8n.workflow.started", "n8n.workflow.success",
                        "n8n.workflow.failed", "n8n.workflow.canceled",
                        "n8n.node.started", "n8n.node.finished",
                    }:
                        continue
                    payload = event.get("payload", {})
                    if not payload.get("executionId") or not payload.get("workflowId"):
                        continue
                    events.append({
                        "time": when, "event": name,
                        "execution_id": str(payload["executionId"]),
                        "workflow_id": payload["workflowId"],
                        "mode": payload.get("mode"),
                        "node": payload.get("nodeName"),
                    })
        except FileNotFoundError:
            # A rotation may rename a file between glob and open.
            continue
    return {"events": sorted(events, key=lambda item: item["time"]),
            "oldest_event": oldest, "log_files": len(files), "malformed_lines": malformed}


def normalize_nodes(nodes):
    return [{
        "id": node["id"], "name": node["name"], "type": node["type"],
        "disabled": bool(node.get("disabled")),
        "parameters": node.get("parameters", {}) if node["type"].endswith(".scheduleTrigger") else {},
        "credential_ids": [value["id"] for value in node.get("credentials", {}).values() if value.get("id")],
    } for node in nodes]


def read_database(path, since):
    connection = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        workflows = []
        for row in connection.execute("SELECT * FROM workflow_entity"):
            workflow = {key: row[key] for key in ("id", "name", "active", "isArchived", "activeVersionId", "updatedAt")}
            nodes, edges = row["nodes"], row["connections"]
            if row["activeVersionId"]:
                history = connection.execute(
                    "SELECT nodes, connections FROM workflow_history WHERE versionId = ?",
                    (row["activeVersionId"],),
                ).fetchone()
                workflow["published_version_found"] = history is not None
                if history:
                    nodes, edges = history["nodes"], history["connections"]
            workflow["nodes"] = normalize_nodes(json.loads(nodes or "[]"))
            workflow["connections"] = json.loads(edges or "{}")
            workflow["timezone"] = json.loads(row["settings"] or "{}").get("timezone", "Europe/Warsaw")
            workflows.append(workflow)
        cutoff = datetime.fromtimestamp(since, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        executions = [dict(row) for row in connection.execute(
            "SELECT id, workflowId, mode, status, startedAt, stoppedAt, waitTill FROM execution_entity "
            "WHERE startedAt >= ? OR stoppedAt >= ? OR status IN ('running', 'waiting', 'new')", (cutoff, cutoff),
        )]
        credentials = [row[0] for row in connection.execute("SELECT id FROM credentials_entity")]
        statistics = [dict(row) for row in connection.execute(
            "SELECT workflowId, name, count, latestEvent FROM workflow_statistics "
            "WHERE name IN ('production_success', 'production_error')",
        )]
        triggers = [dict(row) for row in connection.execute(
            "SELECT workflowId, nodeId, versionId, status, updatedAt FROM workflow_publication_trigger_status",
        )]
        return {"workflows": workflows, "executions": executions, "credential_ids": credentials,
                "statistics": statistics, "triggers": triggers}
    finally:
        connection.close()


def snapshot(since, directory=DATA_DIR):
    result = {"collected_at": datetime.now(timezone.utc).timestamp(), "problems": []}
    for name, url in [("n8n", "http://127.0.0.1:5678/healthz/readiness"),
                      ("helper", "http://127.0.0.1:8765/health")]:
        if not health(url):
            result["problems"].append({"key": f"health/{name}", "title": f"Usługa {name} nie odpowiada",
                                       "detail": f"Nieudany test {url}."})
    try:
        completed = subprocess.run(
            ["docker", "exec", "n8n", "node", "-p",
             "require('/usr/local/lib/node_modules/n8n/package.json').version"],
            capture_output=True, text=True, timeout=15, check=True,
        )
        result["version"] = completed.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        result["problems"].append({"key": "version/runtime", "title": "Nie można odczytać wersji n8n",
                                   "detail": "Kontener Docker n8n nie udostępnił informacji o wersji."})
    try:
        result.update(read_database(Path(directory) / "database.sqlite", since))
    except (OSError, ValueError, sqlite3.Error) as exc:
        result["problems"].append({"key": "telemetry/database", "title": "Nie można odczytać metadanych n8n",
                                   "detail": f"{type(exc).__name__}: {exc}"})
    try:
        result.update(read_events(directory, since))
    except OSError as exc:
        result["problems"].append({"key": "telemetry/logs", "title": "Nie można odczytać dziennika zdarzeń n8n",
                                   "detail": f"{type(exc).__name__}: {exc}"})
    disk = shutil.disk_usage(directory)
    result["disk_used_percent"] = round(100 * disk.used / disk.total, 1)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", type=float, required=True)
    args = parser.parse_args()
    print(json.dumps(snapshot(args.since), ensure_ascii=True))
