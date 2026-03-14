import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from rcl_extract_project import extract_project


HOST = os.getenv("RCL_HELPER_HOST", "127.0.0.1")
PORT = int(os.getenv("RCL_HELPER_PORT", "8765"))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.respond(200, {"ok": True})
            return

        if parsed.path != "/extract":
            self.respond(404, {"error": True, "message": "Not found"})
            return

        params = parse_qs(parsed.query or "")
        project_url = (params.get("url") or [""])[0].strip()
        from_email = (params.get("fromEmail") or [""])[0].strip()
        to_email = (params.get("toEmail") or [""])[0].strip()
        days_lookback = int((params.get("daysLookback") or ["14"])[0] or "14")
        score_threshold = float((params.get("scoreThreshold") or ["0"])[0] or "0")

        if not project_url:
            self.respond(400, {"error": True, "message": "Missing url"})
            return

        payload = extract_project(
            project_url=project_url,
            from_email=from_email,
            to_email=to_email,
            days_lookback=days_lookback,
            score_threshold=score_threshold,
        )
        self.respond(200, payload)

    def log_message(self, format, *args):
        return

    def respond(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"RCL helper listening on http://{HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
