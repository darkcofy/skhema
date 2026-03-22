# NovaPay Platform

NovaPay is a digital payments platform processing 2M+ transactions per day across UK and EU markets. The platform enables consumer-to-merchant payments via mobile app, web checkout, and NFC, with real-time fraud detection and automated compliance reporting.

**Scope of this document:**
- Core payment processing (authorization, capture, settlement, refunds)
- Real-time fraud detection and case management
- Merchant management (onboarding, payouts, disputes)
- Analytics and data platform
- Production infrastructure and disaster recovery

**Key architectural principles:**
- Event-driven: Kafka as the backbone for async communication between services
- Double-entry ledger: Every financial movement is recorded as a balanced debit/credit pair
- Client isolation: Each client's data and configuration are fully separated
- Stdlib-first: Minimal external dependencies for portability
