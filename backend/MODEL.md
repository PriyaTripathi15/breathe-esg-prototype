# MODEL

## Design Goals
The model is built around three requirements from the assignment:

1. Multi-tenancy so one client's data never mixes with another's.
2. Full provenance from source file to normalized review row.
3. A review state machine that supports analyst sign-off before audit lock.

The prototype uses a simple relational shape because the hard part is not computation, it is keeping the provenance legible.

## Core Entities

### Tenant
Represents a client company. Every downstream record belongs to exactly one tenant.

Why it exists:
- Keeps source uploads, normalized records, and review actions tenant-scoped.
- Makes the prototype safe to extend into a real multi-customer system.

### SourceBatch
Represents one intake event for a source file or API pull.

Fields that matter:
- `source_type`: `sap`, `utility`, or `travel`.
- `source_system`: the upstream system name such as SAP ECC, Utility Portal, or Concur.
- `source_format`: the concrete shape handled in this MVP, such as CSV or JSON.
- `original_filename` and `source_reference`: the source-of-truth anchor for audits.

Why it exists:
- Multiple files can arrive from the same source type over time.
- Analysts need to know which exact batch produced a row.

### RawRecord
Stores the immutable upstream payload.

Why it exists:
- Raw payloads are preserved exactly as ingested.
- A normalized record is never the only evidence of what arrived.
- If mapping logic changes later, the raw layer still lets us replay.

### EmissionRecord
This is the review row analysts see.

It contains both the business meaning and the audit metadata:
- `scope` for Scope 1 / 2 / 3 categorization.
- `category` for the emissions activity bucket.
- `quantity`, `original_unit`, `normalized_quantity`, and `normalized_unit` for unit normalization.
- `co2e_kg` for the calculated emissions value.
- `review_status`, `edited_at`, `approved_at`, and `locked_at` for lifecycle tracking.
- `source_reference`, `source_filename`, `external_id`, and `raw_record` for provenance.

## Review State
The review workflow is intentionally simple:

- `pending`: loaded, parsed, and ready for analyst review.
- `flagged`: suspicious or likely out-of-family.
- `approved`: accepted by an analyst.
- `rejected`: not fit for audit.
- `locked`: approved and frozen for audit trail purposes.

The prototype treats approval as the point where the row becomes effectively locked.

## Unit Normalization
The goal is not to force every activity into one measurement system. The goal is to normalize each source into a canonical unit that makes the category usable downstream.

Examples used in the prototype:
- SAP fuel rows normalize to `kWh` so fuels can be compared by energy content.
- Utility rows stay in `kWh` because that is already the canonical electricity unit.
- Travel rows normalize to `passenger_km`, `room_night`, or `vehicle_km` depending on the category.
- Procurement rows normalize to `kg` to make material volume easier to compare.

This is a pragmatic normalization layer, not a universal ontology.

## Audit Trail
The audit story is split across the raw and normalized layers:

- Raw data is immutable.
- Normalized rows link back to the exact raw record.
- Source batches preserve which file or feed created the row.
- Review timestamps show when the row changed state.
- Analyst identity fields are included even though this prototype does not add authentication.

## Scope Mapping
The prototype maps the sources as follows:

- SAP fuel rows -> Scope 1.
- SAP procurement rows -> Scope 3.
- Utility electricity -> Scope 2.
- Travel rows -> Scope 3.

## What I Would Change in a Larger Build
If this moved beyond prototype scope, I would split emission factors, unit conversion rules, and review workflow into separate versioned tables so they can be governed independently from the ingestion rows.