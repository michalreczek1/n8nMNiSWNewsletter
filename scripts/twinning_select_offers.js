const cfg = $json;
const toEmails = String(cfg.toEmailsCsv || '')
  .split(',')
  .map(value => value.trim())
  .filter(Boolean);

const offers = Array.isArray(cfg.activeOffers) ? cfg.activeOffers : [];
return offers
  .filter(offer => offer?.offerId && offer?.contentHash && offer?.url)
  .filter(offer => offer.notificationType === 'new' || offer.notificationType === 'updated')
  .map(offer => ({
    json: {
      ...offer,
      fromEmail: cfg.fromEmail,
      toEmails,
      waitSeconds: Number(cfg.waitSeconds || 1),
    },
  }));
