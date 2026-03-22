# Container Overview

The container view decomposes the NovaPay platform into its core services. The architecture follows an event-driven pattern with Kafka as the central message backbone.

**Payment flow:** Mobile App → Payment Engine → Fraud Detector (risk check) → Card Network (authorization) → Ledger (recording) → Kafka (event bus) → Notification Service + Webhook Engine

**Data stores:**
- PostgreSQL (operational DB) for transactional data
- Redis (cache layer) for fraud feature lookups and idempotency
- Kafka for event streaming between services

**Key design decision:** The Ledger Service is implemented in Rust for correctness guarantees around double-entry bookkeeping. All other services use Java/Spring Boot, Go, or Python depending on their I/O vs. compute profile.
