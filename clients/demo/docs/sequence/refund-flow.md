# Refund Processing

Refund flow initiated by a merchant through the portal. Supports both full and partial refunds.

**Validations:** The Payment Engine checks that the original transaction exists and the refund amount does not exceed the captured amount. Refunds against uncaptured (auth-only) transactions are rejected — those should be voided instead.

**Ledger impact:** Every refund creates a reversal entry in the ledger, maintaining the double-entry invariant.
