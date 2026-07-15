const tz = 'Europe/Warsaw';
const daysLookback = 7;
const pageSize = 100;
const now = new Date();
const inWarsaw = new Intl.DateTimeFormat('sv-SE', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit' });
const formatDate = (date) => inWarsaw.format(date);
const dateTo = formatDate(now);
const dateFrom = formatDate(new Date(now.getTime() - daysLookback * 24 * 60 * 60 * 1000));
const getIsoWeek = (date) => {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
};
const ctx = {
  dateFrom,
  dateTo,
  modifiedSince: `${dateFrom}T00:00`,
  daysLookback,
  weekNumber: getIsoWeek(now),
  year: Number(dateTo.slice(0, 4)),
  timezone: tz,
  fromEmail: 'legislacja@send.familyos.pl',
  toEmail: 'michalreczek@gmail.com'
};
const base = 'https://api.sejm.gov.pl/sejm/term10';
const eliBase = 'https://api.sejm.gov.pl/eli/acts/search';
const items = [
  { source: 'prints', kind: 'prints', url: `${base}/prints`, dateContext: ctx },
  { source: 'proceedings-current', kind: 'proceedings', url: `${base}/proceedings/current`, dateContext: ctx },
  { source: 'voting-days', kind: 'voting-days', url: `${base}/votings`, dateContext: ctx }
];

// API Sejmu zwraca najwyzej 100 rekordow. Pobieramy kolejne strony,
// aby newsletter nie opieral sie tylko na pierwszych 100 interpelacjach.
for (let offset = 0; offset <= 1000; offset += pageSize) {
  items.push({
    source: `interpellations-${offset}`,
    kind: 'interpellations',
    url: `${base}/interpellations?modifiedSince=${encodeURIComponent(ctx.modifiedSince)}&sort_by=-lastModified&limit=${pageSize}&offset=${offset}`,
    dateContext: ctx
  });
}
for (let offset = 0; offset <= 500; offset += pageSize) {
  items.push({
    source: `writtenQuestions-${offset}`,
    kind: 'writtenQuestions',
    url: `${base}/writtenQuestions?modifiedSince=${encodeURIComponent(ctx.modifiedSince)}&sort_by=-lastModified&limit=${pageSize}&offset=${offset}`,
    dateContext: ctx
  });
}

// ELI: wyszukujemy po dacie ogloszenia (promulgation), a nie po dacie
// modyfikacji rekordu, ktora potrafi oznaczyc stary akt jako nowy.
for (const publisher of ['DU', 'MP']) {
  for (let offset = 0; offset <= 200; offset += pageSize) {
    const query = `publisher=${publisher}&pubDateFrom=${ctx.dateFrom}&pubDateTo=${ctx.dateTo}&limit=${pageSize}&offset=${offset}&sortBy=promulgation&sortDir=desc`;
    items.push({ source: `eli-${publisher.toLowerCase()}-${offset}`, kind: 'eli', publisher, url: `${eliBase}?${query}`, dateContext: ctx });
  }
}

for (let i = 0; i <= daysLookback; i += 1) {
  const date = formatDate(new Date(now.getTime() - i * 24 * 60 * 60 * 1000));
  items.push({ source: `committees-${date}`, kind: 'committees', date, url: `${base}/committees/sittings/${date}`, dateContext: ctx });
}
return items.map((json) => ({ json }));
