import argparse
import json
import subprocess
import sys
from pathlib import Path

from sejm_research import research_legal_sources


ROOT = Path(__file__).resolve().parents[1]
FILTER_PATH = ROOT / "scripts" / "briefing_relevance_filter.js"
BUILD_PATH = ROOT / "scripts" / "briefing_build_newsletter.js"
APPLY_PATH = ROOT / "scripts" / "briefing_apply_summaries.js"


def run_javascript(
    research: dict,
    ai_summaries: list[dict] | None = None,
    include_html: bool = False,
) -> dict:
    harness = r"""
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const filterSource = fs.readFileSync(process.argv[1], 'utf8');
const applySource = fs.readFileSync(process.argv[2], 'utf8');
const buildSource = fs.readFileSync(process.argv[3], 'utf8');
const staticData = {};
const init = {
  dateFrom: input.research.dateFrom,
  dateTo: input.research.dateTo,
  fromEmail: 'smoke@example.test',
  toEmail: 'smoke@example.test',
};
const filter = new Function('$input', '$', '$getWorkflowStaticData', filterSource);
const filtered = filter(
  { first: () => ({ json: input.research }) },
  () => ({ first: () => ({ json: init }) }),
  () => staticData,
)[0].json;
const apply = new Function('$json', applySource);
const summarized = apply({ ...filtered, output: { summaries: input.aiSummaries || [] } })[0].json;
const build = new Function('$json', buildSource);
const mail = build(summarized)[0].json;
const groups = ['interpelacje', 'zapytania', 'druki', 'aktyPrawne'];
const titles = Object.fromEntries(groups.map(group => [
  group,
  (summarized[group] || []).map(item => ({
    id: item.num || item.number || item.eli,
    title: item.title,
    score: item.score,
    reason: item.decisionReason,
    quality: item.researchQuality,
    questionSummary: item.questionSummary,
    answerSummary: item.answerSummary,
    replyStatus: item.replyStatus,
  })),
]));
process.stdout.write(JSON.stringify({
  briefingStatus: filtered.briefingStatus,
  stats: filtered.stats,
  scanStats: filtered.scanStats,
  sourceErrors: filtered.sourceErrors,
  titles,
  mail: {
    subject: mail.subject,
    htmlLength: mail.html.length,
    textLength: mail.text.length,
    textPreview: mail.text.slice(0, 3200),
    html: input.includeHtml ? mail.html : undefined,
  },
}, null, 2));
"""
    result = subprocess.run(
        ["node", "-e", harness, str(FILTER_PATH), str(APPLY_PATH), str(BUILD_PATH)],
        input=json.dumps(
            {
                "research": research,
                "aiSummaries": ai_summaries or [],
                "includeHtml": include_html,
            },
            ensure_ascii=False,
        ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("date_from")
    parser.add_argument("date_to")
    parser.add_argument("--max-enrich", type=int, default=4)
    args = parser.parse_args()
    research = research_legal_sources(
        args.date_from,
        args.date_to,
        scope="mnisw",
        term=10,
        max_enrich=args.max_enrich,
    )
    print(json.dumps(run_javascript(research), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
