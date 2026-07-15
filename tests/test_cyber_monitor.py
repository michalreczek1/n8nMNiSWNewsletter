import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "CyberMonitorSejmowy.json"
PREPARE_PATH = ROOT / "scripts" / "cyber_prepare_sources.js"
FILTER_PATH = ROOT / "scripts" / "cyber_aggregate_filter.js"


def load_workflow() -> dict:
    return json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))


def node_code(name: str) -> str:
    for node in load_workflow()["nodes"]:
        if node.get("name") == name:
            return node["parameters"]["jsCode"]
    raise AssertionError(f"Node not found: {name}")


def run_node(source: str, item_sets: dict[str, list] | None = None):
    sets = item_sets or {}
    wrapper = f"""
const sets = {json.dumps(sets, ensure_ascii=False)};
const $items = (name) => sets[name] || [];
const result = (new Function('$items', {json.dumps(source)}))($items);
console.log(JSON.stringify(result));
"""
    result = subprocess.run(
        ["node", "-e", wrapper],
        capture_output=True,
        text=True,
        check=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


def test_workflow_nodes_match_checked_in_sources():
    assert node_code("Przygotuj URL-e zrodel") == PREPARE_PATH.read_text(encoding="utf-8")
    assert node_code("Agreguj i filtruj dane") == FILTER_PATH.read_text(encoding="utf-8")


def test_prepare_sources_paginates_sejm_and_uses_eli_search_by_publication_date():
    items = run_node(PREPARE_PATH.read_text(encoding="utf-8"))
    payloads = [item["json"] for item in items]
    interpellations = [item for item in payloads if item["kind"] == "interpellations"]
    questions = [item for item in payloads if item["kind"] == "writtenQuestions"]
    eli = [item for item in payloads if item["kind"] == "eli"]

    assert len(interpellations) == 11
    assert len(questions) == 6
    assert any("offset=100" in item["url"] for item in interpellations)
    assert any("offset=500" in item["url"] for item in questions)
    assert eli
    assert all("/eli/acts/search?" in item["url"] for item in eli)
    assert all("pubDateFrom=" in item["url"] and "pubDateTo=" in item["url"] for item in eli)
    assert all("sortBy=promulgation" in item["url"] for item in eli)
    assert not any("/eli/acts/DU/" in item["url"] or "/eli/acts/MP/" in item["url"] for item in eli)


def test_filter_rejects_old_changed_act_and_recipient_only_question():
    ctx = {"dateFrom": "2026-07-08", "dateTo": "2026-07-15"}
    source_items = [
        {"json": {"source": "interpellations-0", "kind": "interpellations", "dateContext": ctx}},
        {"json": {"source": "interpellations-100", "kind": "interpellations", "dateContext": ctx}},
        {"json": {"source": "writtenQuestions-0", "kind": "writtenQuestions", "dateContext": ctx}},
        {"json": {"source": "eli-du-0", "kind": "eli", "dateContext": ctx}},
    ]
    relevant_interpellation = {
        "num": 901,
        "title": "Bezpieczeństwo systemów teleinformatycznych administracji",
        "lastModified": "2026-07-12T09:00:00",
        "links": [],
    }
    responses = [
        {"json": [
            relevant_interpellation,
            {
                "num": 904,
                "title": "Zatrudnianie osób z podwójnym obywatelstwem w Ministerstwie Zdrowia",
                "lastModified": "2026-07-12T12:00:00",
                "links": [],
            },
        ], "pairedItem": {"item": 0}},
        {"json": [relevant_interpellation], "pairedItem": {"item": 1}},
        {"json": [
            {
                "num": 902,
                "title": "Wynagrodzenia nauczycieli wychowania fizycznego",
                "to": ["minister cyfryzacji"],
                "lastModified": "2026-07-13T08:00:00",
                "links": [],
            },
            {
                "num": 903,
                "title": "Odporność na incydenty cyberbezpieczeństwa w szkołach",
                "lastModified": "2026-07-13T10:00:00",
                "links": [],
            },
            {
                "num": 905,
                "title": "Zmiana ustawy o ochronie zdrowia przed następstwami używania tytoniu",
                "lastModified": "2026-07-13T11:00:00",
                "links": [],
            },
        ], "pairedItem": {"item": 2}},
        {"json": {"items": [
            {
                "ELI": "DU/2025/999",
                "publisher": "DU",
                "title": "Rozporządzenie w sprawie systemu teleinformatycznego",
                "promulgation": "2025-12-01",
                "changeDate": "2026-07-14",
            },
            {
                "ELI": "DU/2026/777",
                "publisher": "DU",
                "title": "Ustawa o krajowym systemie cyberbezpieczeństwa",
                "promulgation": "2026-07-14",
            },
        ]}, "pairedItem": {"item": 3}},
    ]
    result = run_node(FILTER_PATH.read_text(encoding="utf-8"), {
        "Przygotuj URL-e zrodel": source_items,
        "Pobierz zrodla": responses,
        "Przygotuj URL-e glosowan": [],
        "Pobierz szczegoly glosowan": [],
    })[0]["json"]

    assert [item["number"] for item in result["sections"]["interpellations"]] == [901]
    assert [item["number"] for item in result["sections"]["writtenQuestions"]] == [903]
    assert [item["number"] for item in result["sections"]["acts"]] == ["DU/2026/777"]
    assert result["sections"]["acts"][0]["date"] == "2026-07-14"


def test_sources_compile_in_n8n_function_wrapper():
    for path in (PREPARE_PATH, FILTER_PATH):
        source = path.read_text(encoding="utf-8")
        subprocess.run(
            ["node", "-e", f"new Function({json.dumps(source)}); console.log('ok')"],
            capture_output=True,
            text=True,
            check=True,
        )
