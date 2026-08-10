import json

from twinning_monitor import extract_offer, list_active_offers


def main():
    listing = list_active_offers(lookback_days=180, max_offers=30)
    offers = listing.get("activeOffers", [])
    if not offers:
        raise SystemExit("Smoke failed: no active Twinning offers found")
    first = offers[0]
    extracted = extract_offer(first["url"])
    if not extracted.get("analysisText") or not extracted.get("primaryDocument"):
        raise SystemExit("Smoke failed: no readable primary fiche")
    print(
        json.dumps(
            {
                "activeOffers": len(offers),
                "listingErrors": listing.get("errors", []),
                "firstOffer": first.get("offerId"),
                "deadline": first.get("mszDeadline"),
                "primaryDocument": extracted.get("primaryDocument"),
                "analysisCharacters": len(extracted.get("analysisText", "")),
            },
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
