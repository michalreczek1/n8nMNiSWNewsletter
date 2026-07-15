function clean(s) {
  return String(s || '')
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#34;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&ndash;|&#8211;/g, '-')
    .replace(/&mdash;|&#8212;/g, '-')
    .replace(/\s+/g, ' ')
    .trim();
}

function abs(url) {
  if (!url) return null;
  const cleanUrl = String(url).replace(/#.*$/, '');
  if (cleanUrl.startsWith('http')) return cleanUrl;
  if (cleanUrl.startsWith('/')) return `https://legislacja.gov.pl${cleanUrl}`;
  return `https://legislacja.gov.pl/${cleanUrl}`;
}

function parseDatePL(val) {
  if (!val) return null;
  const s = String(val).trim();
  let m = s.match(/(\d{2})-(\d{2})-(\d{4})/);
  if (!m) m = s.match(/(\d{2})\.(\d{2})\.(\d{4})/);
  return m ? new Date(`${m[3]}-${m[2]}-${m[1]}T00:00:00Z`) : null;
}

function dateKey(date) {
  return date ? date.toISOString().slice(0, 10) : '';
}

function cellTexts(rowHtml) {
  const cells = [];
  const cellRegex = /<td\b[^>]*>([\s\S]*?)<\/td\s*>/gi;
  let cell;
  while ((cell = cellRegex.exec(rowHtml)) !== null) {
    cells.push(clean(cell[1]));
  }
  return cells;
}

function extractRowsFromFullList(html) {
  const listMatch = html.match(/<table[^>]*id=["']table["'][\s\S]*?<tbody>([\s\S]*?)<\/tbody>/i);
  const section = listMatch ? listMatch[1] : html;
  const out = [];
  const rowRegex = /<tr\b[^>]*>([\s\S]*?)<\/tr\s*>/gi;
  let row;
  while ((row = rowRegex.exec(section)) !== null) {
    const rowHtml = row[1];
    const linkMatch = rowHtml.match(/<a\s+href=["']([^"']*\/projekt\/[^"']*)["'][^>]*>([\s\S]*?)<\/a>/i);
    if (!linkMatch) continue;
    const cells = cellTexts(rowHtml);
    const created = cells.find(v => /^(\d{2}-\d{2}-\d{4}|\d{2}\.\d{2}\.\d{4})$/.test(v)) || '';
    const dateCells = cells.filter(v => /^(\d{2}-\d{2}-\d{4}|\d{2}\.\d{2}\.\d{4})$/.test(v));
    out.push({
      projectUrl: abs(linkMatch[1]),
      title: clean(linkMatch[2]),
      applicant: cells[1] || '',
      number: cells[2] && !/^(\d{2}-\d{2}-\d{4}|\d{2}\.\d{2}\.\d{4})$/.test(cells[2]) ? cells[2] : '',
      dateCreated: created,
      dateUpdated: dateCells[1] || '',
      sourceListType: 'full-list'
    });
  }
  return out;
}

function extractRowsFromHomepage(html) {
  const sectionMatch = html.match(/Ostatnio dodane projekty([\s\S]*?)Rozwiń lub zwiń menu projektów/i);
  const section = sectionMatch ? sectionMatch[1] : html;
  const out = [];
  const regex = /<tr>[\s\S]*?<a href="([^"]*\/projekt\/[^"]*)"[^>]*>([\s\S]*?)<\/a>[\s\S]*?<td[^>]*class="text-right"[^>]*>\s*(\d{2}-\d{2}-\d{4}|\d{2}\.\d{2}\.\d{4})\s*<\/td>[\s\S]*?<\/tr>/gsi;
  let m;
  while ((m = regex.exec(section)) !== null) {
    out.push({
      projectUrl: abs(m[1]),
      title: clean(m[2]),
      applicant: '',
      number: '',
      dateCreated: m[3],
      dateUpdated: '',
      sourceListType: 'homepage-recent'
    });
  }
  return out;
}

const raw = $input.first().json;
const html = typeof raw === 'string'
  ? raw
  : (raw.body || raw.data || raw.html || raw.response || '');

if (!html) {
  return [{ json: { error: true, stage: 'fetch-project-list', message: 'Brak HTML z listy projektów RCL.', bodyPreview: '' } }];
}

if (html.includes('Żądanie nie może zostać zrealizowane') || html.includes('Request Rejected')) {
  return [{
    json: {
      error: true,
      stage: 'fetch-project-list',
      message: 'Serwis odrzucił żądanie do listy projektów RCL.',
      bodyPreview: html.slice(0, 500)
    }
  }];
}

const cfg = $('Config').first().json;
const daysLookback = Number(cfg.daysLookback || 14);
const now = new Date();
const parsedRows = html.includes('Lista projektów według wybranych kryteriów')
  ? extractRowsFromFullList(html)
  : extractRowsFromHomepage(html);

const seen = new Set();
const candidates = [];
for (const row of parsedRows) {
  const created = parseDatePL(row.dateCreated);
  const ageDays = created ? Math.floor((now - created) / 86400000) : null;
  if (ageDays !== null && ageDays > daysLookback) continue;
  if (!row.projectUrl || !row.title || seen.has(row.projectUrl)) continue;
  seen.add(row.projectUrl);
  candidates.push({ ...row, created, ageDays });
}

const newestKey = candidates
  .map(row => dateKey(row.created))
  .filter(Boolean)
  .sort()
  .pop();

const newestProjects = newestKey
  ? candidates.filter(row => dateKey(row.created) === newestKey)
  : candidates;

const out = newestProjects.map(row => ({
  json: {
    projectUrl: row.projectUrl,
    titleFromList: row.title,
    applicantFromList: row.applicant,
    numberFromList: row.number,
    dateCreatedFromList: row.dateCreated,
    dateUpdatedFromList: row.dateUpdated,
    sourceListType: row.sourceListType,
    newestDateFromList: newestKey,
    fromEmail: cfg.fromEmail,
    toEmail: cfg.toEmail,
    daysLookback: cfg.daysLookback,
    scoreThreshold: cfg.scoreThreshold,
    batchSize: cfg.batchSize,
    waitSeconds: cfg.waitSeconds,
    retentionDays: cfg.retentionDays
  }
}));

if (!out.length) {
  return [{
    json: {
      error: true,
      stage: 'extract-recent-projects',
      message: 'Nie znaleziono linków do najnowszych projektów w RCL.',
      bodyPreview: html.slice(0, 700)
    }
  }];
}

return out;
