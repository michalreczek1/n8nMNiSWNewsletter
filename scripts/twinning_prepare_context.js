const MAX_CONTEXT_CHARS = 9000;
const LISTING_LIMIT = 1600;

const clean = (value) => String(value || "")
  .replace(/\r/g, "")
  .replace(/[\t ]+/g, " ")
  .replace(/\n{3,}/g, "\n\n")
  .trim();

const clip = (value, limit) => {
  const text = clean(value);
  if (text.length <= limit) return text;
  const boundary = Math.max(text.lastIndexOf(" ", limit - 80), Math.floor(limit * 0.75));
  return text.slice(0, boundary > 0 ? boundary : limit).trimEnd() + " [truncated]";
};

const splitLong = (value, size = 1100) => {
  const text = clean(value);
  const parts = [];
  for (let start = 0; start < text.length;) {
    let end = Math.min(start + size, text.length);
    if (end < text.length) {
      const space = text.lastIndexOf(" ", end);
      if (space > start + Math.floor(size * 0.55)) end = space;
    }
    parts.push(text.slice(start, end).trim());
    start = end;
    while (text[start] === " ") start += 1;
  }
  return parts.filter(Boolean);
};

const relevantChunks = (value, budget) => {
  const normalized = clean(value);
  if (!normalized) return "";
  const paragraphs = normalized.split(/\n{2,}/).flatMap((part) => splitLong(part));
  const chunks = (paragraphs.length ? paragraphs : splitLong(normalized)).map((text, index) => ({ text, index }));
  const keywords = /resident twinning adviser|\brta\b|project leader|component leader|short[- ]term|\bste\b|expert|profile|qualification|experience|years? of|degree|education|language|english|cv|mandatory|required|minimum|eligib|selection|twinning fiche|work plan|result|activity|budget|duration|mission|beneficiary|digital|cyber|information system|data|e-?government|education|university|research|science|public administration|administrative|legal|legislation|regulation|anti-?corruption|process|project management/gi;
  for (const chunk of chunks) {
    const matches = chunk.text.match(keywords) || [];
    chunk.score = matches.length * 8 + (chunk.index < 3 ? 3 : 0) + (chunk.text.length > 220 ? 1 : 0);
  }
  const selected = [];
  let used = 0;
  for (const chunk of [...chunks].sort((a, b) => b.score - a.score || a.index - b.index)) {
    if (!chunk.score && selected.length >= 2) continue;
    const extra = chunk.text.length + (selected.length ? 2 : 0);
    if (used + extra > budget) continue;
    selected.push(chunk);
    used += extra;
  }
  if (!selected.length) return clip(normalized, budget);
  return selected.sort((a, b) => a.index - b.index).map((chunk) => chunk.text).join("\n\n");
};

return $input.all().map((item) => {
  const source = item.json;
  const header = [
    "SOURCE: official MSZ announcement and Twinning fiche.",
    source.title ? "TITLE: " + source.title : "",
    source.country ? "COUNTRY: " + source.country : "",
    source.area ? "AREA: " + source.area : "",
    source.reference ? "FICHE REFERENCE: " + source.reference : "",
    source.mszDeadline ? "MSZ DEADLINE: " + source.mszDeadline : "",
    source.beneficiaryDeadline ? "BENEFICIARY DEADLINE: " + source.beneficiaryDeadline : "",
  ].filter(Boolean).join("\n");
  const listing = clip(source.pageText, LISTING_LIMIT);
  const availableForFiche = Math.max(2800, MAX_CONTEXT_CHARS - header.length - listing.length - 100);
  const fiche = relevantChunks(source.analysisText, availableForFiche);
  const analysisContext = [header, listing ? "MSZ ANNOUNCEMENT:\n" + listing : "", fiche ? "RELEVANT FICHE EXCERPTS:\n" + fiche : ""]
    .filter(Boolean)
    .join("\n\n")
    .slice(0, MAX_CONTEXT_CHARS);

  return {
    json: {
      ...source,
      analysisContext,
      analysisContextStats: {
        sourceChars: clean(source.pageText).length + clean(source.analysisText).length,
        contextChars: analysisContext.length,
        maxContextChars: MAX_CONTEXT_CHARS,
      },
    },
  };
});
