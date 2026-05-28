# Decisions

This section records the ambiguities I resolved and what I would still ask the PM.

## SAP
Chosen subset:
- Flat CSV exports from SAP ECC instead of IDocs, BAPIs, or OData.
- Fuel and procurement lines only.

Why:
- A CSV export is the most realistic lowest-friction intake for a prototype.
- IDocs and BAPIs add integration overhead without changing the core review problem.
- CSV also lets me show German column headers, mixed units, and plant codes in one file.

What I ignored:
- Deep SAP master-data joins.
- Complex document hierarchies.
- Real IDoc segment parsing.

What I would ask the PM:
- Which SAP system versions and export templates are actually in scope?
- Do we need the importer to resolve plant codes against a master table, or is that a downstream enrichment step?

## Utility
Chosen subset:
- Utility portal CSV export for electricity.

Why:
- Facilities teams usually get this data in CSV or portal export form before anything else.
- PDF OCR is a different product surface and would have pulled the prototype away from the ingestion/review problem.
- Billing periods and estimated reads are still realistic in CSV form.

What I ignored:
- OCR from PDF invoices.
- Utility-specific tariff engines.
- Interval-meter time series.

What I would ask the PM:
- Do we need to model time-of-use tariffs and demand charges, or only monthly billed electricity?
- Should estimated reads be auto-flagged or only annotated?

## Travel
Chosen subset:
- Concur-style structured travel payloads, represented as JSON.
- Flights, hotels, and ground transport.

Why:
- Travel platforms commonly expose itinerary-style payloads or exports with category-specific fields.
- JSON is a realistic API shape for modern travel tools and lets me show different normalization logic per category.

What I ignored:
- Loyalty program details.
- Per-diem logic.
- Expense approval workflows unrelated to emissions review.

What I would ask the PM:
- Which travel source should be considered authoritative when itinerary and expense records disagree?
- Are we expected to estimate flight distance from airport codes when distance is missing?

## Multi-Tenancy
Chosen subset:
- Tenant-scoped records with a tenant selector in the dashboard.

Why:
- It proves the model handles multiple clients without adding auth complexity.

What I ignored:
- Role-based access control.
- Per-tenant permissions and SSO.

What I would ask the PM:
- How many review roles exist, and who is allowed to override a flagged row?

## Review Workflow
Chosen subset:
- Pending, flagged, approved, rejected, and locked states.
- Inline approval from the dashboard.

Why:
- It is enough to show analyst sign-off before audit lock.

What I ignored:
- Multi-step collaborative approvals.
- Comment threads and escalations.

What I would ask the PM:
- Is approved the same as locked, or do we need a separate final lock step?

## Source-of-Truth Tracking
Chosen subset:
- Store the raw payload, batch reference, row id, timestamps, and edited-by fields.

Why:
- This gives a full provenance chain without overbuilding a data warehouse.

What I ignored:
- Full event sourcing.
- Immutable append-only change events for every field edit.

What I would ask the PM:
- Do auditors need field-level diff history or is row-level provenance enough?