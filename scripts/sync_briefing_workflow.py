import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "BriefingParlamentarnyMNiSW.json"
NORMALIZE_PATH = ROOT / "scripts" / "briefing_normalize_research.js"
FILTER_PATH = ROOT / "scripts" / "briefing_relevance_filter.js"
BUILD_PATH = ROOT / "scripts" / "briefing_build_newsletter.js"
PREPARE_SUMMARIES_PATH = ROOT / "scripts" / "briefing_prepare_summaries.js"
APPLY_SUMMARIES_PATH = ROOT / "scripts" / "briefing_apply_summaries.js"


def connection(node: str):
    return {"main": [[{"node": node, "type": "main", "index": 0}]]}


workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
by_name = {node["name"]: node for node in workflow["nodes"]}

research = by_name.get("Sejm API: Interpelacje") or by_name["Research API: Sejm i ELI"]
research["name"] = "Research API: Sejm i ELI"
research["parameters"] = {
    "url": "={{ 'http://127.0.0.1:8765/sejm-research?dateFrom=' + encodeURIComponent($('Init: daty i stan').first().json.dateFrom) + '&dateTo=' + encodeURIComponent($('Init: daty i stan').first().json.dateTo) + '&scope=mnisw&term=10&maxEnrich=8' }}",
    "options": {
        "response": {"response": {"responseFormat": "json"}},
        "timeout": 180000,
    },
}
research["position"] = [460, 250]
research["continueOnFail"] = True

normalize = by_name.get("Normalize: Interpelacje") or by_name["Normalize: Research"]
normalize["name"] = "Normalize: Research"
normalize["parameters"] = {
    "mode": "runOnceForAllItems",
    "jsCode": NORMALIZE_PATH.read_text(encoding="utf-8"),
}
normalize["position"] = [700, 250]

filter_node = by_name["Filtruj i scoruj (MNiSW)"]
filter_node["parameters"]["jsCode"] = FILTER_PATH.read_text(encoding="utf-8")
filter_node["position"] = [940, 250]

prepare_summaries = {
    "id": "briefing-prepare-summaries",
    "name": "Przygotuj materiał do syntezy",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [1180, 40],
    "parameters": {
        "mode": "runOnceForAllItems",
        "jsCode": PREPARE_SUMMARIES_PATH.read_text(encoding="utf-8"),
    },
}

summary_schema = {
    "type": "object",
    "properties": {
        "summaries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "questionSummary": {"type": "string"},
                    "answerSummary": {"type": "string"},
                },
                "required": ["id", "questionSummary", "answerSummary"],
            },
        }
    },
    "required": ["summaries"],
}

ai_summaries = {
    "id": "briefing-ai-summaries",
    "name": "AI: Podsumuj pytania i odpowiedzi",
    "type": "@n8n/n8n-nodes-langchain.informationExtractor",
    "typeVersion": 1.2,
    "position": [1420, 40],
    "parameters": {
        "text": "={{ $json.summaryInput || '{\"questions\":[]}' }}",
        "schemaType": "manual",
        "inputSchema": json.dumps(summary_schema, ensure_ascii=False),
        "options": {
            "systemPromptTemplate": (
                "Jesteś analitykiem parlamentarnym. Zwróć wyłącznie JSON zgodny ze schematem i przygotuj po jednym wpisie dla każdego id. "
                "Pisz po polsku, konkretnie i wyłącznie na podstawie przekazanego materiału. questionSummary ma mieć 2-3 zdania: wyjaśnij problem lub kontekst oraz czego dokładnie chcą dowiedzieć się posłowie. "
                "Nie kopiuj nagłówków, metadanych, numeru interpelacji ani formuł grzecznościowych. Nie streszczaj samym tytułem. "
                "answerSummary ma mieć 2-4 zdania i wskazywać, kto odpowiedział, jakie stanowisko zajął oraz jakie podał decyzje, terminy, liczby lub dalsze działania. "
                "Jeśli replyStatus nie jest 'answered', nie twórz odpowiedzi merytorycznej: zwięźle opisz rzeczywisty status. "
                "Nie dopowiadaj faktów, których nie ma w źródle. Gdy materiał jest niepełny, powiedz to wprost."
            )
        },
    },
    "continueOnFail": True,
}

groq_model = {
    "id": "briefing-groq-model",
    "name": "Groq Chat Model",
    "type": "@n8n/n8n-nodes-langchain.lmChatGroq",
    "typeVersion": 1,
    "position": [1420, -150],
    "parameters": {
        "model": "llama-3.3-70b-versatile",
        "options": {"temperature": 0.2, "maxTokensToSample": 3000},
    },
    "credentials": {
        "groqApi": {"id": "j4jwLe5JW6aKUJ0O", "name": "Groq account"}
    },
}

merge_summaries = {
    "id": "briefing-merge-summaries",
    "name": "Scal briefing i podsumowania",
    "type": "n8n-nodes-base.merge",
    "typeVersion": 3.2,
    "position": [1660, 250],
    "parameters": {"mode": "combine", "combineBy": "combineByPosition", "options": {}},
}

apply_summaries = {
    "id": "briefing-apply-summaries",
    "name": "Zastosuj podsumowania",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [1900, 250],
    "parameters": {
        "mode": "runOnceForAllItems",
        "jsCode": APPLY_SUMMARIES_PATH.read_text(encoding="utf-8"),
    },
}

build = by_name["Buduj HTML newsletter"]
build["parameters"]["jsCode"] = BUILD_PATH.read_text(encoding="utf-8")
build["position"] = [2140, 250]

send = by_name["Resend: wyślij email"]
send["position"] = [2380, 250]
send["credentials"] = {
    "httpHeaderAuth": {
        "id": "8pIewAUkFsshffYZ",
        "name": "Header Auth account",
    }
}

keep_names = {
    "When clicking Test workflow",
    "Poniedziałek 07:00",
    "Init: daty i stan",
    "Filtruj i scoruj (MNiSW)",
    "Buduj HTML newsletter",
    "Resend: wyślij email",
}
workflow["nodes"] = [
    node
    for node in workflow["nodes"]
    if node["name"] in keep_names
]
workflow["nodes"].extend([research, normalize])
workflow["nodes"].extend([
    prepare_summaries,
    ai_summaries,
    groq_model,
    merge_summaries,
    apply_summaries,
])
workflow["nodes"].sort(key=lambda node: (node["position"][0], node["position"][1], node["name"]))

workflow["connections"] = {
    "When clicking Test workflow": connection("Init: daty i stan"),
    "Poniedziałek 07:00": connection("Init: daty i stan"),
    "Init: daty i stan": connection("Research API: Sejm i ELI"),
    "Research API: Sejm i ELI": connection("Normalize: Research"),
    "Normalize: Research": connection("Filtruj i scoruj (MNiSW)"),
    "Filtruj i scoruj (MNiSW)": {
        "main": [[
            {"node": "Przygotuj materiał do syntezy", "type": "main", "index": 0},
            {"node": "Scal briefing i podsumowania", "type": "main", "index": 0},
        ]]
    },
    "Przygotuj materiał do syntezy": connection("AI: Podsumuj pytania i odpowiedzi"),
    "AI: Podsumuj pytania i odpowiedzi": {
        "main": [[{"node": "Scal briefing i podsumowania", "type": "main", "index": 1}]]
    },
    "Groq Chat Model": {
        "ai_languageModel": [[{"node": "AI: Podsumuj pytania i odpowiedzi", "type": "ai_languageModel", "index": 0}]]
    },
    "Scal briefing i podsumowania": connection("Zastosuj podsumowania"),
    "Zastosuj podsumowania": connection("Buduj HTML newsletter"),
    "Buduj HTML newsletter": connection("Resend: wyślij email"),
}
workflow["id"] = "9cDqVFh4KQBYw7ic"
workflow["active"] = False
workflow["tags"] = []

WORKFLOW_PATH.write_text(
    json.dumps(workflow, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
