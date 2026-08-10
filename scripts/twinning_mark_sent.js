const payload = $json || {};
if (!payload.offerId || !payload.contentHash) {
  throw new Error('Nie można zapisać stanu Twinning bez offerId i contentHash');
}
const staticData = $getWorkflowStaticData('global');
if (!staticData.sentOffers) staticData.sentOffers = {};
staticData.sentOffers[payload.offerId] = {
  contentHash: payload.contentHash,
  sentAt: new Date().toISOString(),
  recipients: Array.isArray(payload.toEmails) ? payload.toEmails : [],
  resendId: payload.id || payload.resendId || null,
};
return [{ json: { offerId: payload.offerId, sent: true, sentAt: staticData.sentOffers[payload.offerId].sentAt } }];

