import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from rcl_extract_project import extract_project, fetch_bytes
from sejm_research import research_legal_sources
from twinning_monitor import extract_offer as extract_twinning_offer
from twinning_monitor import list_active_offers


HOST = os.getenv("RCL_HELPER_HOST", "127.0.0.1")
PORT = int(os.getenv("RCL_HELPER_PORT", "8765"))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.respond(200, {"ok": True})
            return

        if parsed.path == "/fetch":
            params = parse_qs(parsed.query or "")
            source_url = (params.get("url") or [""])[0].strip()
            if not source_url:
                self.respond(400, {"error": True, "message": "Missing url"})
                return

            try:
                data, _, final_url = fetch_bytes(source_url)
            except Exception as exc:  # pragma: no cover - surfaced in response
                self.respond(
                    502,
                    {
                        "error": True,
                        "message": f"Failed to fetch url: {exc}",
                        "url": source_url,
                    },
                )
                return

            html = ""
            for encoding in ("utf-8", "cp1250", "latin-1"):
                try:
                    html = data.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            if not html:
                html = data.decode("utf-8", errors="ignore")

            self.respond(200, {"html": html, "finalUrl": final_url})
            return

        if parsed.path == "/sejm-research":
            params = parse_qs(parsed.query or "")
            date_from = (params.get("dateFrom") or [""])[0].strip()
            date_to = (params.get("dateTo") or [""])[0].strip()
            scope = (params.get("scope") or ["mnisw"])[0].strip() or "mnisw"
            term = (params.get("term") or ["10"])[0].strip() or "10"
            max_enrich = (params.get("maxEnrich") or ["20"])[0].strip() or "20"
            try:
                payload = research_legal_sources(
                    date_from=date_from,
                    date_to=date_to,
                    scope=scope,
                    term=int(term),
                    max_enrich=int(max_enrich),
                )
            except (TypeError, ValueError) as exc:
                self.respond(400, {"error": True, "message": str(exc)})
                return
            except Exception as exc:  # pragma: no cover - surfaced in response
                self.respond(502, {"error": True, "message": f"Sejm research failed: {exc}"})
                return
            self.respond(200, payload)
            return

        if parsed.path == "/twinning/offers":
            params = parse_qs(parsed.query or "")
            list_url = (params.get("url") or [""])[0].strip() or None
            lookback_days = (params.get("lookbackDays") or ["180"])[0].strip() or "180"
            max_offers = (params.get("maxOffers") or ["30"])[0].strip() or "30"
            try:
                kwargs = {
                    "lookback_days": int(lookback_days),
                    "max_offers": int(max_offers),
                }
                if list_url:
                    kwargs["list_url"] = list_url
                payload = list_active_offers(**kwargs)
            except (TypeError, ValueError) as exc:
                self.respond(400, {"error": True, "message": str(exc)})
                return
            except Exception as exc:  # pragma: no cover - surfaced in response
                self.respond(502, {"error": True, "message": f"Twinning listing failed: {exc}"})
                return
            self.respond(200, payload)
            return

        if parsed.path == "/twinning/extract":
            params = parse_qs(parsed.query or "")
            offer_url = (params.get("url") or [""])[0].strip()
            if not offer_url:
                self.respond(400, {"error": True, "message": "Missing url"})
                return
            try:
                payload = extract_twinning_offer(offer_url)
            except Exception as exc:  # pragma: no cover - surfaced in response
                self.respond(502, {"error": True, "message": f"Twinning extraction failed: {exc}"})
                return
            self.respond(200, payload)
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
