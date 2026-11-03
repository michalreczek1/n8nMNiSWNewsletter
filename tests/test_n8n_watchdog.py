import copy
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts import n8n_watchdog as monitor
from scripts import n8n_watchdog_probe as probe


NOW = datetime(2026, 11, 3, 14, 0, tzinfo=timezone.utc).timestamp()


def iso(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def config():
    return {"container_id": 105, "probe_path": "/probe.py", "from_email": "monitor@example.test",
            "to_emails": ["owner@example.test"], "required_workflows": {"WF": "Newsletter"},
            "schedule_grace_minutes": 15}


def healthy():
    return {"version": "2.40.5", "problems": [], "events": [], "executions": [], "credential_ids": ["mail"],
            "workflows": [{"id": "WF", "name": "Newsletter", "active": True, "isArchived": False,
                           "activeVersionId": "published", "published_version_found": True,
                           "updatedAt": iso(NOW - 7 * 86400), "timezone": "Europe/Warsaw",
                           "nodes": [{"id": "schedule", "name": "08:00 i 15:00", "type": "n8n-nodes-base.scheduleTrigger",
                                      "disabled": False, "parameters": {"rule": {"interval": [{"field": "cronExpression", "expression": "0 8,15 * * *"}]}}},
                                     {"id": "work", "name": "Fetch", "type": "n8n-nodes-base.httpRequest",
                                      "disabled": False, "credential_ids": ["mail"]}],
                           "connections": {"08:00 i 15:00": {"main": [[{"node": "Fetch"}]]}}}],
            "statistics": [{"workflowId": "WF", "name": "production_success", "count": 5, "latestEvent": iso(NOW - 30)}],
            "triggers": [{"workflowId": "WF", "nodeId": "schedule", "versionId": "published", "status": "activated", "updatedAt": iso(NOW - 7 * 86400)}]}


def old_state():
    return {"monitor_started": NOW - 7 * 86400, "last_check": NOW - monitor.INTERVAL}


def keys(problems):
    return {problem["key"] for problem in problems}


def test_success_is_visible_without_saved_execution_history():
    problems, _ = monitor.evaluate(healthy(), config(), old_state(), NOW)
    assert problems == []


def test_renamed_disconnected_schedule_is_detected_even_if_workflow_says_active():
    snapshot = healthy()
    snapshot["workflows"][0]["connections"] = {"Old schedule name": {"main": [[{"node": "Fetch"}]]}}
    problems, _ = monitor.evaluate(snapshot, config(), old_state(), NOW)
    assert "graph/WF/Old schedule name" in keys(problems)
    assert "disconnected/WF/schedule" in keys(problems)


@pytest.mark.parametrize("change,expected", [
    ("inactive", "inactive/WF"), ("archived", "inactive/WF"), ("unpublished", "unpublished/WF"),
    ("disabled", "disabled-schedules/WF"), ("credential", "credentials/WF/work"),
    ("trigger", "trigger/WF/schedule"),
])
def test_configuration_failures(change, expected):
    snapshot = healthy()
    workflow = snapshot["workflows"][0]
    if change == "inactive":
        workflow["active"] = False
    elif change == "archived":
        workflow["isArchived"] = True
    elif change == "unpublished":
        workflow["published_version_found"] = False
    elif change == "disabled":
        workflow["nodes"][0]["disabled"] = True
    elif change == "credential":
        snapshot["credential_ids"] = []
    elif change == "trigger":
        snapshot["triggers"] = []
    problems, _ = monitor.evaluate(snapshot, config(), old_state(), NOW)
    assert expected in keys(problems)


def test_archived_workflows_outside_required_list_do_not_alert():
    snapshot = healthy()
    archived = copy.deepcopy(snapshot["workflows"][0])
    archived.update(id="ARCHIVED", active=False, isArchived=True)
    snapshot["workflows"].append(archived)
    assert monitor.evaluate(snapshot, config(), old_state(), NOW)[0] == []


def test_missing_scheduled_success_is_not_masked_by_manual_execution():
    snapshot = healthy()
    snapshot["statistics"] = []
    snapshot["executions"] = [{"id": 1, "workflowId": "WF", "status": "success", "mode": "manual",
                               "startedAt": iso(NOW - 60), "stoppedAt": iso(NOW - 30)}]
    problems, _ = monitor.evaluate(snapshot, config(), old_state(), NOW)
    assert "silent/WF/schedule/0" in keys(problems)


def test_cli_success_in_native_statistics_does_not_mask_a_missed_schedule():
    snapshot = healthy()
    snapshot["executions"] = [{"id": 1, "workflowId": "WF", "status": "success", "mode": "cli",
                               "startedAt": iso(NOW - 60), "stoppedAt": iso(NOW - 30)}]
    problems, _ = monitor.evaluate(snapshot, config(), old_state(), NOW)
    assert "silent/WF/schedule/0" in keys(problems)


def test_removed_required_schedule_is_detected_even_if_other_trigger_runs():
    snapshot = healthy()
    policy = {**config(), "required_schedules": {"WF": {"removed": "Digest"}}}
    problems, _ = monitor.evaluate(snapshot, policy, old_state(), NOW)
    assert "required-schedule/WF/removed" in keys(problems)


def test_scheduled_errors_alert_but_manual_and_cli_failures_do_not():
    snapshot = healthy()
    for number, mode in enumerate(["trigger", "manual", "cli"], 1):
        snapshot["executions"].append({"id": number, "workflowId": "WF", "status": "error", "mode": mode,
                                        "startedAt": iso(NOW - 60), "stoppedAt": iso(NOW - 30)})
    problems, _ = monitor.evaluate(snapshot, config(), old_state(), NOW)
    assert {key for key in keys(problems) if key.startswith("execution/")} == {"execution/1"}


def test_native_error_counter_catches_pruned_execution():
    snapshot = healthy()
    snapshot["statistics"].append({"workflowId": "WF", "name": "production_error", "count": 4,
                                    "latestEvent": iso(NOW - 3 * 86400)})
    state = {**old_state(), "error_counts": {"WF": 3}}
    problems, _ = monitor.evaluate(snapshot, config(), state, NOW)
    assert "error-counter/WF/4" in keys(problems)


def test_native_production_counters_do_not_turn_cli_diagnostics_into_false_alerts():
    snapshot = healthy()
    snapshot["statistics"].append({"workflowId": "WF", "name": "production_error", "count": 4,
                                    "latestEvent": iso(NOW - 30)})
    snapshot["executions"].append({"id": 5, "workflowId": "WF", "status": "error", "mode": "cli",
                                    "startedAt": iso(NOW - 60), "stoppedAt": iso(NOW - 30)})
    assert monitor.evaluate(snapshot, config(), old_state(), NOW)[0] == []
    state = {**old_state(), "error_counts": {"WF": 3}}
    assert monitor.evaluate(snapshot, config(), state, NOW)[0] == []


def test_schedules_on_one_workflow_are_checked_individually():
    snapshot = healthy()
    workflow = snapshot["workflows"][0]
    digest = copy.deepcopy(workflow["nodes"][0])
    digest.update(id="digest", name="Digest")
    workflow["nodes"].append(digest)
    workflow["nodes"].append({"id": "digest-work", "name": "Digest config", "type": "n8n-nodes-base.set", "disabled": False})
    workflow["connections"]["Digest"] = {"main": [[{"node": "Digest config"}]]}
    snapshot["triggers"].append({**snapshot["triggers"][0], "nodeId": "digest"})
    snapshot["events"] = [
        {"execution_id": "25", "workflow_id": "WF", "time": NOW - 35, "event": "n8n.workflow.started", "mode": "trigger"},
        {"execution_id": "25", "workflow_id": "WF", "time": NOW - 34, "event": "n8n.node.started", "node": "Fetch"},
        {"execution_id": "25", "workflow_id": "WF", "time": NOW - 30, "event": "n8n.workflow.success", "mode": "trigger"},
    ]
    problems, success = monitor.evaluate(snapshot, config(), old_state(), NOW)
    assert "silent/WF/schedule/0" not in keys(problems)
    assert "silent/WF/digest/0" in keys(problems)
    assert success["WF/schedule"] == NOW - 30


def test_multi_day_interval_and_first_run_do_not_raise_premature_alarm():
    snapshot = healthy()
    snapshot["statistics"] = []
    snapshot["workflows"][0]["nodes"][0]["parameters"]["rule"]["interval"] = [{"daysInterval": 2, "triggerAtHour": 8}]
    assert monitor.evaluate(snapshot, config(), {}, NOW)[0] == []
    assert "silent/WF/schedule/0" in keys(monitor.evaluate(snapshot, config(), old_state(), NOW)[0])


def test_cron_respects_local_timezone_weekends_and_six_fields():
    # Tuesday 15:00 Warsaw: latest weekday 12:20 is today 11:20 UTC.
    expected = datetime(2026, 11, 3, 11, 20, tzinfo=timezone.utc).timestamp()
    assert monitor.last_due("0 20 12 * * 1-5", NOW, "Europe/Warsaw") == expected
    assert monitor.last_due("20 12 * * 1-5", NOW, "Europe/Warsaw") == expected
    monday_morning = datetime(2026, 11, 2, 7, tzinfo=timezone.utc).timestamp()
    friday = datetime(2026, 10, 30, 11, 20, tzinfo=timezone.utc).timestamp()
    assert monitor.last_due("20 12 * * 1-5", monday_morning, "Europe/Warsaw") == friday


def test_waiting_execution_before_resume_is_not_stuck():
    snapshot = healthy()
    snapshot["executions"] = [{"id": 1, "workflowId": "WF", "status": "waiting", "mode": "trigger",
                               "startedAt": iso(NOW - 86400), "stoppedAt": None, "waitTill": iso(NOW + 86400)}]
    assert monitor.evaluate(snapshot, config(), old_state(), NOW)[0] == []
    snapshot["executions"][0]["waitTill"] = iso(NOW - 7200)
    assert "waiting/1" in keys(monitor.evaluate(snapshot, config(), old_state(), NOW)[0])


def test_update_is_stable_only_and_not_repeated_for_same_version():
    problems, _ = monitor.inspect(config(), old_state(), NOW, healthy(), stable="2.45.7")
    assert "update/2.45.7" in keys(problems)
    state = {**old_state(), "notified_update": "2.45.7"}
    assert monitor.inspect(config(), state, NOW, healthy(), stable="2.45.7")[0] == []
    with pytest.raises(ValueError):
        monitor.version_tuple("2.46.4-beta.1")
    assert monitor.inspect(config(), old_state(), NOW, healthy(), stable="2.39.0")[0] == []


def test_gap_beyond_retention_is_reported():
    problems, _ = monitor.inspect(config(), {**old_state(), "last_check": NOW - 49 * 3600}, NOW, healthy(), stable="2.40.5")
    assert "monitor/gap" in keys(problems)


def test_healthy_run_is_silent_and_dry_run_does_not_checkpoint(tmp_path, monkeypatch):
    config_path, state_path = tmp_path / "config.json", tmp_path / "state.json"
    monitor.write_json(config_path, config())
    monkeypatch.setattr(monitor, "collect_snapshot", lambda *args: healthy())
    monkeypatch.setattr(monitor, "fetch_stable_version", lambda: "2.40.5")
    monkeypatch.setattr(monitor, "send_report", lambda *args: pytest.fail("Healthy status must never send an email"))
    assert monitor.run(config_path, state_path, dry_run=True)["mail_sent"] is False
    assert not state_path.exists()
    assert monitor.run(config_path, state_path)["mail_sent"] is False
    assert state_path.exists()


def test_container_outage_is_reported_without_using_n8n_to_send_mail(tmp_path, monkeypatch):
    config_path, state_path = tmp_path / "config.json", tmp_path / "state.json"
    monitor.write_json(config_path, config())

    def unavailable(*args):
        raise OSError("LXC is stopped")

    sent = []
    monkeypatch.setattr(monitor, "collect_snapshot", unavailable)
    monkeypatch.setattr(monitor, "fetch_stable_version", lambda: "2.45.7")
    monkeypatch.setattr(monitor, "send_report", lambda payload, key: sent.append(payload) or "accepted")
    result = monitor.run(config_path, state_path)
    assert result["mail_sent"] is True
    assert "container/unreachable" in keys(result["issues"])
    assert "Brak dostępu do kontenera" in sent[0]["text"]


def test_resend_transport_identifies_the_client_and_confirms_acceptance(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test_only")

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return b'{"id":"accepted"}'

    def transport(request, **kwargs):
        assert request.get_header("User-agent") == "n8n-watchdog/1.0"
        assert request.get_header("Authorization") == "Bearer re_test_only"
        assert request.get_header("Idempotency-key") == "test/key"
        return Response()

    monkeypatch.setattr(monitor, "urlopen", transport)
    assert monitor.send_report({"subject": "test"}, "test/key") == "accepted"


def test_failed_delivery_retries_identical_report_without_rechecking(tmp_path, monkeypatch):
    config_path, state_path = tmp_path / "config.json", tmp_path / "state.json"
    monitor.write_json(config_path, config())
    monkeypatch.setattr(monitor, "collect_snapshot", lambda *args: healthy())
    monkeypatch.setattr(monitor, "fetch_stable_version", lambda: "2.45.7")
    attempts = []

    def send(payload, key):
        attempts.append((payload, key))
        if len(attempts) == 1:
            raise OSError("temporary delivery outage")
        return "accepted-message"

    monkeypatch.setattr(monitor, "send_report", send)
    with pytest.raises(OSError):
        monitor.run(config_path, state_path)
    assert not state_path.exists()
    monkeypatch.setattr(monitor, "collect_snapshot", lambda *args: pytest.fail("Retry must use the saved outbox"))
    assert monitor.run(config_path, state_path)["retried_delivery"] is True
    assert attempts[0] == attempts[1]
    assert monitor.read_json(state_path)["notified_update"] == "2.45.7"
    assert not state_path.with_suffix(".outbox.json").exists()


def test_already_checkpointed_outbox_is_removed_without_second_send(tmp_path, monkeypatch):
    config_path, state_path = tmp_path / "config.json", tmp_path / "state.json"
    monitor.write_json(config_path, config())
    monitor.write_json(state_path, {"last_delivery": {"key": "already-accepted"}})
    monitor.write_json(state_path.with_suffix(".outbox.json"), {"key": "already-accepted", "issues": ["update/2.45.7"]})
    monkeypatch.setattr(monitor, "send_report", lambda *args: pytest.fail("Duplicate send"))
    monitor.run(config_path, state_path)
    assert not state_path.with_suffix(".outbox.json").exists()


def test_probe_omits_payloads_and_ignores_partial_final_log_line(tmp_path):
    log = tmp_path / "n8nEventLog.log"
    log.write_text(json.dumps({"ts": iso(NOW), "eventName": "n8n.node.started", "payload": {
        "workflowId": "WF", "executionId": "2", "nodeName": "Fetch", "secret": "never-export-this",
    }}) + '\n{"incomplete"', encoding="utf-8")
    result = probe.read_events(tmp_path, NOW - 60)
    assert len(result["events"]) == 1
    assert "never-export-this" not in json.dumps(result)
    assert result["malformed_lines"] == 0
    assert probe.stamp("2026-11-03T09:00:00-05:00") == NOW


def test_probe_reads_published_graph_and_native_statistics_without_credentials(tmp_path):
    path = tmp_path / "database.sqlite"
    connection = sqlite3.connect(path)
    connection.executescript('''
        CREATE TABLE workflow_entity(id, name, active, isArchived, activeVersionId, updatedAt, nodes, connections, settings);
        CREATE TABLE workflow_history(versionId, nodes, connections);
        CREATE TABLE execution_entity(id, workflowId, mode, status, startedAt, stoppedAt, waitTill);
        CREATE TABLE credentials_entity(id, data);
        CREATE TABLE workflow_statistics(workflowId, name, count, latestEvent);
        CREATE TABLE workflow_publication_trigger_status(workflowId, nodeId, versionId, status, updatedAt);
    ''')
    published = [{"id": "published-node", "name": "Published", "type": "n8n-nodes-base.code", "parameters": {"jsCode": "sensitive code"}}]
    connection.execute("INSERT INTO workflow_entity VALUES(?,?,?,?,?,?,?,?,?)",
                       ("WF", "Newsletter", 1, 0, "V", iso(NOW), "[]", "{}", "{}"))
    connection.execute("INSERT INTO workflow_history VALUES(?,?,?)", ("V", json.dumps(published), "{}"))
    connection.execute("INSERT INTO credentials_entity VALUES(?,?)", ("mail", "encrypted-secret"))
    connection.execute("INSERT INTO workflow_statistics VALUES(?,?,?,?)", ("WF", "production_success", 12, iso(NOW)))
    connection.commit()
    connection.close()
    snapshot = probe.read_database(path, NOW - 86400)
    assert snapshot["workflows"][0]["nodes"][0]["name"] == "Published"
    assert snapshot["statistics"][0]["count"] == 12
    assert "sensitive code" not in json.dumps(snapshot)
    assert "encrypted-secret" not in json.dumps(snapshot)


def test_report_escapes_untrusted_workflow_details():
    result = monitor.render_report([monitor.issue("test", "<script>bad</script>", "<b>injected</b>", "WF")], config(), NOW)
    assert "<script>" not in result["html"]
    assert "&lt;script&gt;" in result["html"]


def test_systemd_timer_runs_full_control_every_47_hours():
    root = Path(__file__).resolve().parents[1]
    timer = (root / "ops/n8n-watchdog.timer").read_text(encoding="utf-8")
    assert "OnUnitInactiveSec=47h" in timer
    assert "OnBootSec=" in timer
    assert not list((root / "ops").glob("*collector*"))


@pytest.mark.parametrize("value", ["re_test_only", "Bearer re_test_only", "bearer re_test_only"])
def test_bootstrap_accepts_existing_n8n_sending_credential_formats(value):
    assert monitor.extract_resend_key({"name": "Authorization", "value": value}) == "re_test_only"
