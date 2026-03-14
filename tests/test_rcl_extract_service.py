import importlib.util
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen


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
