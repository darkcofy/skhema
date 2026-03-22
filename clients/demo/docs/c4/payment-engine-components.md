# Payment Engine Components

The Payment Engine is the core orchestrator for the transaction lifecycle. It handles four distinct phases: authorization, capture, refund, and settlement.

**Component responsibilities:**

| Component | Responsibility | Protocol |
|-----------|---------------|----------|
| Auth Handler | Processes incoming authorization requests | REST |
| Capture Handler | Converts authorized transactions to captured | Internal |
| Refund Handler | Full and partial refund processing | REST |
| Settlement Handler | Batches nightly clearing files | SFTP |
| Routing Engine | Selects optimal card processor and route | Internal |
| Idempotency Store | Prevents duplicate transaction processing | Redis |

**Critical path:** Auth Handler → Routing Engine → Card Network takes < 200ms p99. The idempotency store adds ~1ms overhead but prevents costly duplicate authorizations.
