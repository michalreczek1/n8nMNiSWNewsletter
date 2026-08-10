function clean(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function list(value, limit = 8) {
  if (!Array.isArray(value)) return [];
  return value.map(clean).filter(Boolean).slice(0, limit);
}

function renderList(title, values, accent = '#1d4ed8') {
  const items = list(values);
  if (!items.length) return '';
  return `<div style="margin:18px 0 0"><div style="font-size:12px;font-weight:800;letter-spacing:.7px;text-transform:uppercase;color:${accent};margin-bottom:8px">${escapeHtml(title)}</div><ul style="margin:0;padding-left:20px;color:#334155;font-size:14px;line-height:1.7">${items.map(item => `<li style="margin:0 0 6px">${escapeHtml(item)}</li>`).join('')}</ul></div>`;
}

function renderFact(label, value) {
  const normalized = clean(value);
  if (!normalized) return '';
  return `<tr><td style="padding:8px 12px 8px 0;color:#64748b;font-size:12px;font-weight:700;text-transform:uppercase;vertical-align:top;white-space:nowrap">${escapeHtml(label)}</td><td style="padding:8px 0;color:#0f172a;font-size:14px;line-height:1.55">${escapeHtml(normalized)}</td></tr>`;
}

const payload = $json || {};
const ai = payload.output && typeof payload.output === 'object' ? payload.output : {};
const isUpdate = payload.notificationType === 'updated';
const fitLabel = ai.fitBand === 'strong' ? 'Dobre dopasowanie' : 'Możliwe dopasowanie — oceń samodzielnie';
const statusLabel = isUpdate ? 'Aktualizacja fiszki' : 'Nowa fiszka Twinning';
const statusColor = isUpdate ? '#b45309' : '#047857';
const statusBackground = isUpdate ? '#fff7ed' : '#ecfdf5';
const title = clean(payload.title || ai.projectTitle || 'Nowa oferta Twinning');
const country = clean(payload.country || payload.beneficiary || ai.locationAndTravel);
const purpose = clean(ai.purpose || ai.decisionSummary || payload.pageText);
const decision = clean(ai.decisionSummary || purpose);
const sourceFiles = Array.isArray(payload.sourceFiles)
  ? payload.sourceFiles.map(file => file.name).filter(Boolean).join(', ')
  : clean(payload.primaryDocument);

const facts = [
  renderFact('Kraj / beneficjent', country),
  renderFact('Obszar', payload.area),
  renderFact('Numer', payload.reference || payload.offerId),
  renderFact('Termin do MSZ', payload.mszDeadline),
  renderFact('Termin beneficjenta', payload.beneficiaryDeadline),
  renderFact('Budżet', ai.budget),
  renderFact('Czas projektu', ai.duration),
  renderFact('Miejsce i wyjazdy', ai.locationAndTravel),
  renderFact('Język', ai.language),
  renderFact('Dopasowanie do profilu', `${fitLabel}${ai.fitScore !== undefined ? ` (${ai.fitScore}/100)` : ''}`),
  renderFact('Najlepsza rola wejściowa', ai.bestEntryRole),
  renderFact('Doświadczenie międzynarodowe', ai.internationalExperienceRequirement),
].join('');

const html = `<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:0;padding:20px;background:#eef2f7;font-family:Arial,Helvetica,sans-serif;color:#0f172a"><div style="max-width:720px;margin:0 auto">
  <div style="background:linear-gradient(135deg,#0f2f55,#1d4ed8);color:#fff;border-radius:18px;padding:30px 28px;box-shadow:0 16px 40px rgba(30,64,175,.2)">
    <div style="display:inline-block;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.25);border-radius:999px;padding:6px 12px;font-size:11px;font-weight:800;letter-spacing:.8px;text-transform:uppercase">${escapeHtml(statusLabel)}</div>
    <h1 style="font-size:24px;line-height:1.35;margin:16px 0 8px">${escapeHtml(title)}</h1>
    <div style="font-size:14px;line-height:1.7;opacity:.9">${escapeHtml(country)}${payload.area ? ` · ${escapeHtml(payload.area)}` : ''}</div>
  </div>

  <div style="background:${statusBackground};border:1px solid ${isUpdate ? '#fed7aa' : '#a7f3d0'};border-radius:14px;padding:18px 20px;margin-top:18px">
    <div style="font-size:11px;font-weight:800;letter-spacing:.7px;text-transform:uppercase;color:${statusColor};margin-bottom:7px">Ocena do szybkiej decyzji</div>
    <div style="font-size:15px;line-height:1.7;color:#1f2937"><strong>${escapeHtml(fitLabel)}.</strong> ${escapeHtml(clean(ai.fitReason))}${ai.fitReason ? '<br><br>' : ''}${escapeHtml(decision || 'Szczegóły zostały odczytane z oficjalnej fiszki. Otwórz dokument źródłowy, aby zweryfikować dopasowanie do Twojego doświadczenia.')}</div>
  </div>

  <div style="background:#fff;border:1px solid #dbe3ee;border-radius:14px;padding:22px;margin-top:18px">
    <h2 style="font-size:18px;margin:0 0 10px;color:#0f172a">Najważniejsze informacje</h2>
    <p style="font-size:14px;line-height:1.75;color:#334155;margin:0 0 12px">${escapeHtml(purpose)}</p>
    <table role="presentation" style="border-collapse:collapse;width:100%;margin-top:8px">${facts}</table>
    ${renderList('Kogo szukają', ai.soughtProfiles, '#7c3aed')}
    ${renderList('Wymagania obowiązkowe', ai.mandatoryRequirements, '#b45309')}
    ${renderList('Główne zadania', ai.keyTasks, '#1d4ed8')}
    ${renderList('Na co uważać', ai.risksOrCaveats, '#be123c')}
  </div>

  <div style="background:#fff7ed;border:1px solid #fdba74;border-radius:14px;padding:18px 20px;margin-top:18px">
    <div style="font-size:12px;font-weight:800;color:#9a3412;text-transform:uppercase;letter-spacing:.6px;margin-bottom:7px">Ważne: jak można dołączyć</div>
    <div style="font-size:14px;line-height:1.7;color:#431407">${escapeHtml(clean(ai.whoCanApply) || 'Ofertę składa polska jednostka administracji publicznej albo instytucja ze statusem Mandated Body. Indywidualny ekspert uczestniczy przez taką instytucję — jako RTA, lider komponentu lub ekspert ad hoc — a nie jako samodzielny oferent.')}</div>
  </div>

  <div style="text-align:center;margin:22px 0 8px"><a href="${escapeHtml(payload.url)}" style="display:inline-block;background:#1d4ed8;color:#fff;text-decoration:none;border-radius:10px;padding:12px 20px;font-size:14px;font-weight:700">Otwórz ogłoszenie MSZ</a>${payload.attachmentUrl ? ` <a href="${escapeHtml(payload.attachmentUrl)}" style="display:inline-block;background:#fff;color:#1d4ed8;text-decoration:none;border:1px solid #93c5fd;border-radius:10px;padding:11px 20px;font-size:14px;font-weight:700;margin-left:6px">Pobierz załączniki</a>` : ''}</div>

  <div style="font-size:11px;line-height:1.6;color:#94a3b8;text-align:center;margin:18px 0">Automatyczny monitoring strony MSZ · sprawdzanie co 30 minut<br>Analiza dokumentu: ${escapeHtml(payload.primaryDocument || sourceFiles || 'oficjalna fiszka')} · zweryfikuj dane przed aplikowaniem.</div>
</div></body></html>`;

const plainLists = [
  ['Kogo szukają', list(ai.soughtProfiles)],
  ['Wymagania obowiązkowe', list(ai.mandatoryRequirements)],
  ['Główne zadania', list(ai.keyTasks)],
  ['Na co uważać', list(ai.risksOrCaveats)],
].map(([heading, values]) => values.length ? `${heading}:\n- ${values.join('\n- ')}` : '').filter(Boolean).join('\n\n');

const subjectPrefix = isUpdate ? 'AKTUALIZACJA FISZKI' : 'NOWA FISZKA TWINNING';
return [{ json: {
  ...payload,
  subject: `${subjectPrefix}: ${country || payload.area || 'MSZ'} — ${title}`.slice(0, 220),
  html,
  text: [
    statusLabel,
    title,
    country,
    `Termin do MSZ: ${clean(payload.mszDeadline) || 'sprawdź w ogłoszeniu'}`,
    '',
    decision,
    '',
    purpose,
    '',
    plainLists,
    '',
    `Kto może aplikować: ${clean(ai.whoCanApply) || 'polska administracja publiczna / Mandated Body; ekspert indywidualny przez uprawnioną instytucję'}`,
    '',
    `Ogłoszenie: ${payload.url}`,
    payload.attachmentUrl ? `Załączniki: ${payload.attachmentUrl}` : '',
  ].filter(value => value !== '').join('\n'),
} }];
