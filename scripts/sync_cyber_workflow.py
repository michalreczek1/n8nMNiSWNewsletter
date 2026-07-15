import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "CyberMonitorSejmowy.json"
SOURCES = {
    "Przygotuj URL-e zrodel": ROOT / "scripts" / "cyber_prepare_sources.js",
    "Agreguj i filtruj dane": ROOT / "scripts" / "cyber_aggregate_filter.js",
}


workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
nodes = {node["name"]: node for node in workflow["nodes"]}
for node_name, source_path in SOURCES.items():
    nodes[node_name]["parameters"]["jsCode"] = source_path.read_text(encoding="utf-8")

workflow["id"] = "cmSjm260419t3iA"
workflow["active"] = False
WORKFLOW_PATH.write_text(
    json.dumps(workflow, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
