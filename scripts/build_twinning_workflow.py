import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_script(name: str) -> str:
    return (ROOT / "scripts" / name).read_text(encoding="utf-8")


def node(node_id, name, node_type, position, parameters, *, version=1, credentials=None, **extra):
    payload = {
        "id": node_id,
        "name": name,
        "type": node_type,
        "typeVersion": version,
        "position": position,
        "parameters": parameters,
    }
    if credentials:
        payload["credentials"] = credentials
    payload.update(extra)
    return payload


def connection(target, index=0):
    return {"node": target, "type": "main", "index": index}


def build_workflow():
    nodes = [
        node("tw1", "Test workflow", "n8n-nodes-base.manualTrigger", [180, 180], {}, version=1),
        node(
            "tw2",
            "Check every 30 minutes",
            "n8n-nodes-base.scheduleTrigger",
            [180, 340],
            {"rule": {"interval": [{"field": "minutes", "minutesInterval": 30}]}},
            version=1.2,
        ),
        node(
            "tw3",
            "Config",
            "n8n-nodes-base.set",
            [420, 260],
            {
                "assignments": {
                    "assignments": [
                        {"name": "listUrl", "value": "https://twinning.msz.gov.pl/fiszki-twinning", "type": "string"},
                        {"name": "fromEmail", "value": "twinning@send.familyos.pl", "type": "string"},
                        {"name": "toEmailsCsv", "value": "michalreczek@gmail.com,wmotylewska@gmail.com", "type": "string"},
                        {"name": "lookbackDays", "value": 180, "type": "number"},
                        {"name": "maxOffers", "value": 30, "type": "number"},
                        {"name": "retentionDays", "value": 730, "type": "number"},
                        {"name": "waitSeconds", "value": 1, "type": "number"},
                    ]
                },
                "options": {},
            },
            version=3.4,
        ),
        node(
            "tw4",
            "Fetch active Twinning offers",
            "n8n-nodes-base.httpRequest",
            [680, 340],
            {
                "method": "GET",
                "url": "={{ 'http://127.0.0.1:8765/twinning/offers?url=' + encodeURIComponent($json.listUrl) + '&lookbackDays=' + encodeURIComponent($json.lookbackDays) + '&maxOffers=' + encodeURIComponent($json.maxOffers) }}",
                "options": {"response": {"response": {"responseFormat": "json"}}, "timeout": 180000},
            },
            version=4.2,
        ),
        node(
            "tw5",
            "Merge config and listing",
            "n8n-nodes-base.merge",
            [920, 260],
            {"mode": "combine", "combineBy": "combineByPosition", "options": {}},
            version=3.2,
        ),
        node(
            "tw6",
            "Select new or changed offers",
            "n8n-nodes-base.code",
            [1160, 260],
            {"mode": "runOnceForAllItems", "jsCode": read_script("twinning_select_offers.js")},
            version=2,
        ),
        node(
            "tw7",
            "Loop over offers",
            "n8n-nodes-base.splitInBatches",
            [1400, 260],
            {"batchSize": 1, "options": {}},
            version=3,
        ),
        node(
            "tw8",
            "Wait between offers",
            "n8n-nodes-base.wait",
            [1640, 360],
            {"resume": "timeInterval", "amount": "={{ $json.waitSeconds || 1 }}", "unit": "seconds"},
            version=1.1,
        ),
        node(
            "tw9",
            "Extract Twinning fiche",
            "n8n-nodes-base.httpRequest",
            [1880, 440],
            {
                "method": "GET",
                "url": "={{ 'http://127.0.0.1:8765/twinning/extract?url=' + encodeURIComponent($json.url) }}",
                "options": {"response": {"response": {"responseFormat": "json"}}, "timeout": 240000},
            },
            version=4.2,
        ),
        node(
            "tw10",
            "Merge offer and fiche",
            "n8n-nodes-base.merge",
            [2120, 360],
            {"mode": "combine", "combineBy": "combineByPosition", "options": {}},
            version=3.2,
        ),
        node(
            "tw11",
            "Analyse fit and requirements",
            "@n8n/n8n-nodes-langchain.informationExtractor",
            [2380, 440],
            {
                "text": "={{ ['DANE OGŁOSZENIA MSZ:', $json.pageText || '', 'TEKST FISZKI:', $json.analysisText || ''].join('\\n\\n') }}",
                "schemaType": "manual",
                "inputSchema": json.dumps(
                    {
                        "type": "object",
                        "properties": {
                            "projectTitle": {"type": "string"},
                            "purpose": {"type": "string", "description": "Cel projektu po polsku w 2-4 konkretnych zdaniach."},
                            "soughtProfiles": {"type": "array", "items": {"type": "string"}, "description": "Role i profile ekspertów: PL, RTA, liderzy komponentów, eksperci ad hoc."},
                            "mandatoryRequirements": {"type": "array", "items": {"type": "string"}, "description": "Konkretne wymagania: wykształcenie, lata doświadczenia, sektor, język, obywatelstwo/status."},
                            "keyTasks": {"type": "array", "items": {"type": "string"}},
                            "locationAndTravel": {"type": "string"},
                            "duration": {"type": "string"},
                            "budget": {"type": "string"},
                            "language": {"type": "string"},
                            "whoCanApply": {"type": "string", "description": "Wyjaśnij, że ofertę składa administracja publiczna lub Mandated Body, a ekspert indywidualny działa przez uprawnioną instytucję."},
                            "decisionSummary": {"type": "string", "description": "Krótka ocena komu warto aplikować i co jest główną barierą."},
                            "risksOrCaveats": {"type": "array", "items": {"type": "string"}},
                            "sourceQuality": {"type": "string", "description": "high, medium albo low"},
                        },
                        "required": ["purpose", "soughtProfiles", "mandatoryRequirements", "whoCanApply", "decisionSummary"],
                    },
                    ensure_ascii=False,
                ),
                "options": {
                    "systemPromptTemplate": "Jesteś polskim doradcą analizującym oficjalne fiszki projektów Twinning UE. Zwróć wyłącznie JSON zgodny ze schematem. Pisz po polsku, precyzyjnie i bez marketingu. Oddziel wymagania dla Project Leadera, Resident Twinning Advisera, liderów komponentów i ekspertów krótkoterminowych. Nie zmyślaj. Jeżeli danych brakuje, napisz to wprost. Podkreśl, że osoba fizyczna nie składa samodzielnej oferty: musi być delegowana przez kwalifikującą się administrację publiczną lub Mandated Body. Uwzględnij terminy, kraj, tryb pobytu RTA, misje ekspertów, budżet, czas realizacji i język, jeśli są w źródle.",
                },
            },
            version=1.2,
            retryOnFail=True,
            maxTries=5,
            waitBetweenTries=65000,
        ),
        node(
            "tw12",
            "Groq Chat Model",
            "@n8n/n8n-nodes-langchain.lmChatGroq",
            [2380, 660],
            {"model": "llama-3.3-70b-versatile", "options": {"temperature": 0.1, "maxTokensToSample": 1800}},
            version=1,
            credentials={"groqApi": {"id": "j4jwLe5JW6aKUJ0O", "name": "Groq account"}},
        ),
        node(
            "tw13",
            "Merge fiche and analysis",
            "n8n-nodes-base.merge",
            [2640, 360],
            {"mode": "combine", "combineBy": "combineByPosition", "options": {}},
            version=3.2,
        ),
        node(
            "tw14",
            "Build decision email",
            "n8n-nodes-base.code",
            [2880, 360],
            {"mode": "runOnceForAllItems", "jsCode": read_script("twinning_build_email.js")},
            version=2,
        ),
        node(
            "tw15",
            "Send via Resend",
            "n8n-nodes-base.httpRequest",
            [3120, 440],
            {
                "method": "POST",
                "url": "https://api.resend.com/emails",
                "authentication": "genericCredentialType",
                "genericAuthType": "httpHeaderAuth",
                "sendHeaders": True,
                "headerParameters": {"parameters": [
                    {"name": "Content-Type", "value": "application/json"},
                    {"name": "Idempotency-Key", "value": "={{ ('twinning/' + $json.offerId + '/' + $json.contentHash).slice(0, 256) }}"},
                ]},
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": "={{ ({ from: $json.fromEmail, to: $json.toEmails, subject: $json.subject, html: $json.html, text: $json.text }) }}",
                "options": {"timeout": 60000},
            },
            version=4.2,
            credentials={"httpHeaderAuth": {"id": "8pIewAUkFsshffYZ", "name": "Header Auth account"}},
            retryOnFail=True,
            maxTries=3,
            waitBetweenTries=5000,
        ),
        node(
            "tw16",
            "Merge email and delivery",
            "n8n-nodes-base.merge",
            [3360, 360],
            {"mode": "combine", "combineBy": "combineByPosition", "options": {}},
            version=3.2,
        ),
        node(
            "tw17",
            "Remember successful notification",
            "n8n-nodes-base.code",
            [3600, 360],
            {"mode": "runOnceForAllItems", "jsCode": read_script("twinning_mark_sent.js")},
            version=2,
        ),
        node("tw18", "Next offer", "n8n-nodes-base.noOp", [3840, 360], {}, version=1),
    ]

    connections = {
        "Test workflow": {"main": [[connection("Config")]]},
        "Check every 30 minutes": {"main": [[connection("Config")]]},
        "Config": {"main": [[connection("Fetch active Twinning offers"), connection("Merge config and listing", 0)]]},
        "Fetch active Twinning offers": {"main": [[connection("Merge config and listing", 1)]]},
        "Merge config and listing": {"main": [[connection("Select new or changed offers")]]},
        "Select new or changed offers": {"main": [[connection("Loop over offers")]]},
        "Loop over offers": {"main": [[], [connection("Wait between offers")]]},
        "Wait between offers": {"main": [[connection("Extract Twinning fiche"), connection("Merge offer and fiche", 0)]]},
        "Extract Twinning fiche": {"main": [[connection("Merge offer and fiche", 1)]]},
        "Merge offer and fiche": {"main": [[connection("Analyse fit and requirements"), connection("Merge fiche and analysis", 0)]]},
        "Analyse fit and requirements": {"main": [[connection("Merge fiche and analysis", 1)]]},
        "Groq Chat Model": {"ai_languageModel": [[{"node": "Analyse fit and requirements", "type": "ai_languageModel", "index": 0}]]},
        "Merge fiche and analysis": {"main": [[connection("Build decision email")]]},
        "Build decision email": {"main": [[connection("Send via Resend"), connection("Merge email and delivery", 0)]]},
        "Send via Resend": {"main": [[connection("Merge email and delivery", 1)]]},
        "Merge email and delivery": {"main": [[connection("Remember successful notification")]]},
        "Remember successful notification": {"main": [[connection("Next offer")]]},
        "Next offer": {"main": [[connection("Loop over offers")]]},
    }
    return {
        "id": "TWNMONITOR2026",
        "name": "MSZ Twinning → analiza ofert → Resend",
        "active": False,
        "nodes": nodes,
        "connections": connections,
        "settings": {
            "executionOrder": "v1",
            "timezone": "Europe/Warsaw",
            "saveManualExecutions": True,
            "saveExecutionProgress": True,
            "saveDataSuccessExecution": "all",
            "saveDataErrorExecution": "all",
        },
        "versionId": "twinning-monitor-resend-v1",
        "meta": {"templateCredsSetupCompleted": False},
        "tags": [],
    }


if __name__ == "__main__":
    target = ROOT / "TwinningMonitor.json"
    target.write_text(json.dumps(build_workflow(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)
