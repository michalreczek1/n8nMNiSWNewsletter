import importlib.util
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
MODULE_PATH = SCRIPTS_DIR / "sejm_research.py"


def load_module(name="sejm_research_test"):
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


def test_paginated_array_reads_every_page(monkeypatch):
    module = load_module("sejm_research_paging")
    offsets = []

    def fake_fetch_json(url):
        query = parse_qs(urlparse(url).query)
        offset = int(query["offset"][0])
        offsets.append(offset)
        if offset == 0:
            return [{"num": value} for value in range(100)]
        if offset == 100:
            return [{"num": value} for value in range(100, 135)]
        return []

    monkeypatch.setattr(module, "fetch_json", fake_fetch_json)
    items = module.fetch_paginated_array("https://api.example/items", {"sort_by": "-num"})
    assert len(items) == 135
    assert offsets == [0, 100]


def test_eli_research_uses_publication_dates_and_supported_parameter_names(monkeypatch):
    module = load_module("sejm_research_eli")
    captured = {}

    def fake_fetch(params, max_pages=module.MAX_PAGES):
        captured.update(params)
        return ([{
            "ELI": "DU/2026/123",
            "title": "Rozporządzenie w sprawie dróg",
            "promulgation": "2026-07-10",
            "textPDF": True,
            "keywords": ["drogi"],
        }], 1)

    monkeypatch.setattr(module, "fetch_paginated_eli", fake_fetch)
    items, stats = module.research_eli("2026-07-06", "2026-07-13", "mnisw", 10)
    assert len(items) == 1
    assert stats == {"checked": 1, "withinWindow": 1, "enriched": 0}
    assert captured["pubDateFrom"] == "2026-07-06"
    assert captured["pubDateTo"] == "2026-07-13"
    assert captured["sortBy"] == "promulgation"
    assert captured["sortDir"] == "desc"
    assert "sort_by" not in captured


def test_question_research_merges_updates_and_enriches_official_body(monkeypatch):
    module = load_module("sejm_research_questions")
    record = {
        "num": 42,
        "title": "Interpelacja w sprawie finansowania badań naukowych na uczelniach",
        "receiptDate": "2026-07-07",
        "sentDate": "2026-07-08",
        "lastModified": "2026-07-10T10:00:00",
        "recipientDetails": [{"name": "minister nauki"}],
        "links": [
            {"rel": "body", "href": "https://api.example/interpellations/42/body"},
            {"rel": "web-description", "href": "https://sejm.example/42"},
        ],
        "replies": [{
            "lastModified": "2026-07-10T10:00:00",
            "links": [{"rel": "body", "href": "https://api.example/interpellations/42/reply/body"}],
        }],
    }

    def fake_pages(base_url, params, max_pages=module.MAX_PAGES):
        return [record]

    def fake_text(url):
        if "/reply/" in url:
            return "Minister wyjaśnia zasady finansowania badań naukowych na uczelniach publicznych."
        return "Pytanie dotyczy finansowania badań naukowych oraz środków dla uczelni publicznych."

    monkeypatch.setattr(module, "fetch_paginated_array", fake_pages)
    monkeypatch.setattr(module, "fetch_text", fake_text)
    items, stats = module.research_questions(
        "interpellations", "2026-07-06", "2026-07-13", "mnisw", 10, 20
    )
    assert len(items) == 1
    assert items[0]["url"] == "https://sejm.example/42"
    assert items[0]["researchQuality"] == "full-text"
    assert items[0]["summary"]
    assert items[0]["replySummary"]
    assert "science-policy" in items[0]["researchLabels"]
    assert stats == {"checked": 1, "withinWindow": 1, "enriched": 1}


def test_question_metadata_path_does_not_fetch_nested_reply(monkeypatch):
    module = load_module("sejm_research_question_limit")
    record = {
        "num": 43,
        "title": "Interpelacja w sprawie uczelni publicznej",
        "recipientDetails": [{"name": "minister nauki"}],
        "links": [{"rel": "body", "href": "https://api.example/body"}],
        "replies": [{"links": [{"rel": "body", "href": "https://api.example/reply/body"}]}],
    }
    monkeypatch.setattr(
        module,
        "fetch_text",
        lambda url: (_ for _ in ()).throw(AssertionError(f"unexpected fetch: {url}")),
    )
    item = module._enrich_question(record, "interpellations", "mnisw", fetch_content=False)
    assert item["bodyText"] == ""
    assert item["replyText"] == ""
    assert item["researchQuality"] == "metadata"


def test_print_research_filters_to_week_before_enrichment(monkeypatch):
    module = load_module("sejm_research_prints")
    raw = [
        {
            "number": "100",
            "title": "Projekt ustawy Prawo o szkolnictwie wyższym i nauce",
            "deliveryDate": "2026-07-08",
            "changeDate": "2026-07-09T08:00:00",
        },
        {
            "number": "1",
            "title": "Historyczny druk o uczelniach",
            "deliveryDate": "2024-01-01",
            "changeDate": "2024-01-01T08:00:00",
        },
    ]
    monkeypatch.setattr(module, "fetch_json", lambda url: raw)
    monkeypatch.setattr(
        module,
        "_enrich_print",
        lambda record, scope, term: {**record, "researchQuality": "details", "url": "https://sejm.example/100"},
    )
    items, stats = module.research_prints("2026-07-06", "2026-07-13", "mnisw", 10, 20)
    assert [item["number"] for item in items] == ["100"]
    assert stats == {"checked": 2, "withinWindow": 1, "enriched": 1}


def test_print_attachment_ignores_signature_files():
    module = load_module("sejm_research_attachments")
    selected = module.choose_print_attachment(
        ["projekt.pdf", "uzasadnienie.docx", "uzasadnienie.docx.xades"]
    )
    assert selected == "uzasadnienie.docx"


def test_research_returns_partial_status_when_one_source_fails(monkeypatch):
    module = load_module("sejm_research_partial")
    monkeypatch.setattr(module, "research_questions", lambda *args, **kwargs: ([], {"checked": 0, "withinWindow": 0, "enriched": 0}))
    monkeypatch.setattr(module, "research_prints", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("prints unavailable")))
    monkeypatch.setattr(module, "research_eli", lambda *args, **kwargs: ([], {"checked": 0, "withinWindow": 0, "enriched": 0}))
    result = module.research_legal_sources("2026-07-06", "2026-07-13")
    assert result["status"] == "partial_error"
    assert result["sourceErrors"] == [{"source": "prints", "message": "prints unavailable"}]
    assert result["sources"]["prints"]["error"]["message"] == "prints unavailable"
