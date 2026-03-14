import json
from pathlib import Path


WORKFLOW_PATH = Path(__file__).resolve().parents[1] / "RPL.json"


def load_build_email_code() -> str:
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    for node in workflow["nodes"]:
        if node.get("name") == "Build Email If Any":
            return node["parameters"]["jsCode"]
    raise AssertionError("Build Email If Any node not found")


def test_header_copy_explains_main_section_without_internal_filter_name():
    code = load_build_email_code()
    assert (
        "Sekcja główna pokazuje projekty, które zgodnie z przyjętymi założeniami "
        "mieszczą się we właściwości Ministra Nauki i Szkolnictwa Wyższego albo "
        "wyraźnie wpływają na ten obszar."
    ) in code
    assert "filtr MNiSW" not in code


def test_empty_state_heading_uses_reader_friendly_language():
    code = load_build_email_code()
    assert (
        "Brak nowych projektów mieszczących się we właściwości "
        "Ministra Nauki i Szkolnictwa Wyższego"
    ) in code


def test_empty_state_body_explains_why_main_section_is_empty():
    code = load_build_email_code()
    assert (
        "Na stronie głównej RCL pojawiły się nowe projekty, ale żaden z nich nie "
        "mieści się w przyjętym zakresie właściwości Ministra Nauki i "
        "Szkolnictwa Wyższego albo nie wpływa na ten obszar w stopniu "
        "uzasadniającym pokazanie go w sekcji głównej."
    ) in code


def test_plain_text_fallback_matches_html_message():
    code = load_build_email_code()
    assert (
        "Brak nowych projektów mieszczących się we właściwości Ministra Nauki i "
        "Szkolnictwa Wyższego albo wyraźnie wpływających na ten obszar."
    ) in code
    assert "Najnowsze projekty w RCL" in code
