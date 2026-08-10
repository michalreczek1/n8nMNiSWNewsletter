const fs = require('fs');
const path = require('path');
const vm = require('vm');

const sourcePath = path.join(__dirname, 'twinning_build_digest.js');
const outputPath = process.argv[2] || path.join(__dirname, '..', '.tmp-twinning-digest.html');
const code = fs.readFileSync(sourcePath, 'utf8');
const fixture = {
  fromEmail: 'twinning@send.familyos.pl',
  toEmailsCsv: 'michalreczek@gmail.com,wmotylewska@gmail.com',
  pendingOffers: [
    {
      offerId: 'GM-AG-1', contentHash: 'hash-1', country: 'Gambia', area: 'Rolnictwo',
      title: 'Strengthening SPS Systems and Food Safety Control', mszDeadline: '29 września 2026 r.',
      bestEntryRole: 'Short-Term Expert ds. kontroli żywności', url: 'https://example.test/gambia',
    },
    {
      offerId: 'UA-TR-1', contentHash: 'hash-2', country: 'Ukraina', area: 'Transport',
      title: 'Institutional assistance for rail transport reform', mszDeadline: '31 sierpnia 2026 r.',
      bestEntryRole: 'Short-Term Expert ds. kolejnictwa', url: 'https://example.test/ukraine',
    },
  ],
};

const result = vm.runInNewContext(`(() => { ${code} })()`, { $json: fixture });
if (!Array.isArray(result) || !result[0]?.json?.html) throw new Error('Digest builder did not return HTML');
fs.writeFileSync(outputPath, result[0].json.html, 'utf8');
process.stdout.write(JSON.stringify({ outputPath, subject: result[0].json.subject, count: result[0].json.offerIds.length }));
