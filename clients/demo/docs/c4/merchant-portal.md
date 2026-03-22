# Merchant Portal Components

The Merchant Portal is a React SPA backed by a Node.js BFF (backend-for-frontend) that aggregates data from multiple internal services.

**Key modules:**
- **Transaction Viewer** — search, filter, and export transaction history with real-time status updates
- **Payout Manager** — configure payout schedules, manage bank accounts, and track payout status
- **Dispute Manager** — handle chargebacks, upload evidence, and track resolution deadlines

**Authentication:** SSO via OIDC to the Identity Provider. The BFF validates JWTs through the Auth Gateway. All merchant data access is scoped by `merchant_id` — no cross-tenant visibility.
