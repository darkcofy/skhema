# Core Transaction Data Model

The central transaction model linking merchants, consumers, payment methods, transactions, refunds, and ledger entries.

**Key relationships:**
- A transaction belongs to exactly one merchant and one consumer
- A transaction uses exactly one payment method (card, bank, or wallet)
- Refunds are always linked to a parent transaction — orphan refunds are not allowed
- Ledger entries provide the audit trail: every status change (auth → capture → settle) creates a new entry

**Status lifecycle:** `CREATED → AUTHORIZED → CAPTURED → SETTLED` (happy path) or `→ REFUNDED` / `→ FAILED` at any point.
