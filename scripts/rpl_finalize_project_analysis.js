function parseDatePL(val) {
  if (!val) return null;
  const s = String(val).trim();
  let m = s.match(/(\d{2})-(\d{2})-(\d{4})/);
  if (!m) m = s.match(/(\d{2})\.(\d{2})\.(\d{4})/);
  return m ? new Date(`${m[3]}-${m[2]}-${m[1]}T00:00:00Z`) : null;
}

function cleanText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function normalizeKeyChanges(value) {
  if (!Array.isArray(value)) return [];
  return value
    .map(v => cleanText(v).replace(/[.;]+$/g, ''))
    .filter(Boolean)
    .slice(0, 4);
}

function normalizeComparable(value) {
  return cleanText(value)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/ł/g, 'l')
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function overlapRatio(summary, title) {
  const summaryTokens = Array.from(new Set(normalizeComparable(summary).split(' ').filter(t => t.length > 3)));
  const titleTokens = Array.from(new Set(normalizeComparable(title).split(' ').filter(t => t.length > 3)));
  if (!summaryTokens.length || !titleTokens.length) return 0;
  const titleSet = new Set(titleTokens);
  const overlap = summaryTokens.filter(token => titleSet.has(token)).length;
  return overlap / Math.max(1, Math.min(summaryTokens.length, titleTokens.length));
}

function looksTitleLike(summary, title) {
  const s = cleanText(summary);
  const t = cleanText(title);
  if (!s) return true;
  const ns = normalizeComparable(s);
  const nt = normalizeComparable(t);
  if (nt && ns.startsWith(nt.slice(0, Math.min(nt.length, 140)))) return true;
  if (/^projekt\s+(ustawy|rozporzadzenia|rozporządzenia|uchwaly|uchwały)\b/i.test(s) && overlapRatio(s, t) >= 0.6) return true;
  return false;
}

function trimSentence(text, maxLen = 520) {
  let s = cleanText(text);
  if (!s) return '';
  if (s.length <= maxLen) return s;
  s = s.slice(0, maxLen).replace(/\s+\S*$/, '');
  return s.replace(/[,:;\-–—\s]+$/, '') + '...';
}

function looksUnreadableSourceText(text) {
  const s = cleanText(text);
  if (!s) return false;
  const normalized = normalizeComparable(s);
  if (/(\/type\s*\/page|\/flatedecode|endobj|xref|obj\s*<<|stream\s+x|microsoft\s+office\s+word|aspose|pk\s*!|<\?xml|xmldsig|<ds:(?:signature|signedinfo|x509certificate))/i.test(s)) return true;
  if (/(type page parent|flatedecode|endobj|mediabox|resources font|producer aspose|creator microsoft office word|xmldsig|signedinfo|signaturevalue|x509certificate)/.test(normalized)) return true;
  const sample = s.slice(0, 500);
  const letters = (sample.match(/[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]/g) || []).length;
  const suspicious = (sample.match(/[{}[\]<>|~^`\\]/g) || []).length;
  return sample.length > 120 && suspicious / sample.length > 0.08 && letters / sample.length < 0.55;
}

function sanitizeFallbackSummary(text) {
  const s = trimSentence(text);
  if (!s || looksUnreadableSourceText(s)) return '';
  if (/^projekt dotyczy:/i.test(s)) return '';
  if (/^nie udało się pobrać/i.test(s)) return '';
  return s;
}

function lowerFirst(text) {
  const s = cleanText(text);
  if (!s) return '';
  return s.charAt(0).toLowerCase() + s.slice(1);
}

function ensureSentence(text) {
  const s = cleanText(text).replace(/[.;:,\s]+$/, '');
  if (!s) return '';
  return /[.!?]$/.test(s) ? s : `${s}.`;
}

function genericPhraseHits(text) {
  const summary = normalizeComparable(text);
  if (!summary) return 0;
  const phrases = [
    'wprowadza nowe rozwiazania',
    'ma na celu poprawe',
    'ma na celu wprowadzenie zmian',
    'ma na celu zmiane',
    'ma wplynac na',
    'usprawnienie systemu',
    'najwazniejsze zmiany dotycza',
    'w tym zakresie',
    'poprawe jakosci i dostepnosci',
    'projekt ten ma na celu',
    'projekt ten wprowadza',
    'projekt ma rowniez na celu'
  ];
  return phrases.filter(p => summary.includes(p)).length;
}

function hasConcreteSignals(text) {
  const summary = cleanText(text);
  if (!summary) return false;
  if (/\d/.test(summary)) return true;
  return /(fundusz|program|tabel|stawk|warto(?:ść|sci)|limit|warun(?:ek|ki)|beneficjent|organizacj(?:e|i)|hospitalizac|weekend|paszport|dow[oó]d|o[łl]ow|termomoderniz|stop smog|po[żz]ytku publicznego|świadcze|personel|dokument publiczn|nara[żz]eni|krwi|komisji|wynagrodze[nń])/i.test(summary);
}

function looksTooGeneric(summary, keyChanges) {
  const text = cleanText(summary);
  if (!text) return true;
  const hits = genericPhraseHits(text);
  const concrete = hasConcreteSignals(text);
  const hasChanges = normalizeKeyChanges(keyChanges).length > 0;
  if (hits >= 2 && !concrete) return true;
  if (hits >= 1 && !concrete && hasChanges) return true;
  if (/^projekt dotyczy:/i.test(text)) return true;
  return false;
}

function composeSummary(author, keyChanges, fallbackSummary) {
  const changes = normalizeKeyChanges(keyChanges);
  const cleanAuthor = cleanText(author);
  const safeFallback = cleanText(fallbackSummary);
  if (changes.length) {
    const first = lowerFirst(changes[0]);
    const rest = changes.slice(1, 3).map(lowerFirst);
    const intro = cleanAuthor
      ? ensureSentence(`${cleanAuthor} przygotował projekt, który przewiduje ${first}`)
      : ensureSentence(`Projekt przewiduje ${first}`);
    let second = '';
    if (rest.length === 1) {
      second = ensureSentence(`Dodatkowo projekt obejmuje ${rest[0]}`);
    } else if (rest.length > 1) {
      second = ensureSentence(`Dodatkowo projekt obejmuje ${rest.join(' oraz ')}`);
    }
    if (safeFallback && !looksTitleLike(safeFallback, '') && !looksTooGeneric(safeFallback, [])) {
      const fallbackSentence = ensureSentence(safeFallback);
      return trimSentence([intro, second, fallbackSentence].filter(Boolean).join(' '));
    }
    return trimSentence([intro, second].filter(Boolean).join(' '));
  }
  if (cleanAuthor && safeFallback) {
    return trimSentence(`Autorem projektu jest ${cleanAuthor}. ${safeFallback}`);
  }
  return trimSentence(safeFallback);
}

function ensureAuthor(summary, author) {
  const cleanAuthor = cleanText(author);
  if (!summary || !cleanAuthor) return summary;
  const normalizedSummary = normalizeComparable(summary);
  const normalizedAuthor = normalizeComparable(cleanAuthor);
  if (normalizedSummary.includes(normalizedAuthor)) return summary;
  return trimSentence(`Autorem projektu jest ${cleanAuthor}. ${summary}`);
}

function collectPatternHits(text, patterns) {
  const hits = [];
  let score = 0;
  for (const pattern of patterns) {
    if (pattern.re.test(text)) {
      hits.push(pattern);
      score += pattern.weight;
    }
  }
  return { hits, score };
}

function combinePatternHits(...groups) {
  const seen = new Set();
  const hits = [];
  let score = 0;
  for (const group of groups) {
    for (const hit of group.hits) {
      if (seen.has(hit.label)) continue;
      seen.add(hit.label);
      hits.push(hit);
      score += hit.weight;
    }
  }
  return { hits, score };
}

const payload = $json;
if (!payload || !payload.url) return { json: {} };

const aiErrorMessage = cleanText(payload.error || payload.message || '');
const ai = payload.output && typeof payload.output === 'object' ? payload.output : null;
const rawAiSummary = cleanText(ai?.summary || '');
const aiAuthor = cleanText(ai?.author || '');
const rawAiKeyChanges = normalizeKeyChanges(ai?.keyChanges);
const aiSourceQuality = cleanText(ai?.sourceQuality || '');

const fallbackSummary = sanitizeFallbackSummary(payload.fallbackSummary || payload.summary);
const fallbackUnavailableSummary = 'Brak czytelnego streszczenia w źródłowym dokumencie.';
const applicant = cleanText(payload.applicant || aiAuthor);
const hasReadableSourceEvidence = Boolean(
  fallbackSummary &&
  payload.summarySource === 'justification-doc' &&
  !looksUnreadableSourceText(payload.analysisText || fallbackSummary)
);
const aiMarkedLowQuality = normalizeComparable(aiSourceQuality) === 'low';
const allowAiClaims = hasReadableSourceEvidence && !aiMarkedLowQuality;
const aiKeyChanges = allowAiClaims ? rawAiKeyChanges : [];
let aiSummary = allowAiClaims && rawAiSummary && !looksTitleLike(rawAiSummary, payload.title) ? trimSentence(rawAiSummary) : '';
if (aiSummary && looksTooGeneric(aiSummary, aiKeyChanges)) {
  aiSummary = '';
}
let summary = aiSummary || composeSummary(applicant || aiAuthor, aiKeyChanges, fallbackSummary);
summary = ensureAuthor(summary || fallbackSummary || fallbackUnavailableSummary, applicant || aiAuthor);
summary = trimSentence(summary || fallbackSummary || fallbackUnavailableSummary);

const primaryEvidenceTextForAnalysis = normalizeComparable([
  payload.title || '',
  applicant || '',
  payload.stage || '',
  payload.projectType || '',
  fallbackSummary || ''
].join(' '));

const extendedEvidenceTextForAnalysis = normalizeComparable(payload.analysisText || '');

const positivePatterns = [
  { label: 'higher-education-law', weight: 5, re: /\bprawo\s+o\s+szkolnictw\w*\s+wyzsz\w*\s+i\s+nauce\b/ },
  { label: 'higher-education', weight: 4, re: /\bszkolnictw\w*\s+wyzsz\w*\b|\bksztalceni\w*\s+wyzsz\w*\b/ },
  { label: 'university', weight: 3, re: /\buczelni\w*\b|\bszkol\w*\s+wyzsz\w*\b/ },
  { label: 'student-affairs', weight: 3, re: /\bstuden\w*\b|\bstypendi\w*\s+studen\w*\b/ },
  { label: 'doctoral-affairs', weight: 3, re: /\bdoktoran\w*\b|\bdoktorat\w*\b|\bdoktora\b|\bdoktorem\b/ },
  { label: 'science-policy', weight: 3, re: /\bbadan\w*\s+naukow\w*\b|\bdzialalnos\w*\s+naukow\w*\b|\bpracownik\w*\s+naukow\w*\b|\bstopni\w*\s+naukow\w*\b|\bewaluacj\w*\s+jakosci\s+dzialalnos\w*\s+naukow\w*\b/ },
  { label: 'science-institutions', weight: 4, re: /\bpolsk\w*\s+akademi\w*\s+nauk\w*\b|\bpan\b|\bnarodow\w*\s+centrum\s+nauk\w*\b|\bncn\b|\bnarodow\w*\s+centrum\s+badan\w*\s+i\s+rozwoju\b|\bncbir\b|\bnawa\b|\bpolsk\w*\s+komisj\w*\s+akredytacyj\w*\b|\bpol\s+on\b|\bpolon\b/ }
];
const highConfidenceExtendedPatterns = positivePatterns.filter(pattern =>
  ['higher-education-law', 'higher-education'].includes(pattern.label)
);
const supportingPatterns = [
  { label: 'science-wording', weight: 1, re: /\bnauk\w*\b/ },
  { label: 'academic-wording', weight: 1, re: /\bakademick\w*\b/ },
  { label: 'rectors', weight: 1, re: /\brektor\w*\b/ },
  { label: 'research-support', weight: 1, re: /\bgrant\w*\b|\blaboratori\w*\b|\btransfer\s+technologii\b|\bstartup\s+akademick\w*\b/ }
];
const negativePatterns = [
  { label: 'school-education', weight: -3, re: /\bszkol\w*\s+podstawow\w*\b|\bprzedszkol\w*\b|\bzlob\w*\b|\blice\w*\b|\btechnik\w*\b|\bmatur\w*\b|\begzamin\w*\s+osmoklasist\w*\b|\bszkol\w*\s+branzow\w*\b/ }
];

const directApplicant = /\bminister\s+nauki\b|\bministerstwo\s+nauki\b|\bminister\s+nauki\s+i\s+szkolnictwa\s+wyzszego\b/.test(normalizeComparable(applicant));
const positive = combinePatternHits(
  collectPatternHits(primaryEvidenceTextForAnalysis, positivePatterns),
  collectPatternHits(extendedEvidenceTextForAnalysis, highConfidenceExtendedPatterns)
);
const supporting = collectPatternHits(primaryEvidenceTextForAnalysis, supportingPatterns);
const negative = collectPatternHits(primaryEvidenceTextForAnalysis, negativePatterns);

let score = positive.score + supporting.score + negative.score;
if (directApplicant) score += 6;

const created = parseDatePL(payload.dateCreated);
const now = new Date();
const ageDays = created ? Math.floor((now - created) / 86400000) : null;
const daysLookback = Number(payload.daysLookback || 14);
const withinLookback = ageDays === null ? true : ageDays <= daysLookback;

const threshold = Number(payload.scoreThreshold || 4);
const hasCoreEvidence = directApplicant || positive.hits.length > 0;
const isRelevant = score >= threshold && hasCoreEvidence;

const staticData = $getWorkflowStaticData('global');
if (!staticData.sentProjects) staticData.sentProjects = {};
if (!Array.isArray(staticData.currentRunProjects)) staticData.currentRunProjects = [];

const projectId = payload.projectId || payload.url;
const fingerprint = [payload.title || '', payload.dateUpdated || '', payload.stage || '', payload.documentUrl || '', summary].join('|');
const alreadySent = staticData.sentProjects[projectId] && staticData.sentProjects[projectId].fingerprint === fingerprint;
const includeInMain = withinLookback && isRelevant && !alreadySent;

const labels = new Set(positive.hits.map(h => h.label));
const why = [];
if (directApplicant) why.push('wnioskodawcą jest Minister Nauki lub Minister Nauki i Szkolnictwa Wyższego');
if (labels.has('higher-education-law')) why.push('projekt odwołuje się do ustawy Prawo o szkolnictwie wyższym i nauce');
if (labels.has('higher-education')) why.push('projekt wpływa na szkolnictwo wyższe');
if (labels.has('university')) why.push('projekt dotyczy uczelni lub szkół wyższych');
if (labels.has('student-affairs')) why.push('projekt dotyczy studentów lub spraw studenckich');
if (labels.has('doctoral-affairs')) why.push('projekt dotyczy doktorantów, doktoratów lub stopni doktora');
if (labels.has('science-policy')) why.push('projekt zawiera źródłowe odniesienia do badań, działalności lub stopni naukowych');
if (labels.has('science-institutions')) why.push('projekt dotyczy instytucji systemu nauki i szkolnictwa wyższego');
if (!why.length) why.push('projekt nie spełnił szczególnych kryteriów MNiSW, ale został ujęty w przeglądzie RCL');

if (includeInMain) {
  staticData.sentProjects[projectId] = {
    fingerprint,
    seenAt: new Date().toISOString()
  };
}

const result = {
  projectId,
  title: payload.title,
  applicant,
  stage: payload.stage,
  number: payload.number,
  projectType: payload.projectType,
  dateCreated: payload.dateCreated,
  dateUpdated: payload.dateUpdated,
  summary,
  fallbackSummary: fallbackSummary || fallbackUnavailableSummary,
  aiSummary,
  aiAuthor,
  keyChanges: aiKeyChanges,
  sourceQuality: !allowAiClaims && (rawAiSummary || rawAiKeyChanges.length)
    ? 'unverified-ai-discarded'
    : (aiSourceQuality || (aiErrorMessage ? 'fallback-after-ai-error' : payload.summarySource || '')),
  groundingStatus: allowAiClaims ? 'source-grounded' : 'source-insufficient',
  whyRelevant: why.join('; '),
  score,
  url: payload.url,
  fromEmail: payload.fromEmail,
  toEmail: payload.toEmail,
  isRelevant,
  withinLookback,
  alreadySent: Boolean(alreadySent),
  includeInMain,
  matchedPositiveLabels: positive.hits.map(h => h.label),
  matchedSupportingLabels: supporting.hits.map(h => h.label),
  matchedNegativeLabels: negative.hits.map(h => h.label),
  summarySource: aiSummary ? 'ai-summary' : (aiErrorMessage ? 'fallback-after-ai-error' : payload.summarySource),
  documentUrl: payload.documentUrl,
  documentLabel: payload.documentLabel,
  aiError: aiErrorMessage || undefined
};

staticData.currentRunProjects.push(result);
return { json: result };
