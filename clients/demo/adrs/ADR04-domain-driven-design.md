# ADR04: Domain-Driven Design for Payment Platform Boundaries

## Status
Accepted

## Context
NovaPay began as a monolithic Rails application. As feature scope expanded to include fraud
detection, merchant onboarding, settlement processing, and payout disbursement, the codebase
became entangled: the Transaction model accumulated hundreds of attributes and methods spanning
payment processing, risk scoring, billing calculation, and reporting. Any change to the
transaction flow required coordinating across fraud, billing, and merchant teams simultaneously.

Three incidents in Q3 were traced to implicit coupling across what should be independent business
capabilities. A schema change to support new card network fields broke the fraud scoring pipeline
because both were reading from the same ActiveRecord model with conflicting interpretations of
the same columns.

We need clear ownership boundaries that allow teams to evolve their subdomain independently while
preserving well-defined integration contracts at the boundaries.

## Decision
We will organize the NovaPay platform around explicit bounded contexts derived from the domain
model: Core Payments (Transaction, PaymentMethod, Acquirer, Issuer), Merchant Management
(Merchant, Account, FeeSchedule, Payout), and Fraud & Risk (FraudCase, Chargeback).

Each bounded context owns its data store, defines its own internal model, and communicates
with other contexts only through published domain events (via the event_stream) or explicit
API contracts (via api_service). Concepts that appear in multiple contexts (e.g., Transaction)
have context-specific representations — the fraud context's view of a transaction includes risk
signals not present in the core payments representation.

The master_data_svc manages cross-context reference data (merchant identity, fee schedules)
and serves as the authoritative source for shared lookup data. The data_catalog documents
the published contracts between contexts.

<!-- skhema:elements event_stream, api_service, master_data_svc, data_catalog, policy_engine -->
<!-- gnosis:concepts Transaction, Merchant, FraudCase, Chargeback, PaymentMethod, Account, FeeSchedule, Payout, Acquirer, Issuer -->

## Consequences
**Easier:**
- Teams own their bounded context end-to-end: schema, logic, and deployment are within team control
- Fraud team can evolve risk model without coordinating with the core payments team
- Integration contracts are explicit and versioned, making breaking changes visible before deployment
- The domain model in code reflects the language used by business stakeholders, reducing translation errors

**Harder:**
- Cross-context queries (e.g., merchant settlement report joining fraud flags) require choreographing data from multiple contexts
- Distributed transactions spanning contexts require saga patterns rather than database transactions
- Initial decomposition work is significant; extracting the monolith requires careful data migration and dual-write periods
- Defining correct context boundaries is difficult and mistakes are expensive to reverse once teams have built around them
