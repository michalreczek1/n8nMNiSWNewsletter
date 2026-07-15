function cleanText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function shorten(value, maxLength = 1000) {
  const text = cleanText(value);
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength).replace(/\s+\S*$/, '').replace(/[,:;\-–—\s]+$/, '')}...`;
}

function usableSummary(value) {
  const text = cleanText(value);
  if (text.length < 25) return '';
  if (/^(brak|nie podano|nie wiadomo)\.?$/i.test(text)) return '';
  return shorten(text);
}

function fallbackQuestion(item) {
  const source = usableSummary(item.summary);
  if (source) return source;
  const topic = cleanText(item.title)
    .replace(/^(interpelacja|zapytanie)\s+w\s+sprawie\s+/i, '')
    .replace(/[.\s]+$/, '');
  return topic ? `Pytanie poselskie dotyczy ${topic}.` : 'API Sejmu nie udostępniło treści pozwalającej na rzetelne podsumowanie pytania.';
}

function answerStatusSummary(item, aiSummary) {
  const author = cleanText(item.replyAuthor) || 'Organ wskazany jako adresat';
  if (item.replyStatus === 'deadline-extension') {
    return `${author} przedłużył termin udzielenia odpowiedzi. Odpowiedź merytoryczna nie została jeszcze opublikowana.`;
  }
  if (item.replyStatus === 'no-answer') {
    return 'Odpowiedź organu nie została jeszcze opublikowana.';
  }
  if (item.replyStatus === 'unreadable-answer') {
    return `${author} opublikował odpowiedź, ale API Sejmu nie udostępniło jej w postaci pozwalającej na rzetelne podsumowanie.`;
  }
  return usableSummary(aiSummary) || usableSummary(item.replySummary) || `${author} opublikował odpowiedź, lecz nie udało się przygotować jej rzetelnego streszczenia.`;
}

const payload = $json;
const extracted = payload.output && typeof payload.output === 'object' ? payload.output : {};
const rows = Array.isArray(extracted.summaries) ? extracted.summaries : [];
const byId = new Map(rows.map(row => [String(row?.id || ''), row || {}]));

function apply(items) {
  return (Array.isArray(items) ? items : []).map(item => {
    const ai = byId.get(String(item.num || item.url || '')) || {};
    const questionSummary = usableSummary(ai.questionSummary) || fallbackQuestion(item);
    const answerSummary = answerStatusSummary(item, ai.answerSummary);
    return {
      ...item,
      questionSummary,
      answerSummary,
      summary: questionSummary,
      replySummary: item.replyStatus === 'answered' ? answerSummary : '',
      summarySource: usableSummary(ai.questionSummary) ? 'ai-grounded' : 'source-fallback',
    };
  });
}

const result = {
  ...payload,
  interpelacje: apply(payload.interpelacje),
  zapytania: apply(payload.zapytania),
};
delete result.output;
delete result.summaryInput;
delete result.error;
delete result.message;

return [{ json: result }];
