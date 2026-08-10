import importlib.util
import json
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
SERVICE_PATH = SCRIPTS_DIR / "rcl_extract_service.py"


def load_service_module(module_name: str):
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        spec = importlib.util.spec_from_file_location(module_name, SERVICE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


def test_health_endpoint_responds_ok(monkeypatch):
    monkeypatch.setenv("RCL_HELPER_HOST", "127.0.0.1")
    monkeypatch.setenv("RCL_HELPER_PORT", "8767")
    service = load_service_module("rcl_extract_service_test")

    server = ThreadingHTTPServer((service.HOST, service.PORT), service.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)

    try:
        body = urlopen(f"http://{service.HOST}:{service.PORT}/health", timeout=5).read()
        assert body.decode("utf-8") == '{"ok": true}'
    finally:
        server.shutdown()
        server.server_close()


def test_fetch_endpoint_returns_html(monkeypatch):
    monkeypatch.setenv("RCL_HELPER_HOST", "127.0.0.1")
    monkeypatch.setenv("RCL_HELPER_PORT", "8768")
    service = load_service_module("rcl_extract_service_fetch_test")

    def fake_fetch_bytes(url):
        assert url == "https://example.test/"
        return b"<html>ok</html>", "text/html", url

    monkeypatch.setattr(service, "fetch_bytes", fake_fetch_bytes)

    server = ThreadingHTTPServer((service.HOST, service.PORT), service.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)

    try:
        body = urlopen(
            f"http://{service.HOST}:{service.PORT}/fetch?url=https://example.test/",
            timeout=5,
        ).read()
        assert body.decode("utf-8") == '{"html": "<html>ok</html>", "finalUrl": "https://example.test/"}'
    finally:
        server.shutdown()
        server.server_close()


def test_sejm_research_endpoint_returns_structured_payload(monkeypatch):
    monkeypatch.setenv("RCL_HELPER_HOST", "127.0.0.1")
    monkeypatch.setenv("RCL_HELPER_PORT", "8769")
    service = load_service_module("rcl_extract_service_sejm_test")

    def fake_research(**kwargs):
        assert kwargs == {
            "date_from": "2026-07-06",
            "date_to": "2026-07-13",
            "scope": "mnisw",
            "term": 10,
            "max_enrich": 12,
        }
        return {
            "status": "ok",
            "dateFrom": kwargs["date_from"],
            "dateTo": kwargs["date_to"],
            "interpellations": [],
            "writtenQuestions": [],
            "prints": [],
            "eliActs": [],
            "sources": {},
            "sourceErrors": [],
        }

    monkeypatch.setattr(service, "research_legal_sources", fake_research)
    server = ThreadingHTTPServer((service.HOST, service.PORT), service.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)

    try:
        body = urlopen(
            f"http://{service.HOST}:{service.PORT}/sejm-research?dateFrom=2026-07-06&dateTo=2026-07-13&scope=mnisw&term=10&maxEnrich=12",
            timeout=5,
        ).read()
        assert '"status": "ok"' in body.decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()


def test_twinning_offers_endpoint_returns_structured_payload(monkeypatch):
    monkeypatch.setenv("RCL_HELPER_HOST", "127.0.0.1")
    monkeypatch.setenv("RCL_HELPER_PORT", "8770")
    service = load_service_module("rcl_extract_service_twinning_test")

    def fake_list_active_offers(**kwargs):
        assert kwargs == {"lookback_days": 180, "max_offers": 30}
        return {"activeOffers": [{"offerId": "TEST-1"}], "errors": []}

    monkeypatch.setattr(service, "list_active_offers", fake_list_active_offers)
    server = ThreadingHTTPServer((service.HOST, service.PORT), service.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)

    try:
        body = urlopen(f"http://{service.HOST}:{service.PORT}/twinning/offers", timeout=5).read()
        assert '"offerId": "TEST-1"' in body.decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()


def test_twinning_digest_queue_and_ack_endpoints(monkeypatch, tmp_path):
    monkeypatch.setenv("RCL_HELPER_HOST", "127.0.0.1")
    monkeypatch.setenv("RCL_HELPER_PORT", "8771")
    monkeypatch.setenv("TWINNING_STATE_PATH", str(tmp_path / "state.json"))
    service = load_service_module("rcl_extract_service_twinning_digest_test")
    server = ThreadingHTTPServer((service.HOST, service.PORT), service.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)

    try:
        item = {
            "offerId": "TEST-DIGEST",
            "contentHash": "hash-digest",
            "title": "Outside profile",
            "country": "Exampleland",
            "area": "Rolnictwo",
            "url": "https://example.test/digest",
            "fitBand": "no_fit",
        }
        request = Request(
            f"http://{service.HOST}:{service.PORT}/twinning/queue-digest",
            data=json.dumps(item).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        queued = json.loads(urlopen(request, timeout=5).read())
        assert queued == {"queued": True, "offerId": "TEST-DIGEST", "status": "digest_pending"}

        digest = json.loads(
            urlopen(f"http://{service.HOST}:{service.PORT}/twinning/digest", timeout=5).read()
        )
        assert digest["pendingOffers"][0]["offerId"] == "TEST-DIGEST"

        ack_request = Request(
            f"http://{service.HOST}:{service.PORT}/twinning/digest-ack",
            data=json.dumps({"offerIds": ["TEST-DIGEST"], "recipients": ["one@example.test"], "resendId": "r-1"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        acknowledged = json.loads(urlopen(ack_request, timeout=5).read())
        assert acknowledged == {"acknowledged": True, "count": 1}
        digest_after = json.loads(
            urlopen(f"http://{service.HOST}:{service.PORT}/twinning/digest", timeout=5).read()
        )
        assert digest_after == {"pendingOffers": []}
    finally:
        server.shutdown()
        server.server_close()
