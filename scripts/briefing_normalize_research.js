function errorMessage(value) {
  if (!value || typeof value !== 'object') return null;
  const candidates = [
    value.message,
    value.error && value.error.message,
    value.error,
    value.reason,
    value.description,
    value.details,
  ];
  return candidates.find(candidate => typeof candidate === 'string' && candidate.trim()) || null;
}

const all = $input.all();
if (!all.length) {
  return [{
    json: {
      status: 'partial_error',
      interpellations: [],
      writtenQuestions: [],
      prints: [],
      eliActs: [],
      sources: {},
      sourceErrors: [{ source: 'research', message: 'Helper researchu nie zwrócił odpowiedzi.' }],
    },
  }];
}

const raw = all[0].json;
const message = errorMessage(raw);
if (message && raw.error) {
  return [{
    json: {
      status: 'partial_error',
      interpellations: [],
      writtenQuestions: [],
      prints: [],
      eliActs: [],
      sources: {},
      sourceErrors: [{ source: 'research', message }],
    },
  }];
}

const research = raw && typeof raw === 'object' ? raw : {};
return [{
  json: {
    ...research,
    interpellations: Array.isArray(research.interpellations) ? research.interpellations : [],
    writtenQuestions: Array.isArray(research.writtenQuestions) ? research.writtenQuestions : [],
    prints: Array.isArray(research.prints) ? research.prints : [],
    eliActs: Array.isArray(research.eliActs) ? research.eliActs : [],
    sources: research.sources && typeof research.sources === 'object' ? research.sources : {},
    sourceErrors: Array.isArray(research.sourceErrors) ? research.sourceErrors : [],
  },
}];
