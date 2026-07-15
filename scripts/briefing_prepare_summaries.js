function cleanText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function shorten(value, maxLength) {
  const text = cleanText(value);
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength).replace(/\s+\S*$/, '').replace(/[,:;\-–—\s]+$/, '')}...`;
}

function compactQuestion(item, kind) {
  return {
    id: String(item.num || item.url || ''),
    kind,
    title: cleanText(item.title),
    recipients: Array.isArray(item.recipients) ? item.recipients.map(cleanText).filter(Boolean) : [],
    questionText: shorten(item.bodyText || item.summary || '', 7000),
    replyStatus: cleanText(item.replyStatus || 'no-answer'),
    replyAuthor: cleanText(item.replyAuthor),
    replyDate: cleanText(item.replyDate),
    replyText: shorten(item.replyText || item.replySummary || '', 7000),
  };
}

const data = $json;
const questions = [
  ...(Array.isArray(data.interpelacje) ? data.interpelacje.map(item => compactQuestion(item, 'interpelacja')) : []),
  ...(Array.isArray(data.zapytania) ? data.zapytania.map(item => compactQuestion(item, 'zapytanie poselskie')) : []),
];

return [{
  json: {
    ...data,
    summaryInput: JSON.stringify({ questions }),
  },
}];
