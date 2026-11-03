"""Offline end-to-end smoke: quiet healthy run, one update email, no repeat.

Mail transport and telemetry are fixtures; this script never sends email.
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import n8n_watchdog as watchdog


def main():
    config = {"container_id": 105, "from_email": "n8n-monitor@example.test", "to_emails": ["owner@example.test"]}
    snapshot = {"version": "2.40.5", "problems": [], "workflows": [], "statistics": [], "events": [], "executions": []}
    deliveries = []

    def fake_send(payload, key):
        deliveries.append({"subject": payload["subject"], "key": key})
        return "smoke-accepted"

    with tempfile.TemporaryDirectory() as directory:
        config_path, state_path = Path(directory) / "config.json", Path(directory) / "state.json"
        watchdog.write_json(config_path, config)
        with patch.object(watchdog, "collect_snapshot", return_value=snapshot), patch.object(watchdog, "send_report", fake_send):
            with patch.object(watchdog, "fetch_stable_version", return_value="2.40.5"):
                quiet = watchdog.run(config_path, state_path)
                assert quiet["mail_sent"] is False
                assert not deliveries
            with patch.object(watchdog, "fetch_stable_version", return_value="2.45.7"):
                update = watchdog.run(config_path, state_path)
                assert update["mail_sent"] is True
                repeated = watchdog.run(config_path, state_path)
                assert repeated["mail_sent"] is False
                assert len(deliveries) == 1
    problems = [
        watchdog.issue("silent/TWNMONITOR2026", "Brak oczekiwanego wykonania: MSZ Twinning",
                       "Brak potwierdzenia sukcesu harmonogramu 08:00 i 15:00. Sprawdź połączenia węzłów i historię wykonań.", "TWNMONITOR2026"),
        watchdog.issue("update/2.45.7", "Dostępna stabilna aktualizacja n8n: 2.45.7",
                       "Uruchomiona wersja: 2.40.5. Przed aktualizacją wykonaj backup i test obrazu z poprawką base path."),
    ]
    preview = watchdog.render_report(problems, config, datetime.now(timezone.utc).timestamp(), "2.40.5")
    target = Path(__file__).resolve().parents[1] / ".tmp-twinning-watchdog-report.html"
    target.write_text(preview["html"], encoding="utf-8")
    print(json.dumps({"ok": True, "healthy_mail_count": 0, "update_mail_count": len(deliveries), "preview": str(target)}))


if __name__ == "__main__":
    main()
