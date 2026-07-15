import json
import subprocess
import sys
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
PREPARE_PATH = ROOT / "scripts" / "cyber_prepare_sources.js"
FILTER_PATH = ROOT / "scripts" / "cyber_aggregate_filter.js"


def run_prepare() -> list[dict]:
    source = PREPARE_PATH.read_text(encoding="utf-8")
    script = f"const result=(new Function({json.dumps(source)}))(); process.stdout.write(JSON.stringify(result));"
    result = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, encoding="utf-8", check=True
    )
    return json.loads(result.stdout)


def fetch_sources(source_items: list[dict]) -> list[dict]:
    responses = []
    with requests.Session() as session:
        session.headers["User-Agent"] = "n8n-newsletter-smoke/1.0"
        for index, item in enumerate(source_items):
            meta = item["json"]
            try:
                response = session.get(meta["url"], timeout=45)
                if response.ok:
                    payload = response.json()
                else:
                    payload = {"statusCode": response.status_code, "message": response.text[:300]}
            except Exception as exc:  # smoke powinien pokazac czesciowy blad tak jak workflow
                payload = {"error": type(exc).__name__, "message": str(exc)}
            responses.append({"json": payload, "pairedItem": {"item": index}})
    return responses


def run_filter(source_items: list[dict], responses: list[dict]) -> dict:
    sets = {
        "Przygotuj URL-e zrodel": source_items,
        "Pobierz zrodla": responses,
        "Przygotuj URL-e glosowan": [],
        "Pobierz szczegoly glosowan": [],
    }
    script = r"""
const fs = require('fs');
const sets = JSON.parse(fs.readFileSync(0, 'utf8'));
const source = fs.readFileSync(process.argv[1], 'utf8');
const $items = (name) => sets[name] || [];
const result = (new Function('$items', source))($items);
process.stdout.write(JSON.stringify(result[0].json));
"""
    result = subprocess.run(
        ["node", "-e", script, str(FILTER_PATH)],
        input=json.dumps(sets, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(result.stdout)


def main() -> int:
    source_items = run_prepare()
    responses = fetch_sources(source_items)
    result = run_filter(source_items, responses)
    compact = {
        "dateContext": result["dateContext"],
        "stats": result["stats"],
        "errors": result["errors"],
        "titles": {
            section: [
                {"number": item.get("number"), "date": item.get("date"), "title": item.get("title"), "signals": item.get("signals")}
                for item in values
            ]
            for section, values in result["sections"].items()
        },
    }
    print(json.dumps(compact, ensure_ascii=False, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
