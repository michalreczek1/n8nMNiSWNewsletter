const SOURCE_LABELS = {
  interpellations: 'Interpelacje Sejmu',
  writtenQuestions: 'Zapytania poselskie',
  prints: 'Druki sejmowe',
  eliActs: 'ELI / Dziennik Ustaw',
  research: 'Helper researchu Sejm / ELI',
};

const SIGNAL_LABELS = {
  'higher-education-law': 'Prawo o szkolnictwie wyższym i nauce',
  'higher-education': 'system szkolnictwa wyższego',
  universities: 'uczelnie',
  students: 'studenci i przebieg studiów',
  doctoral: 'doktoranci, stopnie i habilitacje',
  'academic-staff': 'nauczyciele akademiccy lub pracownicy naukowi',
  'science-policy': 'badania i finansowanie nauki',
  'science-institutions': 'instytucje systemu nauki',
  scholarships: 'stypendia',
  accreditation: 'akredytacja i jakość kształcenia',
  rectors: 'rektorzy',
  'science-wording': 'kontekst nauki',
  'school-education': 'oświata i szkoły poza szkolnictwem wyższym',
  'vocational-schooling': 'szkolnictwo branżowe',
  'labour-market': 'rynek pracy i urzędy pracy',
  'social-policy': 'pomoc społeczna',
};

const COMMON_POSITIVE_RULES = [
  { label: 'higher-education-law', pattern: /\bprawo\s+o\s+szkolnictw\w*\s+wyższ\w*\s+i\s+nauce\b/i, weight: 7 },
  { label: 'higher-education', pattern: /\bszkolnictw\w*\s+wyższ\w*\b|\bkształceni\w*\s+wyższ\w*\b/i, weight: 6 },
  { label: 'universities', pattern: /\buczelni\w*\b|\buniwersytet\w*\b|\bpolitechnik\w*\b|\bszkoł\w*\s+wyższ\w*\b/i, weight: 5 },
  { label: 'students', pattern: /\bstuden\w*\b|\bstudi(?:a|ów|ach|ami|om)\b/i, weight: 5 },
  { label: 'doctoral', pattern: /\bdoktoran\w*\b|\bdoktorat\w*\b|\bhabilitac\w*\b|\bstopni\w*\s+naukow\w*\b|\btytuł\w*\s+profesor\w*\b/i, weight: 5 },
  { label: 'academic-staff', pattern: /\bnauczyciel\w*\s+akademick\w*\b|\bpracownik\w*\s+naukow\w*\b/i, weight: 5 },
  { label: 'science-policy', pattern: /\bbadan\w*\s+naukow\w*\b|\bdziałalnoś\w*\s+naukow\w*\b|\bfinansowani\w*\s+nauk\w*\b|\bpolityk\w*\s+naukow\w*\b/i, weight: 5 },
  // Sam zwrot "instytut badawczy" nie wystarcza: wiele takich jednostek
  // podlega resortom zdrowia, obrony lub rolnictwa, a nie MNiSW.
  { label: 'science-institutions', pattern: /\bpolsk\w*\s+akademi\w*\s+nauk\w*\b|\bnarodow\w*\s+centrum\s+nauk\w*\b|\bnarodow\w*\s+centrum\s+badań\w*\s+i\s+rozwoju\b|\bsieć\w*\s+badawcz\w*\s+łukasiewicz\b|\bNAWA\b|\bPOL-?on\b/i, weight: 6 },
];

const COMMON_SUPPORTING_RULES = [
  { label: 'scholarships', pattern: /\bstypendi\w*\b/i, weight: 2 },
  { label: 'accreditation', pattern: /\bakredytac\w*\b|\bpolsk\w*\s+komisj\w*\s+akredytacyjn\w*\b/i, weight: 2 },
  { label: 'rectors', pattern: /\brektor(?:zy|a|ów|om|ami)?\b/i, weight: 2 },
  { label: 'science-wording', pattern: /\bnauk\w*\b|\bakademick\w*\b/i, weight: 1 },
];

const COMMON_NEGATIVE_RULES = [
  { label: 'school-education', pattern: /\boświat\w*\b|\bprzedszkol\w*\b|\bszkoł\w*\s+(?:podstawow\w*|średni\w*|artystyczn\w*)\b|\bmatur\w*\b|\bkurator\w*\s+oświat\w*\b/i, weight: -6 },
  { label: 'vocational-schooling', pattern: /\bszkolnictw\w*\s+branżow\w*\b|\bmłodocian\w*\s+pracownik\w*\b/i, weight: -5 },
  { label: 'labour-market', pattern: /\burzęd\w*\s+pracy\b|\bbezrobotn\w*\b|\bbezroboci\w*\b/i, weight: -5 },
  { label: 'social-policy', pattern: /\bpomoc\w*\s+społeczn\w*\b|\bświadczeni\w*\s+socjaln\w*\b/i, weight: -4 },
];

const RECIPIENT_HINT_PATTERNS = [
  /\bminister(?:stwo|a|owi|em)?\s+nauki\b/i,
  /\bminister(?:stwo|a|owi|em)?\s+nauki\s+i\s+szkolnictwa\s+wyższego\b/i,
];

const sourcePolicies = {
  interpellations: {
    sourcePolicy: 'interpellations',
    positivePatterns: COMMON_POSITIVE_RULES,
    supportingPatterns: COMMON_SUPPORTING_RULES,
    negativePatterns: COMMON_NEGATIVE_RULES,
    acceptThreshold: 5,
    reviewThreshold: 3,
    allowRecipientBoost: true,
    allowPublisherBoost: false,
  },
  writtenQuestions: {
    sourcePolicy: 'writtenQuestions',
    positivePatterns: COMMON_POSITIVE_RULES,
    supportingPatterns: COMMON_SUPPORTING_RULES,
    negativePatterns: COMMON_NEGATIVE_RULES,
    acceptThreshold: 5,
    reviewThreshold: 3,
    allowRecipientBoost: true,
    allowPublisherBoost: false,
  },
  prints: {
    sourcePolicy: 'prints',
    positivePatterns: COMMON_POSITIVE_RULES,
    supportingPatterns: COMMON_SUPPORTING_RULES,
    negativePatterns: COMMON_NEGATIVE_RULES,
    acceptThreshold: 5,
    reviewThreshold: 3,
    allowRecipientBoost: false,
    allowPublisherBoost: false,
  },
  eli: {
    sourcePolicy: 'eli',
    positivePatterns: COMMON_POSITIVE_RULES,
    supportingPatterns: COMMON_SUPPORTING_RULES,
    negativePatterns: COMMON_NEGATIVE_RULES,
    acceptThreshold: 6,
    reviewThreshold: 4,
    allowRecipientBoost: false,
    allowPublisherBoost: true,
  },
};

function normalizeText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function uniqueByLabel(matches) {
  const byLabel = new Map();
  for (const match of matches) {
    const previous = byLabel.get(match.label);
    if (!previous || match.weight > previous.weight) byLabel.set(match.label, match);
  }
  return [...byLabel.values()];
}

function findRuleMatches(text, rules, origin) {
  const source = normalizeText(text);
  if (!source) return [];
  return rules
    .filter(rule => rule.pattern.test(source))
    .map(rule => ({ ...rule, origin }));
}

function isMniswText(text) {
  const normalized = normalizeText(text);
  return RECIPIENT_HINT_PATTERNS.some(pattern => pattern.test(normalized));
}

function labelsToPolish(labels) {
  return labels.map(label => SIGNAL_LABELS[label] || label);
}

function decisionReason(result) {
  if (result.decision === 'accept') {
    const evidence = labelsToPolish(result.matchedPositiveLabels);
    const location = [];
    if (result.matchedTitleLabels.length) location.push('tytuł/metadane');
    if (result.matchedDetailLabels.length) location.push('treść źródłowa');
    const boosts = [];
    if (result.recipientBoost) boosts.push('adresatem jest Minister Nauki');
    if (result.publisherBoost) boosts.push('akt wydał Minister Nauki');
    return `Istotne dla MNiSW: ${evidence.join(', ')} (${location.join(' i ') || 'metadane'}${boosts.length ? `; ${boosts.join(', ')}` : ''}).`;
  }
  if (result.decision === 'review') {
    const evidence = labelsToPolish(result.matchedPositiveLabels);
    return `Do przeglądu: ${evidence.join(', ') || 'sygnały są zbyt słabe do automatycznej publikacji'}.`;
  }
  if (result.matchedNegativeLabels.length) {
    return `Poza zakresem: ${labelsToPolish(result.matchedNegativeLabels).join(', ')}.`;
  }
  return 'Poza zakresem: brak mocnego związku z nauką lub szkolnictwem wyższym.';
}

function evaluateRecord({ titleText, detailText, policy, recipients = [], publisherText = '' }) {
  const titlePositive = findRuleMatches(titleText, policy.positivePatterns, 'title');
  const detailPositive = findRuleMatches(detailText, policy.positivePatterns, 'detail');
  const positiveMatches = uniqueByLabel([...titlePositive, ...detailPositive]);
  const supportingMatches = uniqueByLabel([
    ...findRuleMatches(titleText, policy.supportingPatterns, 'title'),
    ...findRuleMatches(detailText, policy.supportingPatterns, 'detail'),
  ]);
  const negativeMatches = uniqueByLabel([
    ...findRuleMatches(titleText, policy.negativePatterns, 'title'),
    ...findRuleMatches(detailText, policy.negativePatterns, 'detail'),
  ]);

  let score = positiveMatches.reduce((sum, match) => sum + match.weight, 0);
  score += supportingMatches.reduce((sum, match) => sum + match.weight, 0);
  score += negativeMatches.reduce((sum, match) => sum + match.weight, 0);

  const recipientNames = (Array.isArray(recipients) ? recipients : [recipients]).map(normalizeText).filter(Boolean);
  const recipientBoost = policy.allowRecipientBoost && recipientNames.length === 1 && isMniswText(recipientNames[0]) && positiveMatches.length ? 2 : 0;
  const publisherBoost = policy.allowPublisherBoost && isMniswText(publisherText) && positiveMatches.length ? 2 : 0;
  score += recipientBoost + publisherBoost;

  let decision = 'reject';
  if (positiveMatches.length && score >= policy.acceptThreshold) {
    decision = 'accept';
  } else if (positiveMatches.length && score >= policy.reviewThreshold) {
    decision = 'review';
  }

  const result = {
    score,
    decision,
    sourcePolicy: policy.sourcePolicy,
    matchedPositiveLabels: positiveMatches.map(match => match.label),
    matchedSupportingLabels: supportingMatches.map(match => match.label),
    matchedNegativeLabels: negativeMatches.map(match => match.label),
    matchedTitleLabels: uniqueByLabel([...titlePositive, ...supportingMatches.filter(match => match.origin === 'title')]).map(match => match.label),
    matchedDetailLabels: uniqueByLabel([...detailPositive, ...supportingMatches.filter(match => match.origin === 'detail')]).map(match => match.label),
    recipientBoost,
    publisherBoost,
  };
  result.decisionReason = decisionReason(result);
  return result;
}

function sourceErrorPayload(error) {
  const source = normalizeText(error && error.source) || 'research';
  return {
    source,
    label: SOURCE_LABELS[source] || source,
    message: normalizeText(error && error.message) || 'Nieznany błąd źródła.',
  };
}

function fingerprint(value) {
  return JSON.stringify(value);
}

function applyDedupe(items, source, staticData) {
  if (!staticData.seenEvidence || typeof staticData.seenEvidence !== 'object') staticData.seenEvidence = {};
  const now = new Date().toISOString();
  return items.map(item => {
    const id = String(item.num || item.number || item.eli || item.ELI || item.url || '');
    const key = `${source}:${id}`;
    const currentFingerprint = fingerprint([
      'semantic-summary-v2',
      item.lastModified,
      item.sentDate,
      item.changeDate,
      item.deliveryDate,
      item.promulgation,
      item.title,
      item.summary,
      item.replySummary,
      item.score,
    ]);
    const alreadySent = staticData.seenEvidence[key] && staticData.seenEvidence[key].fingerprint === currentFingerprint;
    if (!alreadySent && item.decision === 'accept') {
      staticData.seenEvidence[key] = { fingerprint: currentFingerprint, updatedAt: now };
    }
    return { ...item, alreadySent: Boolean(alreadySent) };
  });
}

function pruneStaticData(staticData) {
  const entries = Object.entries(staticData.seenEvidence || {});
  if (entries.length <= 1000) return;
  entries.sort((left, right) => String(right[1].updatedAt || '').localeCompare(String(left[1].updatedAt || '')));
  staticData.seenEvidence = Object.fromEntries(entries.slice(0, 1000));
}

function buildReviewDiagnostics(items) {
  return items
    .filter(item => item && item.decision === 'review')
    .sort((left, right) => Number(right.score || 0) - Number(left.score || 0))
    .slice(0, 10)
    .map(item => ({
      id: item.num || item.number || item.eli || item.url,
      title: item.title,
      score: item.score,
      decisionReason: item.decisionReason,
      matchedPositiveLabels: item.matchedPositiveLabels,
      matchedNegativeLabels: item.matchedNegativeLabels,
    }));
}

function analyseQuestion(item, sourcePolicy) {
  const recipients = Array.isArray(item.recipients) ? item.recipients : [];
  const evaluation = evaluateRecord({
    titleText: item.title,
    detailText: [item.bodyText, item.replyText].filter(Boolean).join(' '),
    policy: sourcePolicies[sourcePolicy],
    recipients,
  });
  return {
    ...item,
    ...evaluation,
    kind: sourcePolicy === 'writtenQuestions' ? 'Zapytanie poselskie' : 'Interpelacja',
    recipientsText: recipients.join(', '),
    hasReply: item.replyStatus === 'answered' || Boolean(normalizeText(item.replyText)),
    hasDeadlineExtension: item.replyStatus === 'deadline-extension',
  };
}

function analysePrint(item) {
  const evaluation = evaluateRecord({
    titleText: item.title,
    detailText: item.attachmentText || item.researchText,
    policy: sourcePolicies.prints,
  });
  return { ...item, ...evaluation };
}

function analyseEli(item) {
  const publisherText = [
    ...(Array.isArray(item.releasedBy) ? item.releasedBy : []),
    ...(Array.isArray(item.authorizedBody) ? item.authorizedBody : []),
  ].join(' ');
  const detailText = [
    ...(Array.isArray(item.keywords) ? item.keywords : []),
    item.actText,
  ].filter(Boolean).join(' ');
  const evaluation = evaluateRecord({
    titleText: item.title,
    detailText,
    policy: sourcePolicies.eli,
    publisherText,
  });
  return { ...item, ...evaluation, eli: item.eli || item.ELI };
}

function sourceStats(research, name) {
  const stats = research.sources && research.sources[name] ? research.sources[name] : {};
  return {
    checked: Number(stats.checked || 0),
    withinWindow: Number(stats.withinWindow || 0),
    enriched: Number(stats.enriched || 0),
  };
}

function runWorkflow() {
  const research = $input.first().json || {};
  const initData = $('Init: daty i stan').first().json;
  const staticData = $getWorkflowStaticData('global');

  const analysedInterpellations = (research.interpellations || []).map(item => analyseQuestion(item, 'interpellations'));
  const analysedWrittenQuestions = (research.writtenQuestions || []).map(item => analyseQuestion(item, 'writtenQuestions'));
  const analysedPrints = (research.prints || []).map(analysePrint);
  const analysedEli = (research.eliActs || []).map(analyseEli);

  const dedupedInterpellations = applyDedupe(analysedInterpellations, 'interpellations', staticData);
  const dedupedWrittenQuestions = applyDedupe(analysedWrittenQuestions, 'writtenQuestions', staticData);
  const dedupedPrints = applyDedupe(analysedPrints, 'prints', staticData);
  const dedupedEli = applyDedupe(analysedEli, 'eli', staticData);
  pruneStaticData(staticData);

  const interpelacje = dedupedInterpellations
    .filter(item => item.decision === 'accept' && !item.alreadySent)
    .sort((left, right) => Number(right.score) - Number(left.score))
    .slice(0, 20);
  const zapytania = dedupedWrittenQuestions
    .filter(item => item.decision === 'accept' && !item.alreadySent)
    .sort((left, right) => Number(right.score) - Number(left.score))
    .slice(0, 20);
  const druki = dedupedPrints
    .filter(item => item.decision === 'accept' && !item.alreadySent)
    .sort((left, right) => Number(right.score) - Number(left.score))
    .slice(0, 20);
  const aktyPrawne = dedupedEli
    .filter(item => item.decision === 'accept' && !item.alreadySent)
    .sort((left, right) => Number(right.score) - Number(left.score))
    .slice(0, 20);

  const stats = {
    interpelacje: interpelacje.length,
    zapytania: zapytania.length,
    druki: druki.length,
    aktyPrawne: aktyPrawne.length,
    total: interpelacje.length + zapytania.length + druki.length + aktyPrawne.length,
  };
  const interStats = sourceStats(research, 'interpellations');
  const questionStats = sourceStats(research, 'writtenQuestions');
  const printStats = sourceStats(research, 'prints');
  const eliStats = sourceStats(research, 'eliActs');
  const scanStats = {
    interpelacjeChecked: interStats.withinWindow,
    zapytaniaChecked: questionStats.withinWindow,
    drukiChecked: printStats.withinWindow,
    aktyPrawneChecked: eliStats.withinWindow,
    totalApiRecordsChecked: interStats.checked + questionStats.checked + printStats.checked + eliStats.checked,
    enriched: interStats.enriched + questionStats.enriched + printStats.enriched + eliStats.enriched,
  };
  const sourceErrors = (research.sourceErrors || []).map(sourceErrorPayload);
  const diagnostics = {
    interpelacjeReview: buildReviewDiagnostics(dedupedInterpellations),
    zapytaniaReview: buildReviewDiagnostics(dedupedWrittenQuestions),
    drukiReview: buildReviewDiagnostics(dedupedPrints),
    aktyPrawneReview: buildReviewDiagnostics(dedupedEli),
  };
  const briefingStatus = sourceErrors.length ? 'partial_error' : stats.total ? 'matches' : 'empty';

  return [{
    json: {
      briefingStatus,
      dateFrom: research.dateFrom || initData.dateFrom,
      dateTo: research.dateTo || initData.dateTo,
      generatedAt: research.generatedAt,
      fromEmail: initData.fromEmail,
      toEmail: initData.toEmail,
      interpelacje,
      zapytania,
      druki,
      aktyPrawne,
      stats,
      scanStats,
      sourceErrors,
      diagnostics,
    },
  }];
}

return runWorkflow();
