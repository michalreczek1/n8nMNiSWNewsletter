import json
from pathlib import Path


WORKFLOW_PATH = Path(__file__).resolve().parents[1] / "RPL.json"
RECENT_PROJECTS_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rpl_extract_recent_projects.js"
FINALIZE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rpl_finalize_project_analysis.js"


def load_workflow() -> dict:
    return json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))


def load_node_code(node_name: str) -> str:
    workflow = load_workflow()
    for node in workflow["nodes"]:
        if node.get("name") == node_name:
            return node["parameters"]["jsCode"]
    raise AssertionError(f"Node not found: {node_name}")


def test_rpl_workflow_uses_full_recent_list_source():
    workflow = load_workflow()
    config = next(node for node in workflow["nodes"] if node["name"] == "Config")
    assignments = config["parameters"]["assignments"]["assignments"]
    home_url = next(item["value"] for item in assignments if item["name"] == "homeUrl")
    assert home_url == "https://legislacja.gov.pl/lista?pSize=100"


def test_rpl_embedded_code_matches_source_files():
    assert load_node_code("Extract Recent Project URLs") == RECENT_PROJECTS_PATH.read_text(encoding="utf-8")
    assert load_node_code("Finalize Project Analysis") == FINALIZE_PATH.read_text(encoding="utf-8")


def test_recent_project_extractor_uses_full_list_and_newest_date():
    code = RECENT_PROJECTS_PATH.read_text(encoding="utf-8")
    assert "extractRowsFromFullList" in code
    assert "Lista projektów według wybranych kryteriów" in code
    assert "newestDateFromList" in code
    assert "dateKey(row.created) === newestKey" in code


def test_finalize_relevance_uses_source_evidence_not_ai_summary():
    code = FINALIZE_PATH.read_text(encoding="utf-8")
    assert "const primaryEvidenceTextForAnalysis = normalizeComparable" in code
    assert "const extendedEvidenceTextForAnalysis = normalizeComparable(payload.analysisText || '')" in code
    assert "payload.analysisText || ''" in code
    assert "highConfidenceExtendedPatterns" in code
    assert "const isRelevant = score >= threshold && hasCoreEvidence;" in code
    assert "matchedPositiveLabels" in code
    assert "positivePatterns" in code


def test_finalize_filters_boilerplate_and_binary_document_text():
    code = FINALIZE_PATH.read_text(encoding="utf-8")
    assert "looksUnreadableSourceText" in code
    assert "sanitizeFallbackSummary(payload.fallbackSummary || payload.summary)" in code
    assert "Brak czytelnego streszczenia w źródłowym dokumencie" in code
    assert "projekt dotyczy:" in code
    assert "collectPatternHits(primaryEvidenceTextForAnalysis, positivePatterns)" in code
    assert "collectPatternHits(extendedEvidenceTextForAnalysis, highConfidenceExtendedPatterns)" in code
    assert "science-institutions'].includes(pattern.label)" not in code
