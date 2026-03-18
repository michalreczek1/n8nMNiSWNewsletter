import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


INFO_PATH = Path(sys.argv[1])
PORT = int(sys.argv[2])


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/bootstrap-info", "/healthz"):
            self.send_response(404)
            self.end_headers()
            return

        payload = {}
        if INFO_PATH.exists():
            try:
                payload = json.loads(INFO_PATH.read_text(encoding="utf-8"))
            except Exception as exc:
                payload = {"status": "error", "message": str(exc)}
        else:
            payload = {"status": "missing"}

        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
