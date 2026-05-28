# Sources

## SAP
What I researched:
- SAP export patterns from ECC-style reporting and flat-file extracts.

What I learned:
- SAP data is often flattened before it reaches analysts.
- Column names can be localized, plant codes are rarely meaningful without lookup tables, and units are inconsistent.
- For an MVP, a CSV export is the easiest realistic shape to handle while still exposing the hard parts.

What the sample data looks like:
- German headers such as `Buchungsdatum`, `Werk`, `Kraftstoff`, `Menge`, and `Einheit`.
- Mixed fuel and procurement lines.
- Units such as liters, gallons, cubic meters, kilograms, and counts.

What would break in a real deployment:
- Master-data joins for plant and material codes.
- Export template drift across SAP configurations.
- Row-level reconciliation back to SAP document numbers if the source team changes the export.

## Utility
What I researched:
- Utility portal CSV exports and billing-style electricity data.

What I learned:
- Facilities teams usually get periodic billing data with meter ids, bill periods, usage, cost, and currency.
- Billing periods do not always align to calendar months.
- Estimated reads and tariff labels are common and should be flagged for review.

What the sample data looks like:
- `meter_id`, `billing_period_start`, `billing_period_end`, `kwh`, `cost`, `currency`, `tariff`, and `facility`.
- Some rows are inferred or need reconciliation because the period or read type is suspicious.

What would break in a real deployment:
- PDF-only utilities would need OCR or vendor-specific scraping.
- Interval meter data would require a different model.
- Locale-specific currency and tax formatting could break naive parsing.

## Travel
What I researched:
- Concur/Navan-style travel payloads and itinerary exports.

What I learned:
- Travel emissions are category-specific.
- Flights often need airport-code based distance estimation when distance is missing.
- Hotels and ground transport behave very differently from flights and should not be forced into one generic travel row.

What the sample data looks like:
- JSON objects for `flight`, `hotel`, and `ground_transport`.
- Flight records may include airport codes and a missing distance so the reviewer can see a derived field.
- Hotel rows carry nights and chain metadata.
- Ground transport rows use distance and mode.

What would break in a real deployment:
- Missing or invalid airport codes.
- Inconsistent itinerary and expense records across systems.
- API rate limits and auth token refresh if the ingestion moved from demo JSON to live API pulls.