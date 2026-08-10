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
    wait_seconds = next(item["value"] for item in config if item["name"] == "waitSeconds")
    assert recipients == "michalreczek@gmail.com,wmotylewska@gmail.com"
    assert wait_seconds == 70
    assert nodes["Send via Resend"]["credentials"]["httpHeaderAuth"]["id"] == "8pIewAUkFsshffYZ"
    assert nodes["Groq Chat Model"]["credentials"]["groqApi"]["id"] == "j4jwLe5JW6aKUJ0O"
    assert nodes["Analyse fit and requirements"]["retryOnFail"] is True
    assert nodes["Analyse fit and requirements"]["waitBetweenTries"] == 65000
    assert nodes["Send via Resend"]["retryOnFail"] is True
    assert nodes["Digest every two days"]["parameters"]["rule"]["interval"][0] == {
        "field": "days",
        "daysInterval": 2,
        "triggerAtHour": 8,
    }
    digest_config = nodes["Digest config"]["parameters"]["assignments"]["assignments"]
    digest_recipients = next(item["value"] for item in digest_config if item["name"] == "toEmailsCsv")
    assert digest_recipients == recipients
    assert nodes["Send digest via Resend"]["credentials"]["httpHeaderAuth"]["id"] == "8pIewAUkFsshffYZ"


def test_workflow_marks_state_only_after_resend_delivery_merge():
    workflow = build_workflow()
    connections = workflow["connections"]
    assert connections["Send via Resend"]["main"][0][0]["node"] == "Merge email and delivery"
    assert connections["Merge email and delivery"]["main"][0][0]["node"] == "Acknowledge successful notification"
    assert connections["Acknowledge successful notification"]["main"][0][0]["node"] == "Next offer"
    nodes = {node["name"]: node for node in workflow["nodes"]}
    assert nodes["Build decision email"]["parameters"]["mode"] == "runOnceForAllItems"
    assert "/twinning/ack?" in nodes["Acknowledge successful notification"]["parameters"]["url"]


def test_workflow_sends_strong_and_borderline_but_queues_clear_nonmatches():
    workflow = build_workflow()
    connections = workflow["connections"]
    fit_outputs = connections["Is profile match or borderline"]["main"]
    assert fit_outputs[0][0]["node"] == "Build decision email"
    assert fit_outputs[1][0]["node"] == "Queue for two-day digest"
    nodes = {node["name"]: node for node in workflow["nodes"]}
    prompt = nodes["Analyse fit and requirements"]["parameters"]["options"]["systemPromptTemplate"]
    assert "magister administracji Uniwersytetu Jagiellońskiego" in prompt
    assert "Od września 2024 r. radca w Ministerstwie Nauki i Szkolnictwa Wyższego" in prompt
    assert "prowadzi projekty informatyczne" in prompt
    assert "język angielski C1" in prompt
    assert "staż w administracji brytyjskiej i współpracę z Radą Europy" in prompt
    assert "lider komponentu są realnymi rolami" in prompt
    assert "nie zakładaj wcześniejszego formalnego udziału w projekcie Twinning" in prompt
    assert "W każdej sytuacji granicznej wybierz borderline" in prompt
    assert "Short-Term Experts (STE)/ekspertów ad hoc" in prompt
    assert nodes["Queue for two-day digest"]["parameters"]["method"] == "POST"
    assert nodes["Acknowledge digest delivery"]["parameters"]["method"] == "POST"


def test_generated_export_matches_builder():
    export = json.loads((ROOT / "TwinningMonitor.json").read_text(encoding="utf-8"))
    assert export == build_workflow()
