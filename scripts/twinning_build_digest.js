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

const payload = $json || {};
const offers = Array.isArray(payload.pendingOffers) ? payload.pendingOffers : [];
if (!offers.length) return [];

const toEmails = String(payload.toEmailsCsv || '')
  .split(',')
  .map(value => value.trim())
  .filter(Boolean);

const sorted = [...offers].sort((a, b) =>
  clean(a.country).localeCompare(clean(b.country), 'pl') || clean(a.title).localeCompare(clean(b.title), 'pl')
);
const cards = sorted.map(offer => `
  <div style="padding:18px 16px;border-bottom:1px solid #e2e8f0">
    <a href="${escapeHtml(offer.url)}" style="color:#1d4ed8;font-size:16px;font-weight:700;text-decoration:none;line-height:1.45">${escapeHtml(clean(offer.title) || 'Oferta Twinning')}</a>
    <div style="margin-top:9px;font-size:13px;line-height:1.7;color:#334155"><strong>Kraj:</strong> ${escapeHtml(clean(offer.country) || '—')} &nbsp;·&nbsp; <strong>Dziedzina:</strong> ${escapeHtml(clean(offer.area) || '—')}<br><strong>Termin MSZ:</strong> ${escapeHtml(clean(offer.mszDeadline) || 'sprawdź')}</div>
    ${offer.bestEntryRole ? `<div style="color:#64748b;font-size:12px;line-height:1.55;margin-top:6px"><strong>Potencjalna rola:</strong> ${escapeHtml(offer.bestEntryRole)}</div>` : ''}
  </div>`).join('');

const html = `<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:0;padding:20px;background:#eef2f7;font-family:Arial,Helvetica,sans-serif;color:#0f172a"><div style="max-width:820px;margin:0 auto">
  <div style="background:linear-gradient(135deg,#334155,#0f172a);color:#fff;border-radius:18px;padding:28px">
    <div style="font-size:11px;font-weight:800;letter-spacing:.8px;text-transform:uppercase;opacity:.75">Przegląd co dwa dni</div>
    <h1 style="font-size:24px;line-height:1.35;margin:10px 0 6px">Pozostałe nowe fiszki Twinning</h1>
    <div style="font-size:14px;opacity:.85">${sorted.length} ${sorted.length === 1 ? 'oferta wyraźnie poza ustawionym profilem' : 'oferty wyraźnie poza ustawionym profilem'}</div>
  </div>
  <div style="background:#fff;border:1px solid #dbe3ee;border-radius:14px;margin-top:18px;overflow:hidden">${cards}</div>
  <div style="font-size:11px;line-height:1.6;color:#94a3b8;text-align:center;margin:18px 0">Oferty dobre i graniczne są wysyłane natychmiast w osobnych wiadomościach. Ten przegląd zawiera tylko pozostałe nowe oferty.</div>
</div></body></html>`;

const textRows = sorted.map(offer => [
  clean(offer.title),
  `Kraj: ${clean(offer.country) || 'brak danych'}`,
  `Dziedzina: ${clean(offer.area) || 'brak danych'}`,
  `Termin MSZ: ${clean(offer.mszDeadline) || 'sprawdź w ogłoszeniu'}`,
  offer.bestEntryRole ? `Potencjalna rola: ${clean(offer.bestEntryRole)}` : '',
  `Ogłoszenie: ${offer.url}`,
].filter(Boolean).join('\n')).join('\n\n');

let checksum = 2166136261;
const signature = sorted.map(offer => `${offer.offerId}:${offer.contentHash}`).join('|');
for (let i = 0; i < signature.length; i += 1) {
  checksum ^= signature.charCodeAt(i);
  checksum = Math.imul(checksum, 16777619);
}

return [{ json: {
  fromEmail: payload.fromEmail,
  toEmails,
  offerIds: sorted.map(offer => offer.offerId),
  digestKey: `twinning-digest/${(checksum >>> 0).toString(16)}`,
  subject: `TWINNING — przegląd pozostałych nowych ofert (${sorted.length})`,
  html,
  text: `Pozostałe nowe fiszki Twinning (${sorted.length})\n\n${textRows}`,
} }];
