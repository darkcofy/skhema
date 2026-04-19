# Stage 3: System Mapping — not yet populated

Stage 3 of the gnosis flow maps canonical concepts (stage 2) onto real
source systems. For MeshCo that would be: `customer.master_customer` →
`{POS.customers, Commerce.buyers, CRM.accounts}` with authority notes
per field.

This demo stops at stage 2 (concept modelling). Stage 3 is scaffolded
but intentionally empty to keep the demo focused.

To populate: apply the gnosis extraction skills against the source-
system documentation and `candidate-concepts.yaml`. See
`skills/gnosis/` at the repo root for the extraction playbooks.

Expected files (when populated):

- `source-to-canonical.csv` — canonical concept → source table mapping
- `field-mappings.csv` — per-column mapping with type coercions
- `system-overlaps.md` — cases where the same concept lives in multiple
  sources (e.g. "customer" in POS, Commerce, CRM)
- `authority-notes.md` — which source is the system of record for each
  field when sources disagree
