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
                        {"name": "waitSeconds", "value": 70, "type": "number"},
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
                            "fitBand": {"type": "string", "enum": ["strong", "borderline", "no_fit"], "description": "Dopasowanie do profilu użytkownika. Przy niepewności zawsze borderline, nigdy no_fit."},
                            "fitScore": {"type": "integer", "minimum": 0, "maximum": 100},
                            "fitReason": {"type": "string", "description": "Konkretne uzasadnienie dopasowania lub niedopasowania do profilu."},
                            "bestEntryRole": {"type": "string", "description": "Najbardziej realna rola wejściowa, preferuj STE/ekspert ad hoc."},
                            "internationalExperienceRequirement": {"type": "string", "description": "Czy wcześniejsze doświadczenie międzynarodowe/Twinning jest wymagane, preferowane czy niewskazane."},
                        },
                        "required": ["purpose", "soughtProfiles", "mandatoryRequirements", "whoCanApply", "decisionSummary", "fitBand", "fitScore", "fitReason", "bestEntryRole", "internationalExperienceRequirement"],
                    },
                    ensure_ascii=False,
                ),
                "options": {
                    "systemPromptTemplate": "Jesteś polskim doradcą analizującym oficjalne fiszki projektów Twinning UE. Zwróć wyłącznie JSON zgodny ze schematem. Pisz po polsku, precyzyjnie i bez marketingu. Oddziel wymagania dla Project Leadera, Resident Twinning Advisera, liderów komponentów oraz Short-Term Experts (STE)/ekspertów ad hoc. Nie zmyślaj. Jeżeli danych brakuje, napisz to wprost. Profil użytkownika: wykształcenie — administracja publiczna na Wydziale Prawa i Administracji; doświadczenie — cyfryzacja, informatyzacja, szkolnictwo wyższe i nauka, zarządzanie projektami, zarządzanie procesowe, administracja i postępowanie administracyjne, decyzje administracyjne, legislacja oraz przeciwdziałanie korupcji. Użytkownik nie ma jeszcze doświadczenia w projektach międzynarodowych/Twinning, więc najbardziej realną drogą wejścia jest STE lub ekspert ad hoc. Nie myl junior partner (instytucja w konsorcjum) z początkującym ekspertem. fitBand=strong, gdy istnieje wyraźnie dopasowana rola; fitBand=borderline, gdy dopasowanie jest możliwe, brakuje danych o kwalifikacjach albo doświadczenie międzynarodowe jest tylko preferowane; fitBand=no_fit wyłącznie gdy dziedzina jest wyraźnie obca lub każda dostępna rola ma jednoznaczne, niespełnione wymaganie wcześniejszego doświadczenia międzynarodowego/Twinning. W każdej sytuacji granicznej wybierz borderline. Podkreśl, że osoba fizyczna nie składa samodzielnej oferty: musi być delegowana przez kwalifikującą się administrację publiczną lub Mandated Body. Uwzględnij terminy, kraj, tryb pobytu RTA, misje ekspertów, budżet, czas realizacji i język, jeśli są w źródle.",
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
            "Is profile match or borderline",
            "n8n-nodes-base.if",
            [2860, 360],
            {
                "conditions": {
                    "options": {"caseSensitive": False, "leftValue": "", "typeValidation": "strict"},
                    "conditions": [{
                        "leftValue": "={{ (($json.output && $json.output.fitBand) || 'borderline') !== 'no_fit' }}",
                        "rightValue": True,
                        "operator": {"type": "boolean", "operation": "true"},
                    }],
                    "combinator": "and",
                },
                "options": {},
            },
            version=2,
        ),
        node(
            "tw15",
            "Build decision email",
            "n8n-nodes-base.code",
            [3100, 260],
            {"mode": "runOnceForAllItems", "jsCode": read_script("twinning_build_email.js")},
            version=2,
        ),
        node(
            "tw16",
            "Send via Resend",
            "n8n-nodes-base.httpRequest",
            [3340, 340],
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
            "tw17",
            "Merge email and delivery",
            "n8n-nodes-base.merge",
            [3580, 260],
            {"mode": "combine", "combineBy": "combineByPosition", "options": {}},
            version=3.2,
        ),
        node(
            "tw18",
            "Acknowledge successful notification",
            "n8n-nodes-base.httpRequest",
            [3820, 260],
            {
                "method": "GET",
                "url": "={{ 'http://127.0.0.1:8765/twinning/ack?offerId=' + encodeURIComponent($json.offerId) + '&contentHash=' + encodeURIComponent($json.contentHash) + '&recipients=' + encodeURIComponent(($json.toEmails || []).join(',')) + '&resendId=' + encodeURIComponent($json.id || $json.resendId || '') }}",
                "options": {"response": {"response": {"responseFormat": "json"}}, "timeout": 30000},
            },
            version=4.2,
        ),
        node(
            "tw19",
            "Queue for two-day digest",
            "n8n-nodes-base.httpRequest",
            [3100, 520],
            {
                "method": "POST",
                "url": "http://127.0.0.1:8765/twinning/queue-digest",
                "sendHeaders": True,
                "headerParameters": {"parameters": [{"name": "Content-Type", "value": "application/json"}]},
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": "={{ ({ offerId: $json.offerId, contentHash: $json.contentHash, title: $json.title, country: $json.country, area: $json.area, mszDeadline: $json.mszDeadline, url: $json.url, fitBand: ($json.output && $json.output.fitBand) || 'no_fit', fitScore: ($json.output && $json.output.fitScore) || 0, fitReason: ($json.output && $json.output.fitReason) || '', bestEntryRole: ($json.output && $json.output.bestEntryRole) || '' }) }}",
                "options": {"response": {"response": {"responseFormat": "json"}}, "timeout": 30000},
            },
            version=4.2,
        ),
        node("tw20", "Next offer", "n8n-nodes-base.noOp", [4060, 360], {}, version=1),
        node(
            "tw21",
            "Digest every two days",
            "n8n-nodes-base.scheduleTrigger",
            [180, 780],
            {"rule": {"interval": [{"field": "days", "daysInterval": 2, "triggerAtHour": 8}]}},
            version=1.2,
        ),
        node(
            "tw22",
            "Digest config",
            "n8n-nodes-base.set",
            [420, 780],
            {
                "assignments": {"assignments": [
                    {"name": "fromEmail", "value": "twinning@send.familyos.pl", "type": "string"},
                    {"name": "toEmailsCsv", "value": "michalreczek@gmail.com,wmotylewska@gmail.com", "type": "string"},
                ]},
                "options": {},
            },
            version=3.4,
        ),
        node(
            "tw23",
            "Fetch digest queue",
            "n8n-nodes-base.httpRequest",
            [660, 860],
            {
                "method": "GET",
                "url": "http://127.0.0.1:8765/twinning/digest",
                "options": {"response": {"response": {"responseFormat": "json"}}, "timeout": 30000},
            },
            version=4.2,
        ),
        node(
            "tw24",
            "Merge digest config and queue",
            "n8n-nodes-base.merge",
            [900, 780],
            {"mode": "combine", "combineBy": "combineByPosition", "options": {}},
            version=3.2,
        ),
        node(
            "tw25",
            "Build two-day digest",
            "n8n-nodes-base.code",
            [1140, 780],
            {"mode": "runOnceForAllItems", "jsCode": read_script("twinning_build_digest.js")},
            version=2,
        ),
        node(
            "tw26",
            "Send digest via Resend",
            "n8n-nodes-base.httpRequest",
            [1380, 860],
            {
                "method": "POST",
                "url": "https://api.resend.com/emails",
                "authentication": "genericCredentialType",
                "genericAuthType": "httpHeaderAuth",
                "sendHeaders": True,
                "headerParameters": {"parameters": [
                    {"name": "Content-Type", "value": "application/json"},
                    {"name": "Idempotency-Key", "value": "={{ $json.digestKey }}"},
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
            "tw27",
            "Merge digest and delivery",
            "n8n-nodes-base.merge",
            [1620, 780],
            {"mode": "combine", "combineBy": "combineByPosition", "options": {}},
            version=3.2,
        ),
        node(
            "tw28",
            "Acknowledge digest delivery",
            "n8n-nodes-base.httpRequest",
            [1860, 780],
            {
                "method": "POST",
                "url": "http://127.0.0.1:8765/twinning/digest-ack",
                "sendHeaders": True,
                "headerParameters": {"parameters": [{"name": "Content-Type", "value": "application/json"}]},
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": "={{ ({ offerIds: $json.offerIds, recipients: $json.toEmails, resendId: $json.id || $json.resendId || '' }) }}",
                "options": {"response": {"response": {"responseFormat": "json"}}, "timeout": 30000},
            },
            version=4.2,
        ),
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
        "Merge fiche and analysis": {"main": [[connection("Is profile match or borderline")]]},
        "Is profile match or borderline": {"main": [[connection("Build decision email")], [connection("Queue for two-day digest")]]},
        "Build decision email": {"main": [[connection("Send via Resend"), connection("Merge email and delivery", 0)]]},
        "Send via Resend": {"main": [[connection("Merge email and delivery", 1)]]},
        "Merge email and delivery": {"main": [[connection("Acknowledge successful notification")]]},
        "Acknowledge successful notification": {"main": [[connection("Next offer")]]},
        "Queue for two-day digest": {"main": [[connection("Next offer")]]},
        "Next offer": {"main": [[connection("Loop over offers")]]},
        "Digest every two days": {"main": [[connection("Digest config")]]},
        "Digest config": {"main": [[connection("Fetch digest queue"), connection("Merge digest config and queue", 0)]]},
        "Fetch digest queue": {"main": [[connection("Merge digest config and queue", 1)]]},
        "Merge digest config and queue": {"main": [[connection("Build two-day digest")]]},
        "Build two-day digest": {"main": [[connection("Send digest via Resend"), connection("Merge digest and delivery", 0)]]},
        "Send digest via Resend": {"main": [[connection("Merge digest and delivery", 1)]]},
        "Merge digest and delivery": {"main": [[connection("Acknowledge digest delivery")]]},
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
