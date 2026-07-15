import json
from pathlib import Path


WORKFLOW_PATH = Path(__file__).resolve().parents[1] / "RPL.json"
EXTRACTOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rcl_extract_project.py"


def load_node_code(node_name: str) -> str:
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    for node in workflow["nodes"]:
        if node.get("name") == node_name:
            return node["parameters"]["jsCode"]
    raise AssertionError(f"Node not found: {node_name}")


def test_finalize_project_analysis_keeps_items_when_ai_errors():
    code = load_node_code("Finalize Project Analysis")
    assert "if (!payload || !payload.url) return { json: {} };" in code
    assert "payload.error || payload.message" in code
    assert "fallback-after-ai-error" in code


def test_extractor_summary_can_use_proponuje_sie_sentence_as_fallback():
    code = EXTRACTOR_PATH.read_text(encoding="utf-8")
    assert r'(Proponuje się[^.!?]{0,900}[.!?])' in code


def test_extractor_does_not_treat_pdf_or_zip_bytes_as_text():
    code = EXTRACTOR_PATH.read_text(encoding="utf-8")
    assert "looks_unreadable_text" in code
    assert 'lowered_url.endswith(".pdf")' in code
    assert 'lowered_url.endswith(".zip")' in code
    assert "macroenabled.12" in code
    assert 'lowered_url.endswith((".xades", ".xml", ".sig"))' in code
    assert "extract_pdf_text" in code


def test_extractor_prefers_real_document_over_xades_signature():
    code = EXTRACTOR_PATH.read_text(encoding="utf-8")
    assert 'doc["url"].lower().endswith((".xades", ".xml", ".sig"))' in code
    assert 'label in d["label"].lower()' in code


def test_document_extraction_errors_do_not_discard_project_metadata():
    code = EXTRACTOR_PATH.read_text(encoding="utf-8")
    assert "try:" in code
    assert "chosen_text, content_type, chosen_doc_url = extract_document_text(chosen_doc_url)" in code
    assert "except Exception:" in code


def test_ai_claims_are_discarded_when_source_is_missing_or_low_quality():
    code = load_node_code("Finalize Project Analysis")
    assert "hasReadableSourceEvidence" in code
    assert "aiMarkedLowQuality" in code
    assert "allowAiClaims" in code
    assert "unverified-ai-discarded" in code
    assert "source-insufficient" in code
