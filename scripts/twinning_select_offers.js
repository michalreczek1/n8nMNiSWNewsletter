const cfg = $json;
const staticData = $getWorkflowStaticData('global');
if (!staticData.sentOffers) staticData.sentOffers = {};

const retentionDays = Number(cfg.retentionDays || 730);
const cutoff = Date.now() - retentionDays * 86400000;
for (const [offerId, value] of Object.entries(staticData.sentOffers)) {
  const sentAt = value?.sentAt ? Date.parse(value.sentAt) : 0;
  if (!sentAt || sentAt < cutoff) delete staticData.sentOffers[offerId];
}

const toEmails = String(cfg.toEmailsCsv || '')
  .split(',')
  .map(value => value.trim())
  .filter(Boolean);

const offers = Array.isArray(cfg.activeOffers) ? cfg.activeOffers : [];
return offers
  .filter(offer => offer?.offerId && offer?.contentHash && offer?.url)
  .filter(offer => staticData.sentOffers[offer.offerId]?.contentHash !== offer.contentHash)
  .map(offer => ({
    json: {
      ...offer,
      notificationType: staticData.sentOffers[offer.offerId] ? 'updated' : 'new',
      fromEmail: cfg.fromEmail,
      toEmails,
      waitSeconds: Number(cfg.waitSeconds || 1),
    },
  }));

