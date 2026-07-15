import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from smoke_briefing_research import run_javascript


RESEARCH = {
    "dateFrom": "2026-07-06",
    "dateTo": "2026-07-13",
    "generatedAt": "2026-07-15T12:00:00Z",
    "interpellations": [
        {
            "num": 17725,
            "title": "Interpelacja w sprawie wprowadzenia tzw. minimum kadrowego na wydziałach prawa",
            "sentDate": "2026-06-23",
            "eventDate": "2026-07-10",
            "eventType": "deadline-extension",
            "recipients": ["minister nauki i szkolnictwa wyższego"],
            "bodyText": "Posłowie pytają o status reprezentacji dziekanów publicznych uniwersyteckich wydziałów prawa, konsultacje MNiSW z uczelniami i środowiskiem akademickim oraz możliwość przywrócenia minimum kadrowego.",
            "replyText": "",
            "replyStatus": "deadline-extension",
            "replyAuthor": "Sekretarz stanu w Ministerstwie Nauki i Szkolnictwa Wyższego Marek Gzik",
            "researchQuality": "full-text",
            "url": "https://sejm.gov.pl/sejm10.nsf/interpelacja.xsp?typ=int&nr=17725",
        },
        {
            "num": 17801,
            "title": "Interpelacja w sprawie powołania Zespołu Identyfikującego Członków Rady Narodowego Centrum Nauki",
            "sentDate": "2026-06-22",
            "eventDate": "2026-07-08",
            "eventType": "answer-update",
            "recipients": ["minister nauki i szkolnictwa wyższego"],
            "bodyText": "Posłowie pytają o podstawę prawną, kryteria i konsultacje dotyczące składu zespołu wskazującego kandydatów do Rady NCN.",
            "replyText": "Minister wyjaśnił podstawę prawną powołania zespołu, wymagania wobec jego członków oraz odrębne kryteria dotyczące kandydatów do Rady NCN.",
            "replyStatus": "answered",
            "replyAuthor": "Sekretarz stanu Marek Gzik",
            "replyDate": "2026-07-06",
            "researchQuality": "full-text",
            "url": "https://sejm.gov.pl/sejm10.nsf/interpelacja.xsp?typ=int&nr=17801",
        },
    ],
    "writtenQuestions": [],
    "prints": [],
    "eliActs": [],
    "sources": {
        "interpellations": {"checked": 2, "withinWindow": 2, "enriched": 2},
        "writtenQuestions": {"checked": 0, "withinWindow": 0, "enriched": 0},
        "prints": {"checked": 0, "withinWindow": 0, "enriched": 0},
        "eliActs": {"checked": 0, "withinWindow": 0, "enriched": 0},
    },
    "sourceErrors": [],
}

SUMMARIES = [
    {
        "id": "17725",
        "questionSummary": "Poseł pyta o status i reprezentatywność Konferencji Dziekanów Publicznych Uniwersyteckich Wydziałów Prawa oraz podstawę jej udziału w konsultacjach z MNiSW. Chce też wiedzieć, czy resort planuje szersze konsultacje i prace nad przywróceniem minimum kadrowego na wydziałach prawa.",
        "answerSummary": "Minister poparł przywrócenie minimum kadrowego.",
    },
    {
        "id": "17801",
        "questionSummary": "Posłowie pytają o podstawę prawną i kryteria doboru członków zespołu wskazującego kandydatów do Rady NCN. Pytają również o konsultacje składu zespołu i sposób zapewnienia reprezentatywności dyscyplin naukowych.",
        "answerSummary": "Sekretarz stanu Marek Gzik wskazał ustawową podstawę powołania zespołu i wyjaśnił, że wymagania wobec jego członków różnią się od kryteriów stawianych kandydatom do Rady NCN. Odpowiedź opisuje tryb wyłaniania kandydatów, ale nie potwierdza dodatkowych konsultacji poza resortem.",
    },
]


def render_html() -> str:
    return run_javascript(RESEARCH, SUMMARIES, include_html=True)["mail"]["html"]


class Handler(BaseHTTPRequestHandler):
    html = render_html().encode("utf-8")

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(self.html)))
        self.end_headers()
        self.wfile.write(self.html)

    def log_message(self, format, *args):
        return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
