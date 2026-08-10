import json
from pathlib import Path

from scripts.build_twinning_workflow import build_workflow


ROOT = Path(__file__).resolve().parents[1]


def test_workflow_has_schedule_credentials_and_two_recipients():
    workflow = build_workflow()
    nodes = {node["name"]: node for node in workflow["nodes"]}
    assert nodes["Check every 30 minutes"]["parameters"]["rule"]["interval"][0] == {
        "field": "minutes",
        "minutesInterval": 30,
    }
    config = nodes["Config"]["parameters"]["assignments"]["assignments"]
    recipients = next(item["value"] for item in config if item["name"] == "toEmailsCsv")
    assert recipients == "michalreczek@gmail.com,wmotylewska@gmail.com"
    assert nodes["Send via Resend"]["credentials"]["httpHeaderAuth"]["id"] == "8pIewAUkFsshffYZ"
    assert nodes["Groq Chat Model"]["credentials"]["groqApi"]["id"] == "j4jwLe5JW6aKUJ0O"


def test_workflow_marks_state_only_after_resend_delivery_merge():
    workflow = build_workflow()
    connections = workflow["connections"]
    assert connections["Send via Resend"]["main"][0][0]["node"] == "Merge email and delivery"
    assert connections["Merge email and delivery"]["main"][0][0]["node"] == "Remember successful notification"
    assert connections["Remember successful notification"]["main"][0][0]["node"] == "Next offer"


def test_generated_export_matches_builder():
    export = json.loads((ROOT / "TwinningMonitor.json").read_text(encoding="utf-8"))
    assert export == build_workflow()

