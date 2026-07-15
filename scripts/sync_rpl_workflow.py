import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "RPL.json"
SOURCES = {
    "Extract Recent Project URLs": ROOT / "scripts" / "rpl_extract_recent_projects.js",
    "Finalize Project Analysis": ROOT / "scripts" / "rpl_finalize_project_analysis.js",
}


workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
nodes = {node["name"]: node for node in workflow["nodes"]}
for node_name, source_path in SOURCES.items():
    nodes[node_name]["parameters"]["jsCode"] = source_path.read_text(encoding="utf-8")

WORKFLOW_PATH.write_text(
    json.dumps(workflow, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
