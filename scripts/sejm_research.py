import json
import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import quote, urlencode

from rcl_extract_project import clean_html, clean_text, extract_document_text, fetch_bytes


SEJM_API = "https://api.sejm.gov.pl/sejm"
ELI_API = "https://api.sejm.gov.pl/eli"
PAGE_SIZE = 100
MAX_PAGES = 50


SCOPE_PATTERNS = {
    "mnisw": [
        ("higher-education-law", re.compile(r"\bprawo\s+o\s+szkolnictw\w*\s+wyzsz\w*\s+i\s+nauce\b")),
        ("higher-education", re.compile(r"\bszkolnictw\w*\s+wyzsz\w*\b|\bksztalceni\w*\s+wyzsz\w*\b")),
        ("universities", re.compile(r"\buczelni\w*\b|\buniwersytet\w*\b|\bpolitechnik\w*\b|\bszkol\w*\s+wyzsz\w*\b")),
        ("students", re.compile(r"\bstuden\w*\b|\bstudi(?:a|ow|ach|ami|om)\b")),
        ("doctoral", re.compile(r"\bdoktoran\w*\b|\bdoktorat\w*\b|\bhabilitac\w*\b|\bstopni\w*\s+naukow\w*\b")),
        ("academic-staff", re.compile(r"\bnauczyciel\w*\s+akademick\w*\b|\bpracownik\w*\s+naukow\w*\b")),
        ("science-policy", re.compile(r"\bbadan\w*\s+naukow\w*\b|\bdzialalnos\w*\s+naukow\w*\b|\bfinansowani\w*\s+nauk\w*\b|\bminister\w*\s+nauki\b")),
        # Ogolny "instytut badawczy" obejmuje tez jednostki resortow zdrowia,
        # obrony i rolnictwa. Research ma premiowac instytucje systemu MNiSW.
        ("science-institutions", re.compile(r"\bpolsk\w*\s+akademi\w*\s+nauk\w*\b|\bnarodow\w*\s+centrum\s+nauk\w*\b|\bnarodow\w*\s+centrum\s+badan\w*\s+i\s+rozwoju\b|\bsiec\w*\s+badawcz\w*\s+lukasiewicz\b|\bnawa\b|\bpolon\b")),
    ],
    "cyber": [
        ("cybersecurity", re.compile(r"\bcyberbezpieczen\w*\b|\bkrajow\w*\s+system\w*\s+cyberbezpieczen\w*\b|\bnis\s*2?\b|\bdora\b")),
        ("information-systems", re.compile(r"\bsystem\w*\s+teleinformatycz\w*\b|\bsieci\w*\s+i\s+system\w*\s+informacyjn\w*\b|\bcsirt\b|\bcert\b")),
        ("data-protection", re.compile(r"\bochron\w*\s+danych\s+osobow\w*\b|\brodo\b|\bprywatnos\w*\s+cyfrow\w*\b")),
        ("digital-identity", re.compile(r"\btozsamos\w*\s+elektroniczn\w*\b|\buslug\w*\s+zaufania\b|\bpodpis\w*\s+elektroniczn\w*\b")),
        ("ai-governance", re.compile(r"\bsztuczn\w*\s+inteligencj\w*\b|\bai\s+act\b")),
    ],
}


def normalize_for_match(value: str) -> str:
    text = clean_text(str(value or "")).lower().replace("ł", "l")
    text = "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9\s]", " ", text)


def matched_scope_labels(value: str, scope: str) -> list[str]:
    normalized = normalize_for_match(value)
    return [label for label, pattern in SCOPE_PATTERNS[scope] if pattern.search(normalized)]


def fetch_json(url: str):
    data, _, _ = fetch_bytes(url)
    return json.loads(data.decode("utf-8-sig"))


def fetch_text(url: str) -> str:
    data, _, _ = fetch_bytes(url)
    decoded = data.decode("utf-8", errors="ignore")
    return clean_html(decoded) if "<" in decoded and ">" in decoded else clean_text(decoded)


def _iso_date(value: str) -> str:
    value = str(value or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"Invalid ISO date: {value}")
    datetime.strptime(value, "%Y-%m-%d")
    return value


def _date_part(value) -> str:
    match = re.search(r"\d{4}-\d{2}-\d{2}", str(value or ""))
    return match.group(0) if match else ""


def _in_window(value, date_from: str, date_to: str) -> bool:
    date = _date_part(value)
    return bool(date and date_from <= date <= date_to)


def _record_in_window(record: dict, fields: tuple[str, ...], date_from: str, date_to: str) -> bool:
    return any(_in_window(record.get(field), date_from, date_to) for field in fields)


def _build_url(base: str, params: dict) -> str:
    return f"{base}?{urlencode(params)}"


def fetch_paginated_array(base_url: str, params: dict, max_pages: int = MAX_PAGES) -> list[dict]:
    items = []
    seen_page_heads = set()
    offset = 0
    for _ in range(max_pages):
        page_params = {**params, "offset": offset, "limit": PAGE_SIZE}
        page = fetch_json(_build_url(base_url, page_params))
        if not isinstance(page, list):
            raise RuntimeError(f"Expected an array from {base_url}")
        if not page:
            break
        head = json.dumps(page[0], ensure_ascii=False, sort_keys=True)[:500]
        if head in seen_page_heads:
            break
        seen_page_heads.add(head)
        items.extend(value for value in page if isinstance(value, dict))
        if len(page) < PAGE_SIZE:
            break
        offset += len(page)
    return items


def fetch_paginated_eli(params: dict, max_pages: int = MAX_PAGES) -> tuple[list[dict], int]:
    items = []
    offset = 0
    total_count = 0
    for _ in range(max_pages):
        page_params = {**params, "offset": offset, "limit": PAGE_SIZE}
        page = fetch_json(_build_url(f"{ELI_API}/acts/search", page_params))
        if not isinstance(page, dict) or not isinstance(page.get("items"), list):
            raise RuntimeError("Expected an ELI search result object")
        batch = [value for value in page["items"] if isinstance(value, dict)]
        total_count = int(page.get("totalCount") or len(batch))
        items.extend(batch)
        if not batch or len(items) >= total_count or len(batch) < PAGE_SIZE:
            break
        offset += len(batch)
    return items, total_count


def _web_link(record: dict, fallback: str) -> str:
    for link in record.get("links") or []:
        if isinstance(link, dict) and link.get("rel") == "web-description" and link.get("href"):
            return link["href"]
    return fallback


def _body_link(record: dict) -> str:
    for link in record.get("links") or []:
        if isinstance(link, dict) and link.get("rel") == "body" and link.get("href"):
            return link["href"]
    return ""


def _evidence_summary(text: str, scope: str, max_length: int = 900) -> str:
    text = clean_text(text).replace("\n", " ")
    if not text:
        return ""
    sentences = [clean_text(part) for part in re.split(r"(?<=[.!?])\s+", text) if len(clean_text(part)) >= 45]
    boilerplate = re.compile(
        r"\b(interpelacja\s+nr|zapytanie\s+nr|zglaszajac|data\s+wplywu|adresat|"
        r"warszawa,?\s+dnia|szanown(?:y|a)\s+pan(?:ie|i))\b",
        re.IGNORECASE,
    )
    sentences = [sentence for sentence in sentences if not boilerplate.search(normalize_for_match(sentence))]
    matched = [sentence for sentence in sentences if matched_scope_labels(sentence, scope)]
    selected = matched[:2] or sentences[:2]
    summary = clean_text(" ".join(selected))
    if len(summary) <= max_length:
        return summary
    return summary[:max_length].rsplit(" ", 1)[0].rstrip(" ,;:-") + "..."


def _recipient_names(record: dict) -> list[str]:
    details = record.get("recipientDetails") or []
    names = [clean_text(value.get("name")) for value in details if isinstance(value, dict)]
    if not names:
        names = [clean_text(value) for value in record.get("to") or []]
    return [value for value in names if value]


def _reply_sort_key(reply: dict) -> str:
    return str(reply.get("lastModified") or reply.get("receiptDate") or "")


def _latest_reply(record: dict) -> dict:
    replies = [reply for reply in record.get("replies") or [] if isinstance(reply, dict)]
    replies.sort(key=_reply_sort_key, reverse=True)
    return replies[0] if replies else {}


def _reply_body_link(reply: dict) -> str:
    for link in reply.get("links") or []:
        if isinstance(link, dict) and link.get("rel") == "body" and link.get("href"):
            return link["href"]
    return ""


def _reply_attachment_url(reply: dict) -> str:
    attachments = [value for value in reply.get("attachments") or [] if isinstance(value, dict)]
    usable = [
        value
        for value in attachments
        if not clean_text(value.get("name")).lower().endswith((".xades", ".xml", ".sig"))
    ]
    supported = [
        value
        for value in usable
        if clean_text(value.get("name")).lower().endswith((".pdf", ".docx", ".docm", ".doc"))
    ]
    attachment = (supported or usable or [{}])[0]
    return clean_text(attachment.get("URL") or attachment.get("url") or attachment.get("href"))


def _enrich_question(record: dict, source_type: str, scope: str, fetch_content: bool = True) -> dict:
    item = dict(record)
    num = item.get("num")
    recipients = _recipient_names(item)
    title = clean_text(item.get("title"))
    seed_text = " ".join([title, *recipients])
    seed_labels = matched_scope_labels(seed_text, scope)
    body_text = ""
    reply_text = ""
    reply_document_url = ""
    latest_reply = _latest_reply(item)
    is_prolongation = bool(latest_reply.get("prolongation"))
    reply_author = clean_text(latest_reply.get("from"))
    reply_date = _date_part(latest_reply.get("receiptDate") or latest_reply.get("lastModified"))
    body_url = _body_link(item)
    if fetch_content and seed_labels and body_url:
        try:
            body_text = fetch_text(body_url)[:16000]
        except Exception:
            body_text = ""
    reply_url = _reply_body_link(latest_reply)
    if fetch_content and seed_labels and reply_url and not is_prolongation:
        try:
            reply_text = fetch_text(reply_url)[:12000]
        except Exception:
            reply_text = ""
    if fetch_content and seed_labels and not is_prolongation and (latest_reply.get("onlyAttachment") or not reply_text):
        attachment_url = _reply_attachment_url(latest_reply)
        if attachment_url:
            reply_document_url = attachment_url
            try:
                reply_text, _, reply_document_url = extract_document_text(attachment_url)
                reply_text = clean_text(reply_text)[:16000]
            except Exception:
                reply_text = ""
    if is_prolongation:
        reply_status = "deadline-extension"
    elif latest_reply and reply_text:
        reply_status = "answered"
    elif latest_reply:
        reply_status = "unreadable-answer"
    else:
        reply_status = "no-answer"
    labels = matched_scope_labels(" ".join([seed_text, body_text, reply_text]), scope)
    item.update(
        {
            "sourceType": source_type,
            "recipients": recipients,
            "bodyText": body_text,
            "replyText": reply_text,
            "replyStatus": reply_status,
            "replyAuthor": reply_author,
            "replyDate": reply_date,
            "replyDocumentUrl": reply_document_url,
            "summary": _evidence_summary(body_text, scope),
            "replySummary": _evidence_summary(reply_text, scope),
            "researchText": clean_text(" ".join([title, body_text, reply_text]))[:26000],
            "researchLabels": labels,
            "researchQuality": "full-text" if body_text or reply_text else "metadata",
            "url": _web_link(
                item,
                f"https://sejm.gov.pl/sejm10.nsf/interpelacja.xsp?typ={'zap' if source_type == 'writtenQuestions' else 'int'}&nr={num}",
            ),
        }
    )
    return item


def research_questions(
    source_type: str,
    date_from: str,
    date_to: str,
    scope: str,
    term: int,
    max_enrich: int,
) -> tuple[list[dict], dict]:
    endpoint = f"{SEJM_API}/term{term}/{source_type}"
    new_items = fetch_paginated_array(
        endpoint,
        {"since": date_from, "till": date_to, "sort_by": "-sentDate"},
    )
    changed_items = fetch_paginated_array(
        endpoint,
        {"modifiedSince": f"{date_from}T00:00", "sort_by": "-lastModified"},
    )
    combined = {}
    for record in [*new_items, *changed_items]:
        if record.get("num") is not None:
            combined[str(record["num"])] = record
    within_window = []
    for record in combined.values():
        new_event_dates = [
            _date_part(record.get(field))
            for field in ("sentDate", "receiptDate")
            if _in_window(record.get(field), date_from, date_to)
        ]
        recent_replies = [
            reply
            for reply in record.get("replies") or []
            if isinstance(reply, dict)
            and any(_in_window(reply.get(field), date_from, date_to) for field in ("lastModified", "receiptDate"))
        ]
        reply_event_dates = [
            _date_part(reply.get(field))
            for reply in recent_replies
            for field in ("lastModified", "receiptDate")
            if _in_window(reply.get(field), date_from, date_to)
        ]
        if not new_event_dates and not reply_event_dates:
            continue
        has_substantive_reply = any(not reply.get("prolongation") for reply in recent_replies)
        has_extension = any(bool(reply.get("prolongation")) for reply in recent_replies)
        if new_event_dates and has_substantive_reply:
            event_type = "new-and-answered"
        elif has_substantive_reply:
            event_type = "answer-update"
        elif new_event_dates and has_extension:
            event_type = "new-and-extension"
        elif has_extension:
            event_type = "deadline-extension"
        else:
            event_type = "new"
        event_date = max([*new_event_dates, *reply_event_dates])
        within_window.append({**record, "eventType": event_type, "eventDate": event_date})
    within_window.sort(
        key=lambda value: (
            len(matched_scope_labels(clean_text(value.get("title")), scope)),
            str(value.get("sentDate") or value.get("receiptDate") or value.get("lastModified") or ""),
        ),
        reverse=True,
    )
    enriched = []
    enriched_count = 0
    for record in within_window:
        seed_text = " ".join([clean_text(record.get("title")), *_recipient_names(record)])
        if matched_scope_labels(seed_text, scope) and enriched_count < max_enrich:
            enriched.append(_enrich_question(record, source_type, scope, fetch_content=True))
            enriched_count += 1
        else:
            enriched.append(_enrich_question(record, source_type, scope, fetch_content=False))
    enriched.sort(key=lambda value: str(value.get("lastModified") or value.get("sentDate") or ""), reverse=True)
    return enriched, {
        "checked": len(combined),
        "withinWindow": len(within_window),
        "enriched": enriched_count,
    }


def _attachment_name(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return clean_text(value.get("name") or value.get("fileName"))
    return ""


def choose_print_attachment(attachments) -> str:
    names = [name for name in (_attachment_name(value) for value in attachments or []) if name]
    usable = [name for name in names if not name.lower().endswith((".xades", ".xml", ".sig"))]
    priorities = ("uzas", "osr", "ocena-skutkow", "ocena_skutkow", "projekt")
    for priority in priorities:
        matches = [name for name in usable if priority in normalize_for_match(name).replace(" ", "-")]
        if matches:
            return matches[0]
    supported = [name for name in usable if name.lower().endswith((".docx", ".docm", ".doc", ".pdf"))]
    return supported[0] if supported else ""


def _enrich_print(record: dict, scope: str, term: int) -> dict:
    item = dict(record)
    number = str(item.get("number") or "")
    detail = {}
    attachment_text = ""
    attachment_url = ""
    try:
        detail = fetch_json(f"{SEJM_API}/term{term}/prints/{quote(number, safe='')}")
        if not isinstance(detail, dict):
            detail = {}
    except Exception:
        detail = {}
    if detail:
        item.update(detail)
    attachment = choose_print_attachment(item.get("attachments"))
    if attachment:
        attachment_url = f"{SEJM_API}/term{term}/prints/{quote(number, safe='')}/{quote(attachment, safe='')}"
        try:
            attachment_text, _, attachment_url = extract_document_text(attachment_url)
            attachment_text = clean_text(attachment_text)[:24000]
        except Exception:
            attachment_text = ""
    title = clean_text(item.get("title"))
    item.update(
        {
            "sourceType": "prints",
            "attachmentText": attachment_text,
            "attachmentUrl": attachment_url,
            "summary": _evidence_summary(attachment_text, scope),
            "researchText": clean_text(" ".join([title, attachment_text]))[:26000],
            "researchLabels": matched_scope_labels(" ".join([title, attachment_text]), scope),
            "researchQuality": "full-text" if attachment_text else ("details" if detail else "metadata"),
            "url": f"https://sejm.gov.pl/sejm10.nsf/druk.xsp?nr={number}",
        }
    )
    return item


def research_prints(
    date_from: str,
    date_to: str,
    scope: str,
    term: int,
    max_enrich: int,
) -> tuple[list[dict], dict]:
    raw = fetch_json(f"{SEJM_API}/term{term}/prints")
    if not isinstance(raw, list):
        raise RuntimeError("Expected a prints array")
    within_window = [
        record
        for record in raw
        if isinstance(record, dict)
        and _record_in_window(record, ("deliveryDate", "documentDate", "changeDate"), date_from, date_to)
    ]
    output = []
    enriched_count = 0
    for record in within_window:
        title = clean_text(record.get("title"))
        if matched_scope_labels(title, scope) and enriched_count < max_enrich:
            output.append(_enrich_print(record, scope, term))
            enriched_count += 1
        else:
            output.append(
                {
                    **record,
                    "sourceType": "prints",
                    "attachmentText": "",
                    "summary": "",
                    "researchText": title,
                    "researchLabels": matched_scope_labels(title, scope),
                    "researchQuality": "metadata",
                    "url": f"https://sejm.gov.pl/sejm10.nsf/druk.xsp?nr={record.get('number', '')}",
                }
            )
    output.sort(key=lambda value: str(value.get("changeDate") or value.get("deliveryDate") or ""), reverse=True)
    return output, {
        "checked": len(raw),
        "withinWindow": len(within_window),
        "enriched": enriched_count,
    }


def _enrich_eli(record: dict, scope: str) -> dict:
    item = dict(record)
    eli = str(item.get("ELI") or "")
    title = clean_text(item.get("title"))
    keywords = [clean_text(value) for value in item.get("keywords") or [] if clean_text(value)]
    released_by = [clean_text(value) for value in item.get("releasedBy") or [] if clean_text(value)]
    base_text = " ".join([title, *keywords, *released_by])
    act_text = ""
    text_url = ""
    if item.get("textHTML"):
        text_url = f"{ELI_API}/acts/{eli}/text.html"
        try:
            act_text = fetch_text(text_url)[:24000]
        except Exception:
            act_text = ""
    elif item.get("textPDF"):
        text_url = f"{ELI_API}/acts/{eli}/text.pdf"
    item.update(
        {
            "sourceType": "eli",
            "eli": eli,
            "actText": act_text,
            "textUrl": text_url,
            "summary": _evidence_summary(act_text, scope),
            "researchText": clean_text(" ".join([base_text, act_text]))[:26000],
            "researchLabels": matched_scope_labels(" ".join([base_text, act_text]), scope),
            "researchQuality": "full-text" if act_text else "official-metadata",
            "url": text_url or f"{ELI_API}/acts/{eli}",
        }
    )
    return item


def research_eli(
    date_from: str,
    date_to: str,
    scope: str,
    max_enrich: int,
) -> tuple[list[dict], dict]:
    raw, total_count = fetch_paginated_eli(
        {
            "publisher": "DU",
            "pubDateFrom": date_from,
            "pubDateTo": date_to,
            "sortBy": "promulgation",
            "sortDir": "desc",
        }
    )
    within_window = [
        record for record in raw if _record_in_window(record, ("promulgation",), date_from, date_to)
    ]
    output = []
    enriched_count = 0
    for record in within_window:
        seed = " ".join(
            [
                clean_text(record.get("title")),
                *[clean_text(value) for value in record.get("keywords") or []],
                *[clean_text(value) for value in record.get("releasedBy") or []],
            ]
        )
        if matched_scope_labels(seed, scope) and enriched_count < max_enrich:
            output.append(_enrich_eli(record, scope))
            enriched_count += 1
        else:
            eli = str(record.get("ELI") or "")
            output.append(
                {
                    **record,
                    "sourceType": "eli",
                    "eli": eli,
                    "actText": "",
                    "summary": "",
                    "researchText": seed,
                    "researchLabels": matched_scope_labels(seed, scope),
                    "researchQuality": "metadata",
                    "url": f"{ELI_API}/acts/{eli}/text.pdf" if record.get("textPDF") else f"{ELI_API}/acts/{eli}",
                }
            )
    output.sort(key=lambda value: str(value.get("promulgation") or ""), reverse=True)
    return output, {
        "checked": total_count,
        "withinWindow": len(within_window),
        "enriched": enriched_count,
    }


def research_legal_sources(
    date_from: str,
    date_to: str,
    scope: str = "mnisw",
    term: int = 10,
    max_enrich: int = 20,
) -> dict:
    date_from = _iso_date(date_from)
    date_to = _iso_date(date_to)
    if date_from > date_to:
        raise ValueError("dateFrom must be on or before dateTo")
    if scope not in SCOPE_PATTERNS:
        raise ValueError(f"Unsupported scope: {scope}")
    term = int(term)
    max_enrich = max(1, min(int(max_enrich), 50))

    output = {
        "dateFrom": date_from,
        "dateTo": date_to,
        "scope": scope,
        "term": term,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "interpellations": [],
        "writtenQuestions": [],
        "prints": [],
        "eliActs": [],
        "sources": {},
        "sourceErrors": [],
    }

    operations = (
        (
            "interpellations",
            lambda: research_questions("interpellations", date_from, date_to, scope, term, max_enrich),
        ),
        (
            "writtenQuestions",
            lambda: research_questions("writtenQuestions", date_from, date_to, scope, term, max_enrich),
        ),
        ("prints", lambda: research_prints(date_from, date_to, scope, term, max_enrich)),
        ("eliActs", lambda: research_eli(date_from, date_to, scope, max_enrich)),
    )
    for name, operation in operations:
        try:
            items, stats = operation()
            output[name] = items
            output["sources"][name] = {**stats, "error": None}
        except Exception as exc:
            error = {"source": name, "message": clean_text(str(exc)) or exc.__class__.__name__}
            output["sources"][name] = {"checked": 0, "withinWindow": 0, "enriched": 0, "error": error}
            output["sourceErrors"].append(error)

    output["status"] = "partial_error" if output["sourceErrors"] else "ok"
    return output
