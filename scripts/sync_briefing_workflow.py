import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "BriefingParlamentarnyMNiSW.json"
NORMALIZE_PATH = ROOT / "scripts" / "briefing_normalize_research.js"
FILTER_PATH = ROOT / "scripts" / "briefing_relevance_filter.js"
BUILD_PATH = ROOT / "scripts" / "briefing_build_newsletter.js"


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

build = by_name["Buduj HTML newsletter"]
build["parameters"]["jsCode"] = BUILD_PATH.read_text(encoding="utf-8")
build["position"] = [1180, 250]

send = by_name["Resend: wyślij email"]
send["position"] = [1420, 250]
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
workflow["nodes"].sort(key=lambda node: (node["position"][0], node["position"][1], node["name"]))

workflow["connections"] = {
    "When clicking Test workflow": connection("Init: daty i stan"),
    "Poniedziałek 07:00": connection("Init: daty i stan"),
    "Init: daty i stan": connection("Research API: Sejm i ELI"),
    "Research API: Sejm i ELI": connection("Normalize: Research"),
    "Normalize: Research": connection("Filtruj i scoruj (MNiSW)"),
    "Filtruj i scoruj (MNiSW)": connection("Buduj HTML newsletter"),
    "Buduj HTML newsletter": connection("Resend: wyślij email"),
}
workflow["id"] = "9cDqVFh4KQBYw7ic"
workflow["active"] = False
workflow["tags"] = []

WORKFLOW_PATH.write_text(
    json.dumps(workflow, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
