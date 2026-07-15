const sourceItems = $items('Przygotuj URL-e zrodel').map((item) => item.json);
const baseResponses = $items('Pobierz zrodla');
const detailSourceItems = $items('Przygotuj URL-e glosowan').map((item) => item.json);
const detailResponses = $items('Pobierz szczegoly glosowan');
const dateContext = sourceItems[0]?.dateContext || detailSourceItems[0]?.dateContext;
const inRange = (value) => {
  const d = String(value || '').slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(d) && d >= dateContext.dateFrom && d <= dateContext.dateTo;
};
const stripHtml = (value) => String(value || '')
  .replace(/<[^>]*>/g, ' ')
  .replace(/&nbsp;/g, ' ')
  .replace(/&oacute;/g, 'ó')
  .replace(/&amp;/g, '&')
  .replace(/&quot;/g, '"')
  .replace(/\s+/g, ' ')
  .trim();
const normalize = (value) => stripHtml(value)
  .toLowerCase()
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .replace(/ł/g, 'l')
  .replace(/[^a-z0-9]+/g, ' ')
  .replace(/\s+/g, ' ')
  .trim();
const exactPatterns = new Set(['ksc', 'nis2', 'dora', 'csirt', 'cert', 'soc', 'rodo', 'gdpr', 'uodo', 'puodo', 'uke', 'ai', 'iot', 'eidas', 'e zdrowie', 'e zdrowia']);
const matchesPattern = (text, pattern) => exactPatterns.has(pattern) ? text.includes(` ${pattern} `) : text.includes(pattern);
const signalDefs = [
  {
    label: 'cyberbezpieczenstwo',
    weight: 6,
    reason: 'Pozycja bezposrednio odnosi sie do cyberbezpieczenstwa, KSC/NIS2, incydentow lub operacyjnej ochrony systemow.',
    patterns: ['cyberbezpieczen', 'cyberatak', 'krajowy system cyberbezpieczenstwa', 'system cyberbezpieczenstwa', 'ksc', 'nis2', 'dora', 'csirt', 'cert', 'soc', 'incydent cyber', 'ransomware', 'malware', 'phishing', 'haker', 'infrastruktura krytyczna']
  },
  {
    label: 'ochrona danych',
    weight: 5,
    reason: 'Pozycja dotyczy ochrony danych osobowych, prywatnosci, RODO/UODO albo odpowiedzialnosci za przetwarzanie danych.',
    patterns: ['dane osobowe', 'ochrona danych', 'rodo', 'gdpr', 'uodo', 'puodo', 'prywatnosc', 'prywatnosci']
  },
  {
    label: 'telekomunikacja i lacznosc',
    weight: 5,
    reason: 'Pozycja dotyczy infrastruktury telekomunikacyjnej, lacznosci, urzadzen nadawczych lub regulacji UKE, co ma znaczenie dla odpornosci komunikacji publicznej.',
    patterns: ['telekomunikac', 'urzadzen telekomunikacyjnych', 'radiowych urzadzen nadawczych', 'nadawczo odbiorczych', 'lacznosc satelitarna', 'laczności satelitarnej', 'uke', 'widmo radiowe', 'czestotliwosci radiowych']
  },
  {
    label: 'cyfryzacja administracji',
    weight: 5,
    reason: 'Pozycja dotyczy cyfryzacji uslug publicznych, e-administracji, podpisu elektronicznego, eIDAS, e-doreczen lub profilu zaufanego.',
    patterns: ['transformacja cyfrowa', 'cyfryzacja uslug publicznych', 'cyfryzacja administracji', 'cyfrowe uslugi publiczne', 'informatyzacja administracji publicznej', 'e administracja', 'e uslug', 'usluga cyfrowa', 'mobywatel', 'e doreczen', 'edoreczen', 'eidas', 'podpis elektroniczny', 'profil zaufany', 'identyfikacja elektroniczna']
  },
  {
    label: 'systemy informatyczne i rejestry',
    weight: 5,
    reason: 'Pozycja dotyczy systemow informatycznych, rejestrow publicznych, baz danych lub interoperacyjnosci uslug panstwa.',
    patterns: ['teleinformatycz', 'system informatyczny', 'systemy informatyczne', 'system informacji', 'rejestr publiczny', 'rejestry publiczne', 'baza danych', 'bazy danych', 'interoperacyjnosc']
  },
  {
    label: 'e-zdrowie',
    weight: 5,
    reason: 'Pozycja dotyczy cyfrowych procesow ochrony zdrowia lub danych medycznych, czyli obszaru o wysokich wymaganiach bezpieczenstwa informacji.',
    patterns: ['cyfrowej ochrony zdrowia', 'cyfryzacji ochrony zdrowia', 'e zdrowie', 'e zdrowia', 'internetowe konto pacjenta', 'dane medyczne', 'dokumentacja medyczna']
  },
  {
    label: 'AI i automatyzacja',
    weight: 5,
    reason: 'Pozycja dotyczy sztucznej inteligencji, AI Act, biometrii, deepfake albo automatyzacji decyzji publicznych.',
    patterns: ['sztuczna inteligencja', 'sztucznej inteligencji', 'artificial intelligence', 'ai act', 'biometr', 'deepfake', 'automatyzacja decyzji', 'automatycznego podejmowania decyzji']
  },
  {
    label: 'aktywa cyfrowe',
    weight: 5,
    reason: 'Pozycja dotyczy aktywow cyfrowych, dostepu do kont lub statusu prawnego danych i zasobow cyfrowych.',
    patterns: ['aktywa cyfrowe', 'aktywow cyfrowych', 'aktywów cyfrowych', 'dziedziczenia aktywow cyfrowych', 'dziedziczenie aktywow cyfrowych']
  },
  {
    label: 'platformy i dezinformacja',
    weight: 4,
    reason: 'Pozycja dotyczy platform internetowych, mediow spolecznosciowych lub dezinformacji, czyli obszaru bezpieczenstwa informacji publicznej.',
    patterns: ['platforma internetowa', 'platformy internetowe', 'media spolecznosciowe', 'dezinformac']
  }
].map((signal) => ({ ...signal, normalized: signal.patterns.map(normalize).filter(Boolean) }));
const relevance = (...parts) => {
  const text = ` ${normalize(parts.filter(Boolean).join(' '))} `;
  const hits = [];
  for (const signal of signalDefs) {
    if (signal.normalized.some((pattern) => matchesPattern(text, pattern))) hits.push(signal);
  }
  const score = hits.reduce((sum, hit) => sum + hit.weight, 0);
  if (!hits.length) return null;
  return {
    score,
    labels: hits.map((hit) => hit.label),
    reason: hits.map((hit) => hit.reason).filter((reason, index, arr) => arr.indexOf(reason) === index).join(' '),
    patterns: hits.flatMap((hit) => hit.normalized)
  };
};
const relevantRows = (items, partsFn, minScore = 4) => items
  .map((item) => ({ item, rel: relevance(...partsFn(item)) }))
  .filter(({ rel }) => rel && rel.score >= minScore);
const asItems = (payload) => {
  if (Array.isArray(payload)) return payload;
  if (payload && Array.isArray(payload.items)) return payload.items;
  if (payload && Array.isArray(payload.data)) return payload.data;
  return payload ? [payload] : [];
};
const firstLink = (links, rel) => {
  if (!Array.isArray(links)) return '';
  const hit = links.find((link) => link.rel === rel) || links[0];
  return hit?.href || '';
};
const uniqBy = (items, keyFn) => {
  const seen = new Set();
  return items.filter((item) => {
    const key = keyFn(item);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
};
const relevantExcerpt = (value, rel, maxLength = 900) => {
  const text = stripHtml(value);
  if (!text) return '';
  const patterns = Array.isArray(rel?.patterns) ? rel.patterns : [];
  const chunks = text
    .split(/(?<=[.!?])\s+|\s+[–—]\s+/)
    .map((part) => part.trim())
    .filter(Boolean);
  const matched = chunks.filter((part) => {
    const normalized = ` ${normalize(part)} `;
    return patterns.some((pattern) => matchesPattern(normalized, pattern));
  });
  if (matched.length) return matched.slice(0, 3).join(' ').slice(0, maxLength);
  const normalizedText = ` ${normalize(text)} `;
  const indexes = patterns.map((pattern) => normalizedText.indexOf(pattern)).filter((index) => index >= 0);
  if (!indexes.length) return text.slice(0, maxLength);
  const start = Math.max(0, Math.min(...indexes) - 250);
  return text.slice(start, start + maxLength).replace(/^\S*\s/, '').trim();
};
const pairedIndex = (item, fallback) => {
  const paired = item?.pairedItem;
  if (Array.isArray(paired)) return paired[0]?.item ?? fallback;
  return paired?.item ?? fallback;
};
const payloads = { prints: [], interpellations: [], writtenQuestions: [], proceedings: [], votingDays: [], committees: [], eli: [], votingDetails: [] };
const errors = [];
for (let i = 0; i < baseResponses.length; i += 1) {
  const meta = sourceItems[pairedIndex(baseResponses[i], i)] || {};
  const payload = baseResponses[i]?.json;
  if (!payload || payload.error || payload.statusCode >= 400) {
    errors.push({ source: meta.source || `base-${i}`, url: meta.url, error: payload?.message || payload?.error || `HTTP ${payload?.statusCode || 'unknown'}` });
    continue;
  }
  if (meta.kind === 'prints') payloads.prints.push(...asItems(payload));
  if (meta.kind === 'interpellations') payloads.interpellations.push(...asItems(payload));
  if (meta.kind === 'writtenQuestions') payloads.writtenQuestions.push(...asItems(payload));
  if (meta.kind === 'proceedings') payloads.proceedings.push(...asItems(payload));
  if (meta.kind === 'voting-days') payloads.votingDays.push(...asItems(payload));
  if (meta.kind === 'committees') payloads.committees.push(...asItems(payload));
  if (meta.kind === 'eli') payloads.eli.push(...asItems(payload));
}
for (let i = 0; i < detailResponses.length; i += 1) {
  const meta = detailSourceItems[pairedIndex(detailResponses[i], i)] || {};
  const payload = detailResponses[i]?.json;
  if (meta.kind === 'noop') continue;
  if (!payload || payload.error || payload.statusCode >= 400) {
    errors.push({ source: meta.source || `detail-${i}`, url: meta.url, error: payload?.message || payload?.error || `HTTP ${payload?.statusCode || 'unknown'}` });
    continue;
  }
  payloads.votingDetails.push(...asItems(payload));
}
const recentChange = (item) => inRange(item.lastModified) || inRange(item.receiptDate) || inRange(item.sentDate) || (Array.isArray(item.replies) && item.replies.some((reply) => inRange(reply.lastModified) || inRange(reply.receiptDate)));
const countRecentReplies = (item) => Array.isArray(item.replies) ? item.replies.filter((reply) => inRange(reply.lastModified) || inRange(reply.receiptDate)).length : 0;
const questionEventDate = (item) => {
  const replyDates = Array.isArray(item.replies)
    ? item.replies.flatMap((reply) => [reply.lastModified, reply.receiptDate]).filter(inRange)
    : [];
  return [...replyDates, item.lastModified, item.receiptDate, item.sentDate].filter(inRange).sort().at(-1) || '';
};
const uniquePrints = uniqBy(payloads.prints, (p) => String(p.number || p.num || `${p.title}-${p.deliveryDate}`));
const uniqueInterpellations = uniqBy(payloads.interpellations, (i) => String(i.num || `${i.title}-${i.sentDate}`));
const uniqueWrittenQuestions = uniqBy(payloads.writtenQuestions, (q) => String(q.num || `${q.title}-${q.sentDate}`));
const uniqueActs = uniqBy(payloads.eli, (act) => String(act.ELI || act.displayAddress || `${act.title}-${act.promulgation}`));
const filteredPrints = relevantRows(uniquePrints.filter((p) => inRange(p.deliveryDate || p.documentDate)), (p) => [p.title, p.description, p.documentType])
  .sort((a, b) => String(b.item.deliveryDate || b.item.documentDate || '').localeCompare(String(a.item.deliveryDate || a.item.documentDate || '')))
  .slice(0, 16)
  .map(({ item: p, rel }) => ({ type: 'Druk sejmowy', title: stripHtml(p.title) || 'Brak tytulu', number: p.number || p.num || '', date: String(p.deliveryDate || p.documentDate || '').slice(0, 10), reason: rel.reason, signals: rel.labels, meta: [p.documentType || p.type || '', p.number ? `druk ${p.number}` : ''].filter(Boolean).join(' | '), url: p.number ? `https://www.sejm.gov.pl/Sejm10.nsf/druk.xsp?nr=${encodeURIComponent(p.number)}` : 'https://www.sejm.gov.pl/Sejm10.nsf/druki.xsp' }));
// Adresat (np. Minister Cyfryzacji) nie jest sam w sobie dowodem trafnosci.
// Interpelacje i zapytania musza miec sygnal tematyczny w tytule.
const filteredInterpellations = relevantRows(uniqueInterpellations.filter(recentChange), (i) => [i.title])
  .sort((a, b) => questionEventDate(b.item).localeCompare(questionEventDate(a.item)))
  .slice(0, 14)
  .map(({ item: i, rel }) => ({ type: 'Interpelacja', title: stripHtml(i.title) || 'Brak tytulu', number: i.num || '', date: questionEventDate(i), reason: rel.reason, signals: rel.labels, meta: [`nr ${i.num || '?'}`, countRecentReplies(i) ? `${countRecentReplies(i)} nowe odpowiedzi/zmiany` : '', Array.isArray(i.to) ? i.to.join(', ') : ''].filter(Boolean).join(' | '), url: firstLink(i.links, 'web-description') }));
const filteredWrittenQuestions = relevantRows(uniqueWrittenQuestions.filter(recentChange), (q) => [q.title])
  .sort((a, b) => questionEventDate(b.item).localeCompare(questionEventDate(a.item)))
  .slice(0, 14)
  .map(({ item: q, rel }) => ({ type: 'Zapytanie poselskie', title: stripHtml(q.title) || 'Brak tytulu', number: q.num || '', date: questionEventDate(q), reason: rel.reason, signals: rel.labels, meta: [`nr ${q.num || '?'}`, countRecentReplies(q) ? `${countRecentReplies(q)} nowe odpowiedzi/zmiany` : '', Array.isArray(q.to) ? q.to.join(', ') : ''].filter(Boolean).join(' | '), url: firstLink(q.links, 'web-description') }));
const filteredActs = relevantRows(uniqueActs.filter((act) => inRange(act.promulgation)), (act) => [act.title, act.type, Array.isArray(act.keywords) ? act.keywords.join(' ') : act.keywords, act.subject])
  .sort((a, b) => String(b.item.promulgation || '').localeCompare(String(a.item.promulgation || '')))
  .slice(0, 14)
  .map(({ item: act, rel }) => ({ type: act.publisher === 'MP' ? 'Monitor Polski' : 'Dziennik Ustaw', title: stripHtml(act.title) || 'Brak tytulu', number: act.displayAddress || act.ELI || '', date: String(act.promulgation || '').slice(0, 10), reason: rel.reason, signals: rel.labels, meta: [act.displayAddress || act.ELI, act.type, act.status].filter(Boolean).join(' | '), url: act.ELI ? `https://api.sejm.gov.pl/eli/acts/${act.ELI}/text.pdf` : 'https://api.sejm.gov.pl/eli' }));
const filteredCommittees = relevantRows(payloads.committees.filter((s) => inRange(s.date || s.startDateTime)), (s) => [s.agenda, s.video?.map((v) => `${v.title} ${v.description}`).join(' ')])
  .sort((a, b) => String(b.item.startDateTime || b.item.date || '').localeCompare(String(a.item.startDateTime || a.item.date || '')))
  .slice(0, 14)
  .map(({ item: s, rel }) => ({ type: s.video?.[0]?.type || 'Komisja/podkomisja', title: stripHtml(s.video?.[0]?.title || s.code || `Posiedzenie ${s.num || ''}`), number: [s.code, s.num ? `nr ${s.num}` : ''].filter(Boolean).join(' '), date: String(s.startDateTime || s.date || '').slice(0, 10), reason: rel.reason, signals: rel.labels, meta: [s.room, s.status, s.remote ? 'zdalne' : 'stacjonarne'].filter(Boolean).join(' | '), body: relevantExcerpt(s.agenda || s.video?.[0]?.description || '', rel), url: s.video?.[0]?.playerLink || 'https://www.sejm.gov.pl/Sejm10.nsf/agent.xsp?symbol=KOMISJE_STALE' }));
const filteredVotings = relevantRows(payloads.votingDetails.filter((v) => inRange(v.date)), (v) => [v.topic, v.title])
  .sort((a, b) => String(b.item.date || '').localeCompare(String(a.item.date || '')))
  .slice(0, 12)
  .map(({ item: v, rel }) => ({ type: 'Glosowanie', title: stripHtml(v.topic || v.title || 'Glosowanie'), number: v.votingNumber ? `nr ${v.votingNumber}` : '', date: String(v.date || '').slice(0, 10), reason: rel.reason, signals: rel.labels, meta: [`posiedzenie ${v.sitting || '?'}`, `za ${v.yes ?? 0}`, `przeciw ${v.no ?? 0}`, `wstrz. ${v.abstain ?? 0}`].join(' | '), url: Array.isArray(v.links) ? firstLink(v.links, 'pdf') : '' }));
// Posiedzenie Sejmu jest kontenerem dla wielu niepowiązanych punktów. Do monitora
// trafia tylko wtedy, gdy sam tytuł posiedzenia jest tematyczny; konkretne sprawy
// cyber wyłapują osobno druki, komisje i głosowania.
const recentProceedings = relevantRows(payloads.proceedings.filter((p) => Array.isArray(p.dates) ? p.dates.some(inRange) : inRange(p.date)), (p) => [p.title])
  .sort((a, b) => String((b.item.dates || [b.item.date || ''])[0]).localeCompare(String((a.item.dates || [a.item.date || ''])[0])))
  .slice(0, 8)
  .map(({ item: p, rel }) => ({ type: 'Posiedzenie Sejmu', title: stripHtml(p.title) || `Posiedzenie nr ${p.number || p.num || ''}`, number: p.number || p.num || '', date: Array.isArray(p.dates) ? p.dates.filter(inRange).join(', ') : String(p.date || '').slice(0, 10), reason: rel.reason, signals: rel.labels, meta: Array.isArray(p.dates) ? p.dates.join(', ') : String(p.date || '').slice(0, 10), body: relevantExcerpt(p.title || '', rel) }));
const sections = {
  prints: uniqBy(filteredPrints, (x) => `print-${x.number}-${x.title}`),
  acts: uniqBy(filteredActs, (x) => `act-${x.number}-${x.title}`),
  interpellations: uniqBy(filteredInterpellations, (x) => `int-${x.number}-${x.title}`),
  writtenQuestions: uniqBy(filteredWrittenQuestions, (x) => `zap-${x.number}-${x.title}`),
  committees: uniqBy(filteredCommittees, (x) => `committee-${x.number}-${x.date}-${x.title}`),
  votings: uniqBy(filteredVotings, (x) => `vote-${x.number}-${x.date}-${x.title}`),
  proceedings: recentProceedings
};
return [{
  json: {
    dateContext,
    sections,
    totalFound: Object.values(sections).flat().length,
    stats: {
      rawPrints: payloads.prints.length,
      rawInterpellations: payloads.interpellations.length,
      rawWrittenQuestions: payloads.writtenQuestions.length,
      rawProceedings: payloads.proceedings.length,
      rawVotingDays: payloads.votingDays.length,
      rawVotingDetails: payloads.votingDetails.length,
      rawCommittees: payloads.committees.length,
      rawEliActs: payloads.eli.length,
      prints: sections.prints.length,
      acts: sections.acts.length,
      interpellations: sections.interpellations.length,
      writtenQuestions: sections.writtenQuestions.length,
      committees: sections.committees.length,
      votings: sections.votings.length,
      proceedings: sections.proceedings.length
    },
    errors
  }
}];
