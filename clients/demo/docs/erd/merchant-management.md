# Merchant Management Data Model

Covers the merchant lifecycle: contacts, bank accounts, API keys, payout schedules, and disputes.

**API key design:** Keys are environment-scoped (TEST vs LIVE) with granular permissions stored as JSONB. The actual key is never stored — only a hash. The `prefix` field (e.g., `npk_live_`) allows quick identification without exposing the secret.

**Payout schedules** link to a specific bank account and support DAILY, WEEKLY, or MONTHLY frequency with configurable minimum payout amounts.
