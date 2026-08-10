const fs = require('fs');
const path = require('path');
const vm = require('vm');

const sourcePath = path.join(__dirname, 'twinning_build_email.js');
const outputPath = process.argv[2] || path.join(__dirname, '..', '.tmp-twinning-email.html');
const code = fs.readFileSync(sourcePath, 'utf8');
const fixture = {
  notificationType: 'new',
  offerId: 'GM 24 NDICI AG 01 26',
  contentHash: 'fixture-hash',
  title: 'Support to the Food Safety and Quality Authority in The Gambia',
  country: 'Gambia',
  area: 'Rolnictwo',
  reference: 'GM 24 NDICI AG 01 26',
  mszDeadline: '29 września 2026 r.',
  beneficiaryDeadline: '1 października 2026 r.',
  url: 'https://twinning.msz.gov.pl/fiszki-twinning/example/',
  attachmentUrl: 'https://twinning.msz.gov.pl/media/example.zip',
  primaryDocument: 'Annex C1.pdf',
  output: {
    purpose: 'Wzmocnienie systemu bezpieczeństwa żywności i kontroli SPS w sektorze ogrodniczym.',
    decisionSummary: 'Oferta jest właściwa dla ekspertów administracji publicznej z doświadczeniem w bezpieczeństwie żywności, SPS i wdrażaniu prawa UE.',
    soughtProfiles: ['Resident Twinning Adviser (RTA)', 'Project Leader', 'Eksperci krótkoterminowi ds. SPS i laboratoriów'],
    mandatoryRequirements: ['Wykształcenie wyższe', 'Co najmniej 10 lat doświadczenia zawodowego', 'Biegła znajomość języka angielskiego'],
    keyTasks: ['Wsparcie zmian regulacyjnych', 'Budowa zdolności instytucjonalnej FSQA', 'Szkolenia i procedury kontroli'],
    risksOrCaveats: ['Ograniczona infrastruktura laboratoryjna', 'Wyjazdy terenowe w porze deszczowej'],
    budget: '1 000 000 EUR',
    duration: '24 miesiące',
    locationAndTravel: 'Gambia; RTA na miejscu, eksperci ad hoc podczas misji',
    language: 'angielski',
    whoCanApply: 'Polska jednostka administracji publicznej albo Mandated Body; ekspert indywidualny przez uprawnioną instytucję.',
    fitBand: 'borderline',
    fitScore: 68,
    fitReason: 'Zakres regulacyjny i procesowy może pasować, ale wymagania sektorowe trzeba zweryfikować.',
    bestEntryRole: 'Short-Term Expert / ekspert ad hoc ds. procedur administracyjnych',
    internationalExperienceRequirement: 'Wcześniejsze doświadczenie międzynarodowe jest mile widziane, ale nie wskazano go jako obowiązkowego dla wszystkich STE.',
  },
};

const result = vm.runInNewContext(`(() => { ${code} })()`, { $json: fixture });
if (!Array.isArray(result) || !result[0]?.json?.html) throw new Error('Email builder did not return HTML');
fs.writeFileSync(outputPath, result[0].json.html, 'utf8');
process.stdout.write(JSON.stringify({ outputPath, subject: result[0].json.subject, recipientsReady: true }));
