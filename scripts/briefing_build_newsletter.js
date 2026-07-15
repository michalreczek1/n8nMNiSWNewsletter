function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function cleanText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function shorten(value, maxLength = 900) {
  const text = cleanText(value);
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength).replace(/\s+\S*$/, '').replace(/[,:;\-–—\s]+$/, '')}...`;
}

function renderMetaHtml(parts) {
  const values = parts.map(cleanText).filter(Boolean);
  return values
    .map(value => `<span style="display:inline-block;font-size:12px;line-height:1.5;color:#64748b">${escapeHtml(value)}</span>`)
    .join('<span style="display:inline-block;font-size:12px;line-height:1.5;color:#cbd5e1;padding:0 8px">|</span>');
}

function renderMetaText(parts) {
  const values = parts.map(cleanText).filter(Boolean);
  return values.length ? values.join(' | ') : '';
}

function renderEvidenceHtml(item) {
  const summary = shorten(item.summary);
  const reply = shorten(item.replySummary);
  const blocks = [];
  if (summary) blocks.push(`<p style="margin:0 0 8px"><strong>Co wynika ze źródła:</strong> ${escapeHtml(summary)}</p>`);
  if (reply) blocks.push(`<p style="margin:0 0 8px"><strong>Najnowsza odpowiedź:</strong> ${escapeHtml(reply)}</p>`);
  blocks.push(`<p style="margin:0;color:#1e3a5f"><strong>Dlaczego w briefingu:</strong> ${escapeHtml(item.decisionReason)}</p>`);
  if (!summary && item.researchQuality === 'metadata') {
    blocks.unshift('<p style="margin:0 0 8px;color:#64748b">API nie udostępniło czytelnej treści dokumentu; kwalifikacja opiera się na tytule i metadanych.</p>');
  }
  return blocks.join('');
}

function renderSection(title, eyebrow, items, renderRow) {
  if (!items || !items.length) return '';
  return `
    <div style="background:#ffffff;border:1px solid #dbe4f0;border-radius:14px;padding:20px 20px 6px;margin-bottom:18px;box-shadow:0 8px 24px rgba(15,23,42,.04)">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:14px">
        <div>
          <div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.7px;margin-bottom:4px">${escapeHtml(eyebrow)}</div>
          <h2 style="margin:0;font-size:18px;line-height:1.3;color:#0f172a">${escapeHtml(title)}</h2>
        </div>
        <span style="display:inline-block;background:#e0ecff;color:#1d4ed8;border-radius:999px;padding:6px 11px;font-size:12px;font-weight:700">${items.length}</span>
      </div>
      ${items.map(renderRow).join('')}
    </div>`;
}

function renderRow({ heading, url, metaParts, bodyHtml, secondaryUrl = '', secondaryLabel = '' }) {
  return `
    <div style="padding:0 0 16px;margin:0 0 16px;border-bottom:1px solid #eef2f7">
      <div style="margin-bottom:8px;line-height:1.8">${renderMetaHtml(metaParts || [])}</div>
      <div style="font-size:15px;font-weight:700;color:#0f172a;line-height:1.5;margin-bottom:8px">${escapeHtml(heading)}</div>
      <div style="font-size:13px;color:#475569;line-height:1.7;margin-bottom:10px">${bodyHtml}</div>
      <a href="${escapeHtml(url)}" style="display:inline-block;color:#1d4ed8;text-decoration:none;font-weight:700;font-size:12px">Otwórz pozycję źródłową</a>
      ${secondaryUrl ? `<span style="color:#cbd5e1;padding:0 8px">|</span><a href="${escapeHtml(secondaryUrl)}" style="display:inline-block;color:#1d4ed8;text-decoration:none;font-weight:600;font-size:12px">${escapeHtml(secondaryLabel || 'Otwórz dokument')}</a>` : ''}
    </div>`;
}

const data = $json;
const {
  briefingStatus,
  dateFrom,
  dateTo,
  interpelacje,
  zapytania,
  druki,
  aktyPrawne,
  stats,
  scanStats,
  sourceErrors,
} = data;

const subtitle = `Tydzień ${dateFrom} – ${dateTo}`;
const statsCards = `
  <div style="margin-top:22px;display:flex;gap:12px;flex-wrap:wrap">
    ${[
      ['Interpelacje', stats.interpelacje],
      ['Zapytania', stats.zapytania],
      ['Druki', stats.druki],
      ['Akty prawne', stats.aktyPrawne],
    ].map(([label, value]) => `
      <div style="min-width:132px;flex:1;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.18);border-radius:12px;padding:14px 16px;text-align:center">
        <div style="font-size:28px;font-weight:800;line-height:1">${value}</div>
        <div style="font-size:11px;opacity:.82;margin-top:8px;text-transform:uppercase;letter-spacing:.7px">${label}</div>
      </div>`).join('')}
  </div>`;

const scanSummaryHtml = `
  <div style="background:#ffffff;border:1px solid #dbe4f0;border-radius:14px;padding:20px 22px;margin-bottom:18px;box-shadow:0 8px 24px rgba(15,23,42,.04)">
    <div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.7px;margin-bottom:6px">Zakres i jakość researchu</div>
    <h2 style="margin:0 0 10px;font-size:18px;color:#0f172a;line-height:1.4">Przeszukano źródła Sejmu i ELI w zadanym okresie</h2>
    <p style="margin:0 0 8px;font-size:14px;color:#475569;line-height:1.7">W oknie tygodniowym znaleziono ${scanStats.interpelacjeChecked} interpelacji, ${scanStats.zapytaniaChecked} zapytań poselskich, ${scanStats.drukiChecked} nowych lub zmienionych druków oraz ${scanStats.aktyPrawneChecked} opublikowanych aktów prawnych.</p>
    <p style="margin:0;font-size:14px;color:#475569;line-height:1.7">Dla ${scanStats.enriched} wstępnie trafnych pozycji pobrano dodatkowo treść interpelacji, odpowiedzi, uzasadnienia albo tekst aktu. Do maila trafiły tylko rekordy z mocnym, wyjaśnionym związkiem z nauką lub szkolnictwem wyższym.</p>
  </div>`;

const emptyStateHtml = `
  <div style="background:#ffffff;border:1px solid #dbe4f0;border-radius:14px;padding:22px;margin-bottom:18px;box-shadow:0 8px 24px rgba(15,23,42,.04)">
    <h2 style="margin:0 0 10px;font-size:18px;color:#0f172a;line-height:1.45">W badanym tygodniu briefing nie wykazał nowych pozycji mieszczących się we właściwości Ministra Nauki i Szkolnictwa Wyższego</h2>
    <p style="margin:0;font-size:14px;color:#475569;line-height:1.7">Nie oznacza to braku aktywności Sejmu. Oznacza, że po sprawdzeniu metadanych i dostępnych treści żaden nowy rekord nie miał wystarczająco mocnego związku z zakresem MNiSW albo został już wcześniej wysłany bez późniejszej zmiany.</p>
  </div>`;

const alertHtml = sourceErrors && sourceErrors.length
  ? `
    <div style="background:#fff7ed;border:1px solid #fdba74;border-radius:14px;padding:18px 20px;margin-bottom:18px">
      <div style="font-size:11px;font-weight:700;color:#c2410c;text-transform:uppercase;letter-spacing:.7px;margin-bottom:6px">Ostrzeżenie o kompletności</div>
      <h2 style="margin:0 0 10px;font-size:18px;color:#9a3412;line-height:1.4">Briefing został przygotowany częściowo</h2>
      <p style="margin:0 0 10px;font-size:14px;color:#7c2d12;line-height:1.7">Co najmniej jedno źródło nie odpowiedziało poprawnie. Mail wychodzi, żeby nie zostawiać Cię bez statusu tygodnia, ale wynik może być niepełny.</p>
      <ul style="margin:0;padding-left:18px;color:#7c2d12;font-size:13px;line-height:1.7">${sourceErrors.map(error => `<li><strong>${escapeHtml(error.label)}</strong>: ${escapeHtml(error.message)}</li>`).join('')}</ul>
    </div>`
  : '';

const interpelacjeHtml = renderSection('Interpelacje', 'Sejm', interpelacje, item => renderRow({
  heading: item.title,
  url: item.url,
  metaParts: [item.eventDate || item.sentDate || item.receiptDate, item.eventType === 'answer-update' ? 'Nowa odpowiedź do wcześniejszej interpelacji' : 'Nowa interpelacja w badanym okresie', item.recipientsText ? `Do: ${item.recipientsText}` : '', item.hasReply ? 'Jest odpowiedź' : 'Bez odpowiedzi', item.researchQuality === 'full-text' ? 'Sprawdzono treść' : 'Tylko metadane'],
  bodyHtml: renderEvidenceHtml(item),
}));

const zapytaniaHtml = renderSection('Zapytania poselskie', 'Sejm', zapytania, item => renderRow({
  heading: item.title,
  url: item.url,
  metaParts: [item.eventDate || item.sentDate || item.receiptDate, item.eventType === 'answer-update' ? 'Nowa odpowiedź do wcześniejszego zapytania' : 'Nowe zapytanie w badanym okresie', item.recipientsText ? `Do: ${item.recipientsText}` : '', item.hasReply ? 'Jest odpowiedź' : 'Bez odpowiedzi', item.researchQuality === 'full-text' ? 'Sprawdzono treść' : 'Tylko metadane'],
  bodyHtml: renderEvidenceHtml(item),
}));

const drukiHtml = renderSection('Druki sejmowe', 'Proces legislacyjny', druki, item => renderRow({
  heading: `Druk nr ${item.number}: ${item.title}`,
  url: item.url,
  metaParts: [item.deliveryDate || (item.changeDate ? item.changeDate.slice(0, 10) : ''), item.documentType || '', item.researchQuality === 'full-text' ? 'Sprawdzono dokument' : 'Tylko metadane'],
  bodyHtml: renderEvidenceHtml(item),
  secondaryUrl: item.attachmentUrl,
  secondaryLabel: 'Otwórz uzasadnienie / dokument',
}));

const aktyHtml = renderSection('Akty prawne opublikowane w Dzienniku Ustaw', 'ELI', aktyPrawne, item => {
  const legalMeta = [
    item.promulgation ? `Ogłoszono: ${item.promulgation}` : '',
    item.entryIntoForce ? `Wejście w życie: ${item.entryIntoForce}` : '',
    item.status || '',
  ];
  const keywords = Array.isArray(item.keywords) && item.keywords.length
    ? `<p style="margin:0 0 8px"><strong>Słowa kluczowe ELI:</strong> ${escapeHtml(item.keywords.slice(0, 8).join(', '))}</p>`
    : '';
  return renderRow({
    heading: `${item.displayAddress || item.eli}: ${item.title}`,
    url: item.url,
    metaParts: legalMeta,
    bodyHtml: `${keywords}${renderEvidenceHtml(item)}`,
  });
});

const sectionsHtml = [interpelacjeHtml, zapytaniaHtml, drukiHtml, aktyHtml].filter(Boolean).join('');
const shouldRenderEmpty = briefingStatus === 'empty' || (briefingStatus === 'partial_error' && stats.total === 0);
const html = `<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>*{box-sizing:border-box}body{margin:0;padding:20px;background:#f1f5f9;font-family:Arial,sans-serif}</style></head><body><div style="max-width:780px;margin:0 auto"><div style="background:linear-gradient(135deg,#163760,#2563eb);color:#fff;border-radius:16px;padding:30px 28px 26px;margin-bottom:20px;box-shadow:0 18px 36px rgba(37,99,235,.20)"><div style="font-size:11px;opacity:.72;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:8px">Monitor Parlamentarny · MNiSW</div><h1 style="margin:0 0 10px;font-size:24px;font-weight:800;line-height:1.25">Tygodniowy Briefing Parlamentarny</h1><div style="max-width:620px;opacity:.92;font-size:14px;line-height:1.7">${escapeHtml(subtitle)}. Wyniki są oparte na oficjalnych danych Sejmu i ELI oraz — gdy API je udostępnia — na treści dokumentów źródłowych.</div>${statsCards}</div>${alertHtml}${scanSummaryHtml}${shouldRenderEmpty ? emptyStateHtml : ''}${sectionsHtml}<div style="margin-top:24px;background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:18px 20px;text-align:center"><div style="font-size:12px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:#1e3a5f;margin-bottom:6px">Monitor Parlamentarny · MNiSW</div><div style="font-size:13px;color:#475569;line-height:1.6">Made by Michał Reczek · <a href="mailto:michalreczek@gmail.com" style="color:#1d4ed8;text-decoration:none">michalreczek@gmail.com</a></div><div style="font-size:11px;color:#94a3b8;margin-top:8px">Źródła: api.sejm.gov.pl/sejm · api.sejm.gov.pl/eli · ${escapeHtml(new Date().toLocaleString('pl-PL'))}</div></div></div></body></html>`;

function evidenceText(item) {
  return [
    item.summary ? `Co wynika ze źródła: ${shorten(item.summary)}` : '',
    item.replySummary ? `Najnowsza odpowiedź: ${shorten(item.replySummary)}` : '',
    `Dlaczego w briefingu: ${item.decisionReason}`,
    !item.summary && item.researchQuality === 'metadata' ? 'Uwaga: kwalifikacja opiera się na tytule i metadanych; API nie udostępniło czytelnej treści dokumentu.' : '',
  ].filter(Boolean).join('\n');
}

function sectionText(title, items, renderItem) {
  if (!items || !items.length) return '';
  return `${title}\n${items.map(renderItem).join('\n\n')}`;
}

const interpelacjeText = sectionText('Interpelacje', interpelacje, item => [item.title, `Link: ${item.url}`, renderMetaText([item.eventDate || item.sentDate || item.receiptDate, item.eventType === 'answer-update' ? 'Nowa odpowiedź do wcześniejszej interpelacji' : 'Nowa interpelacja w badanym okresie', item.recipientsText ? `Do: ${item.recipientsText}` : '', item.hasReply ? 'Jest odpowiedź' : 'Bez odpowiedzi']), evidenceText(item)].filter(Boolean).join('\n'));
const zapytaniaText = sectionText('Zapytania poselskie', zapytania, item => [item.title, `Link: ${item.url}`, renderMetaText([item.eventDate || item.sentDate || item.receiptDate, item.eventType === 'answer-update' ? 'Nowa odpowiedź do wcześniejszego zapytania' : 'Nowe zapytanie w badanym okresie', item.recipientsText ? `Do: ${item.recipientsText}` : '', item.hasReply ? 'Jest odpowiedź' : 'Bez odpowiedzi']), evidenceText(item)].filter(Boolean).join('\n'));
const drukiText = sectionText('Druki sejmowe', druki, item => [`Druk nr ${item.number}: ${item.title}`, `Link: ${item.url}`, item.attachmentUrl ? `Dokument: ${item.attachmentUrl}` : '', renderMetaText([item.deliveryDate || (item.changeDate ? item.changeDate.slice(0, 10) : ''), item.documentType || '']), evidenceText(item)].filter(Boolean).join('\n'));
const aktyText = sectionText('Akty prawne opublikowane w Dzienniku Ustaw', aktyPrawne, item => [item.displayAddress || item.eli, item.title, `Link: ${item.url}`, renderMetaText([item.promulgation ? `Ogłoszono: ${item.promulgation}` : '', item.entryIntoForce ? `Wejście w życie: ${item.entryIntoForce}` : '', item.status || '']), Array.isArray(item.keywords) && item.keywords.length ? `Słowa kluczowe ELI: ${item.keywords.slice(0, 8).join(', ')}` : '', evidenceText(item)].filter(Boolean).join('\n'));
const textSections = [interpelacjeText, zapytaniaText, drukiText, aktyText].filter(Boolean).join('\n\n---\n\n');
const errorsText = sourceErrors && sourceErrors.length ? `Ostrzeżenie: wynik częściowy\n${sourceErrors.map(error => `- ${error.label}: ${error.message}`).join('\n')}` : '';
const emptyText = 'Po sprawdzeniu metadanych i dostępnych treści nie znaleziono nowych, niewysłanych wcześniej pozycji z wystarczająco mocnym związkiem z zakresem MNiSW.';

let subject = `Briefing parlamentarny MNiSW | ${stats.total} nowych pozycji | ${dateTo}`;
if (briefingStatus === 'empty') subject = `Briefing parlamentarny MNiSW | Status tygodniowy | ${dateTo}`;
if (briefingStatus === 'partial_error') subject = `Briefing parlamentarny MNiSW | Wynik częściowy | ${dateTo}`;

const text = [
  'Monitor Parlamentarny - MNiSW',
  subtitle,
  `Interpelacje: ${stats.interpelacje} | Zapytania: ${stats.zapytania} | Druki: ${stats.druki} | Akty prawne: ${stats.aktyPrawne}`,
  `Zakres: ${scanStats.interpelacjeChecked} interpelacji, ${scanStats.zapytaniaChecked} zapytań, ${scanStats.drukiChecked} druków i ${scanStats.aktyPrawneChecked} aktów. Wzbogacono treścią: ${scanStats.enriched}.`,
  errorsText,
  shouldRenderEmpty ? emptyText : '',
  textSections,
  'Źródła: https://api.sejm.gov.pl/sejm | https://api.sejm.gov.pl/eli',
  'Made by Michał Reczek | michalreczek@gmail.com',
].filter(Boolean).join('\n\n');

return [{ json: { subject, html, text, fromEmail: data.fromEmail, toEmail: data.toEmail } }];
