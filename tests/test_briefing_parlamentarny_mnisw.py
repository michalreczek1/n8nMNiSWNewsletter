import json
import importlib.util
import re
import subprocess
import sys
from pathlib import Path


WORKFLOW_PATH = Path(__file__).resolve().parents[1] / "BriefingParlamentarnyMNiSW.json"
FILTER_SOURCE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "briefing_relevance_filter.js"
NORMALIZE_SOURCE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "briefing_normalize_research.js"
BUILD_SOURCE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "briefing_build_newsletter.js"
PREPARE_SUMMARIES_PATH = Path(__file__).resolve().parents[1] / "scripts" / "briefing_prepare_summaries.js"
COLLECT_SUMMARIES_PATH = Path(__file__).resolve().parents[1] / "scripts" / "briefing_collect_summaries.js"
APPLY_SUMMARIES_PATH = Path(__file__).resolve().parents[1] / "scripts" / "briefing_apply_summaries.js"
SMOKE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "smoke_briefing_research.py"


def load_workflow() -> dict:
    return json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))


def get_node(workflow: dict, name: str) -> dict:
    for node in workflow["nodes"]:
        if node.get("name") == name:
            return node
    raise AssertionError(f"Node not found: {name}")


def load_filter_source() -> str:
    return FILTER_SOURCE_PATH.read_text(encoding="utf-8")


def load_smoke_module():
    sys.path.insert(0, str(SMOKE_PATH.parent))
    try:
        spec = importlib.util.spec_from_file_location("smoke_briefing_research_test", SMOKE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


def keyword_boundaries(pattern: str) -> bool:
    return "\\b" in pattern or "\\s" in pattern


def recipient_hint(text: str) -> bool:
    return bool(re.search(r"\bminister(?:stwo|a|owi|em)?\s+nauki\b|\bszkolnictwa\s+wyższego\b", text, re.IGNORECASE))


PY_POLICIES = {
    "interpellations": {
        "positive": [
            ("higher-education-law", re.compile(r"\bprawo\s+o\s+szkolnictwie\s+wyższym\s+i\s+nauce\b", re.IGNORECASE), 5),
            ("higher-education", re.compile(r"\bszkolnictw\w*\s+wyższ\w*\b|\bkształceni\w*\s+wyższ\w*\b", re.IGNORECASE), 4),
            ("university", re.compile(r"\buczelni(?:a|e|om|ach|ami|i)?\b", re.IGNORECASE), 3),
            ("student-affairs", re.compile(r"\bstuden(?:t|ci|ck\w*)\b", re.IGNORECASE), 3),
            ("doctoral-affairs", re.compile(r"\bdoktoran\w*\b|\bdoktorat\w*\b", re.IGNORECASE), 3),
            ("science-policy", re.compile(r"\bbadan(?:ia|ie|iami|iom)?\s+naukow\w*\b|\bnauk\w*\s+i\s+szkolnictw\w*\s+wyższ\w*\b", re.IGNORECASE), 3),
            ("science-minister-title", re.compile(r"\bminister(?:stwo|a|owi|em)?\s+nauki\b", re.IGNORECASE), 2),
        ],
        "supporting": [
            ("science-wording", re.compile(r"\bnauk\w*\b", re.IGNORECASE), 1),
            ("academic-wording", re.compile(r"\bakademick\w*\b", re.IGNORECASE), 1),
            ("rectors", re.compile(r"\brektor(?:zy|a|ów|om|ami)?\b", re.IGNORECASE), 1),
        ],
        "negative": [
            ("labour-offices", re.compile(r"\bpowiatow\w*\s+urzęd\w*\s+pracy\b|\burzęd\w*\s+pracy\b", re.IGNORECASE), -4),
            ("unemployment", re.compile(r"\bbezrobotn\w*\b|\bbezroboci\w*\b", re.IGNORECASE), -3),
            ("social-assistance", re.compile(r"\bpomoc\w*\s+społeczn\w*\b|\bświadczeni\w*\s+społeczn\w*\b", re.IGNORECASE), -3),
            ("migration", re.compile(r"\bmigrant\w*\b|\bcudzoziemc\w*\b|\buchodźc\w*\b", re.IGNORECASE), -3),
            ("judiciary", re.compile(r"\bsędzi\w*\b|\btrybunał\w*\s+konstytucyjn\w*\b", re.IGNORECASE), -4),
            ("vocational-schooling", re.compile(r"\bszkolnictw\w*\s+branżow\w*\b|\bmłodocian\w*\s+pracownik\w*\b", re.IGNORECASE), -2),
        ],
        "accept": 4,
        "review": 2,
    },
    "prints": {
        "positive": [
            ("higher-education-law", re.compile(r"\bprawo\s+o\s+szkolnictwie\s+wyższym\s+i\s+nauce\b", re.IGNORECASE), 5),
            ("higher-education", re.compile(r"\bszkolnictw\w*\s+wyższ\w*\b|\bkształceni\w*\s+wyższ\w*\b", re.IGNORECASE), 4),
            ("university", re.compile(r"\buczelni(?:a|e|om|ach|ami|i)?\b", re.IGNORECASE), 3),
            ("student-affairs", re.compile(r"\bstuden(?:t|ci|ck\w*)\b", re.IGNORECASE), 3),
            ("doctoral-affairs", re.compile(r"\bdoktoran\w*\b|\bdoktorat\w*\b", re.IGNORECASE), 3),
            ("science-committee", re.compile(r"\bkomisj\w*\s+edukacji,\s*nauki\s+i\s+młodzieży\b", re.IGNORECASE), 2),
            ("krasp", re.compile(r"\bkonferencj\w*\s+rektor\w*\b|\bKRASP\b", re.IGNORECASE), 2),
        ],
        "supporting": [
            ("science-wording", re.compile(r"\bnauk\w*\b", re.IGNORECASE), 1),
            ("academic-wording", re.compile(r"\bakademick\w*\b", re.IGNORECASE), 1),
            ("diploma", re.compile(r"\bdyplom\w*\b", re.IGNORECASE), 1),
        ],
        "negative": [
            ("labour-offices", re.compile(r"\bpowiatow\w*\s+urzęd\w*\s+pracy\b|\burzęd\w*\s+pracy\b", re.IGNORECASE), -4),
            ("vocational-schooling", re.compile(r"\bszkolnictw\w*\s+branżow\w*\b|\bmłodocian\w*\s+pracownik\w*\b", re.IGNORECASE), -2),
        ],
        "accept": 4,
        "review": 2,
    },
    "eli": {
        "positive": [
            ("higher-education-law", re.compile(r"\bprawo\s+o\s+szkolnictwie\s+wyższym\s+i\s+nauce\b", re.IGNORECASE), 5),
            ("higher-education", re.compile(r"\bszkolnictw\w*\s+wyższ\w*\b|\bkształceni\w*\s+wyższ\w*\b", re.IGNORECASE), 4),
            ("university", re.compile(r"\buczelni(?:a|e|om|ach|ami|i)?\b", re.IGNORECASE), 3),
            ("student-affairs", re.compile(r"\bstuden(?:t|ci|ck\w*)\b", re.IGNORECASE), 3),
            ("doctoral-affairs", re.compile(r"\bdoktoran\w*\b|\bdoktorat\w*\b", re.IGNORECASE), 3),
        ],
        "supporting": [
            ("science-wording", re.compile(r"\bnauk\w*\b", re.IGNORECASE), 1),
            ("academic-wording", re.compile(r"\bakademick\w*\b", re.IGNORECASE), 1),
        ],
        "negative": [
            ("labour-offices", re.compile(r"\bpowiatow\w*\s+urzęd\w*\s+pracy\b|\burzęd\w*\s+pracy\b", re.IGNORECASE), -4),
            ("vocational-schooling", re.compile(r"\bszkolnictw\w*\s+branżow\w*\b|\bmłodocian\w*\s+pracownik\w*\b", re.IGNORECASE), -2),
        ],
        "accept": 5,
        "review": 3,
    },
}


def evaluate_fixture(policy_name: str, title: str, recipients: str = "") -> tuple[str, int]:
    policy = PY_POLICIES[policy_name]
    score = 0
    positive_labels = []
    for label, pattern, weight in policy["positive"]:
        if pattern.search(title):
            positive_labels.append(label)
            score += weight
    for _, pattern, weight in policy["supporting"]:
        if pattern.search(title):
            score += weight
    for _, pattern, weight in policy["negative"]:
        if pattern.search(title):
            score += weight
    if policy_name == "interpellations" and recipient_hint(recipients) and positive_labels:
        score += 1

    if score >= policy["accept"] and positive_labels:
        return "accept", score
    if score >= policy["review"]:
        return "review", score
    return "reject", score


def test_workflow_has_no_silent_skip_branch():
    workflow = load_workflow()
    node_names = {node["name"] for node in workflow["nodes"]}
    assert "Brak wyników (skip)" not in node_names
    assert "Czy są wyniki?" not in node_names
    assert "Buduj HTML newsletter" in node_names
    assert "Resend: wyślij email" in node_names


def test_workflow_uses_research_helper_instead_of_unsupported_api_queries():
    workflow = load_workflow()
    node_names = {node["name"] for node in workflow["nodes"]}
    assert "Research API: Sejm i ELI" in node_names
    assert "Sejm API: Druki sejmowe" not in node_names
    assert "ELI API: Dziennik Ustaw" not in node_names
    research = get_node(workflow, "Research API: Sejm i ELI")
    assert "127.0.0.1:8765/sejm-research" in research["parameters"]["url"]
    assert "dateFrom=" in research["parameters"]["url"]
    assert "dateTo=" in research["parameters"]["url"]
    assert "queryParameters" not in research["parameters"]
    assert research["parameters"]["options"]["timeout"] == 600000


def test_filter_node_returns_status_scan_stats_and_source_errors():
    workflow = load_workflow()
    code = get_node(workflow, "Filtruj i scoruj (MNiSW)")["parameters"]["jsCode"]
    assert "briefingStatus" in code
    assert "scanStats" in code
    assert "sourceErrors" in code
    assert "diagnostics" in code
    assert "'partial_error'" in code
    assert "'empty'" in code
    assert "'matches'" in code


def test_filter_node_matches_checked_in_source_file():
    workflow = load_workflow()
    code = get_node(workflow, "Filtruj i scoruj (MNiSW)")["parameters"]["jsCode"]
    assert code == load_filter_source()


def test_normalize_and_build_nodes_match_checked_in_source_files():
    workflow = load_workflow()
    normalize = get_node(workflow, "Normalize: Research")["parameters"]["jsCode"]
    build = get_node(workflow, "Buduj HTML newsletter")["parameters"]["jsCode"]
    assert normalize == NORMALIZE_SOURCE_PATH.read_text(encoding="utf-8")
    assert build == BUILD_SOURCE_PATH.read_text(encoding="utf-8")


def test_workflow_uses_grounded_ai_summaries_with_fallback_path():
    workflow = load_workflow()
    prepare = get_node(workflow, "Przygotuj materiał do syntezy")
    ai = get_node(workflow, "AI: Podsumuj pytania i odpowiedzi")
    model = get_node(workflow, "Groq Chat Model")
    collect = get_node(workflow, "Zbierz podsumowania AI")
    loop = get_node(workflow, "Podsumuj po jednej pozycji")
    wait = get_node(workflow, "Odczekaj między podsumowaniami")
    next_summary = get_node(workflow, "Następne podsumowanie")
    apply = get_node(workflow, "Zastosuj podsumowania")
    assert prepare["parameters"]["jsCode"] == PREPARE_SUMMARIES_PATH.read_text(encoding="utf-8")
    assert collect["parameters"]["jsCode"] == COLLECT_SUMMARIES_PATH.read_text(encoding="utf-8")
    assert apply["parameters"]["jsCode"] == APPLY_SUMMARIES_PATH.read_text(encoding="utf-8")
    assert ai["type"] == "@n8n/n8n-nodes-langchain.informationExtractor"
    assert ai["continueOnFail"] is True
    assert ai["retryOnFail"] is True
    assert ai["maxTries"] == 3
    assert loop["parameters"]["batchSize"] == 1
    assert wait["parameters"]["amount"] == 15
    assert "questionSummary" in ai["parameters"]["inputSchema"]
    assert "answerSummary" in ai["parameters"]["inputSchema"]
    assert model["parameters"]["model"] == "llama-3.3-70b-versatile"
    assert model["credentials"]["groqApi"]["id"] == "j4jwLe5JW6aKUJ0O"
    assert workflow["connections"]["Groq Chat Model"]["ai_languageModel"][0][0]["node"] == ai["name"]
    assert workflow["connections"][ai["name"]]["main"][0][0]["node"] == next_summary["name"]
    assert workflow["connections"][loop["name"]]["main"][1][0]["node"] == wait["name"]
    assert workflow["connections"][loop["name"]]["main"][0][0]["node"] == collect["name"]


def test_filter_node_uses_source_policies_and_explainability():
    workflow = load_workflow()
    code = get_node(workflow, "Filtruj i scoruj (MNiSW)")["parameters"]["jsCode"]
    assert "const sourcePolicies =" in code
    assert "positivePatterns" in code
    assert "supportingPatterns" in code
    assert "negativePatterns" in code
    assert "acceptThreshold" in code
    assert "reviewThreshold" in code
    assert "matchedPositiveLabels" in code
    assert "matchedNegativeLabels" in code
    assert "decisionReason" in code
    assert "sourcePolicy" in code
    assert "RECIPIENT_HINT_PATTERNS" in code
    assert "matchedTitleLabels" in code
    assert "matchedDetailLabels" in code
    assert "buildReviewDiagnostics" in code
    assert "semantic-summary-v2" in code


def test_filter_node_uses_word_boundaries_not_short_substrings():
    code = load_filter_source()
    assert "'pan '" not in code
    assert keyword_boundaries(r"\brektor(?:zy|a|ów|om|ami)?\b")
    assert keyword_boundaries(r"\bpowiatow\w*\s+urzęd\w*\s+pracy\b")
    assert "\\brektor(?:zy|a|ów|om|ami)?\\b" in code
    assert "\\burzęd\\w*\\s+pracy\\b" in code


def test_filter_source_compiles_inside_function_wrapper():
    source = load_filter_source()
    wrapped = f"new Function({source!r}); console.log('ok');"
    result = subprocess.run(
        ["node", "-e", wrapped],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "ok" in result.stdout


def test_filter_review_diagnostics_does_not_dereference_missing_evaluation():
    code = load_filter_source()
    assert "item && item.decision === 'review'" in code
    assert "item.evaluation.score" not in code


def test_filter_and_newsletter_execute_on_enriched_fixture():
    smoke = load_smoke_module()
    research = {
        "dateFrom": "2026-07-06",
        "dateTo": "2026-07-13",
        "generatedAt": "2026-07-13T05:00:00Z",
        "interpellations": [{
            "num": 42,
            "title": "Interpelacja w sprawie finansowania badań naukowych na uczelniach",
            "sentDate": "2026-07-08",
            "lastModified": "2026-07-10T10:00:00",
            "recipients": ["minister nauki"],
            "bodyText": "Pytanie dotyczy finansowania badań naukowych i dotacji dla uczelni publicznych.",
            "replyText": "",
            "replyStatus": "no-answer",
            "summary": "Pytanie dotyczy finansowania badań naukowych i dotacji dla uczelni publicznych.",
            "replySummary": "",
            "researchQuality": "full-text",
            "url": "https://sejm.example/42",
        }],
        "writtenQuestions": [],
        "prints": [],
        "eliActs": [],
        "sources": {
            "interpellations": {"checked": 1, "withinWindow": 1, "enriched": 1},
            "writtenQuestions": {"checked": 0, "withinWindow": 0, "enriched": 0},
            "prints": {"checked": 0, "withinWindow": 0, "enriched": 0},
            "eliActs": {"checked": 0, "withinWindow": 0, "enriched": 0},
        },
        "sourceErrors": [],
    }
    result = smoke.run_javascript(research, [{
        "id": "42",
        "questionSummary": "Posłowie pytają o zasady finansowania badań i podział dotacji między uczelnie publiczne. Chcą poznać planowane kwoty oraz kryteria ich przyznawania.",
        "answerSummary": "Odpowiedź nie została jeszcze opublikowana.",
    }])
    assert result["briefingStatus"] == "matches"
    assert result["stats"]["interpelacje"] == 1
    assert result["titles"]["interpelacje"][0]["quality"] == "full-text"
    assert result["mail"]["htmlLength"] > 1000
    assert "O co pyta poseł" in result["mail"]["textPreview"]
    assert "Co wynika ze źródła" not in result["mail"]["textPreview"]
    assert "Odpowiedź organu nie została jeszcze opublikowana" in result["mail"]["textPreview"]


def test_deadline_extension_is_not_presented_as_substantive_answer():
    smoke = load_smoke_module()
    research = {
        "dateFrom": "2026-07-06",
        "dateTo": "2026-07-13",
        "interpellations": [{
            "num": 17725,
            "title": "Interpelacja w sprawie minimum kadrowego na wydziałach prawa",
            "sentDate": "2026-06-23",
            "eventDate": "2026-07-10",
            "eventType": "deadline-extension",
            "recipients": ["minister nauki i szkolnictwa wyższego"],
            "bodyText": "Posłowie pytają o przywrócenie minimum kadrowego na wydziałach prawa i konsultacje z uczelniami.",
            "replyText": "",
            "replyStatus": "deadline-extension",
            "replyAuthor": "Sekretarz stanu Marek Gzik",
            "summary": "Pytanie dotyczy przywrócenia minimum kadrowego na wydziałach prawa.",
            "researchQuality": "full-text",
            "url": "https://sejm.example/17725",
        }],
        "writtenQuestions": [], "prints": [], "eliActs": [],
        "sources": {
            "interpellations": {"checked": 1, "withinWindow": 1, "enriched": 1},
            "writtenQuestions": {"checked": 0, "withinWindow": 0, "enriched": 0},
            "prints": {"checked": 0, "withinWindow": 0, "enriched": 0},
            "eliActs": {"checked": 0, "withinWindow": 0, "enriched": 0},
        },
        "sourceErrors": [],
    }
    result = smoke.run_javascript(research, [{
        "id": "17725",
        "questionSummary": "Posłowie pytają o podstawy i możliwość przywrócenia minimum kadrowego na wydziałach prawa oraz zakres konsultacji ze środowiskiem akademickim.",
        "answerSummary": "Minister poparł przywrócenie minimum kadrowego.",
    }])
    preview = result["mail"]["textPreview"]
    assert "Przedłużono termin odpowiedzi" in preview
    assert "odpowiedź merytoryczna nie została jeszcze opublikowana" in preview.lower()
    assert "Minister poparł" not in preview
    assert "Jest odpowiedź" not in preview


def test_filter_rejects_sectoral_research_institutes_outside_mnisw_scope():
    smoke = load_smoke_module()
    base = {
        "sentDate": "2026-07-09",
        "lastModified": "2026-07-10T10:00:00",
        "recipients": [],
        "researchQuality": "metadata",
        "url": "https://sejm.example/item",
    }
    research = {
        "dateFrom": "2026-07-06",
        "dateTo": "2026-07-13",
        "interpellations": [
            {**base, "num": 1, "title": "Stan infrastruktury w instytutach badawczych nadzorowanych przez ministra zdrowia"},
            {**base, "num": 2, "title": "Małopolski Wojskowy Instytut Medyczny - Państwowy Instytut Badawczy"},
            {**base, "num": 3, "title": "Powołanie członków Rady Narodowego Centrum Nauki"},
        ],
        "writtenQuestions": [],
        "prints": [],
        "eliActs": [],
        "sources": {
            "interpellations": {"checked": 3, "withinWindow": 3, "enriched": 0},
            "writtenQuestions": {"checked": 0, "withinWindow": 0, "enriched": 0},
            "prints": {"checked": 0, "withinWindow": 0, "enriched": 0},
            "eliActs": {"checked": 0, "withinWindow": 0, "enriched": 0},
        },
        "sourceErrors": [],
    }

    result = smoke.run_javascript(research)
    assert result["stats"]["interpelacje"] == 1
    assert [item["id"] for item in result["titles"]["interpelacje"]] == [3]


def test_fixture_true_positive_for_higher_education_interpellation():
    decision, score = evaluate_fixture(
        "interpellations",
        "Interpelacja w sprawie zmian w ustawie Prawo o szkolnictwie wyższym i nauce oraz stypendiów doktoranckich",
        "Minister Nauki i Szkolnictwa Wyższego",
    )
    assert decision == "accept"
    assert score >= 4


def test_fixture_rejects_labour_offices_false_positive():
    decision, score = evaluate_fixture(
        "interpellations",
        "Interpelacja w sprawie apelu Konwentu Dyrektorów Powiatowych Urzędów Pracy",
        "Minister Nauki i Szkolnictwa Wyższego",
    )
    assert decision == "reject"
    assert score < 2


def test_fixture_rejects_recipient_only_case():
    decision, score = evaluate_fixture(
        "interpellations",
        "Interpelacja w sprawie stanu dróg powiatowych i finansowania inwestycji lokalnych",
        "Minister Nauki i Szkolnictwa Wyższego",
    )
    assert decision == "reject"
    assert score < 2


def test_fixture_accepts_relevant_print():
    decision, score = evaluate_fixture(
        "prints",
        "Projekt ustawy o zmianie ustawy Prawo o szkolnictwie wyższym i nauce oraz niektórych innych ustaw",
    )
    assert decision == "accept"
    assert score >= 4


def test_fixture_rejects_vocational_schooling_print():
    decision, score = evaluate_fixture(
        "prints",
        "Rządowy projekt ustawy o szkolnictwie branżowym i refundacji wynagrodzeń młodocianych pracowników",
    )
    assert decision == "reject"
    assert score < 2


def test_fixture_accepts_relevant_eli_act():
    decision, score = evaluate_fixture(
        "eli",
        "Rozporządzenie Ministra Nauki w sprawie stypendiów dla studentów i doktorantów uczelni publicznych",
    )
    assert decision == "accept"
    assert score >= 5


def test_build_node_contains_reader_friendly_empty_and_warning_copy():
    workflow = load_workflow()
    code = get_node(workflow, "Buduj HTML newsletter")["parameters"]["jsCode"]
    assert "W badanym tygodniu briefing nie wykazał nowych pozycji" in code
    assert "mieszczących się we właściwości Ministra Nauki i Szkolnictwa Wyższego" in code
    assert "Briefing został przygotowany częściowo" in code
    assert "Mail wychodzi, żeby nie zostawiać Cię bez statusu tygodnia" in code
    assert "Zakres i jakość researchu" in code
    assert "${scanStats.interpelacjeChecked} interpelacji" in code
    assert "Co wynika ze źródła" in code
    assert "Dlaczego w briefingu" in code
    assert "Made by Michał Reczek" in code


def test_build_node_produces_plain_text_version():
    workflow = load_workflow()
    code = get_node(workflow, "Buduj HTML newsletter")["parameters"]["jsCode"]
    assert "const text =" in code
    assert "Monitor Parlamentarny - MNiSW" in code
    assert "Źródła: https://api.sejm.gov.pl/sejm" in code


def test_resend_node_sends_html_and_text_payload():
    workflow = load_workflow()
    node = get_node(workflow, "Resend: wyślij email")
    params = node["parameters"]
    assert params["jsonBody"] == "={{ ({ from: $json.fromEmail, to: [$json.toEmail], subject: $json.subject, html: $json.html, text: $json.text }) }}"


def test_schedule_stays_monday_at_0700():
    workflow = load_workflow()
    node = get_node(workflow, "Poniedziałek 07:00")
    interval = node["parameters"]["rule"]["interval"][0]
    assert interval["field"] == "weeks"
    assert interval["weeksInterval"] == 1
    assert interval["triggerAtDay"] == [1]
    assert interval["triggerAtHour"] == 7
    assert interval["triggerAtMinute"] == 0
