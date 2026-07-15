function cleanText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

const summaries = $input.all()
  .map(item => item.json?.output)
  .filter(output => output && typeof output === 'object')
  .map(output => ({
    id: cleanText(output.id),
    questionSummary: cleanText(output.questionSummary),
    answerSummary: cleanText(output.answerSummary),
  }))
  .filter(output => output.id && output.id !== '__none__');

return [{ json: { output: { summaries } } }];
