# ADR01: Event-Driven Ingestion Architecture

## Status
Accepted

## Context
NovaPay processes millions of payment transactions daily across card networks, bank transfers,
and third-party wallets. Each transaction generates multiple downstream side-effects: fraud
scoring, settlement batching, merchant webhooks, analytics aggregation, and ledger updates.

A synchronous request-response model for ingestion creates tight coupling between the payment
authorization path and every downstream consumer. A network timeout in analytics must not delay
an authorization response to a merchant. Additionally, peak load during end-of-day settlement
windows creates burst traffic that synchronous consumers cannot absorb without scaling in lockstep
with the ingestion tier.

We need an architecture that decouples ingestion from processing, provides durable event replay,
and allows new consumers to be added without modifying the ingestion path.

## Decision
We will adopt an event-driven ingestion architecture backed by a persistent event stream.
All payment events (TransactionAuthorized, TransactionSettled, ChargebackOpened, etc.) will be
published to a central event stream immediately upon ingestion. Downstream systems subscribe
independently and process at their own pace.

The event stream becomes the system of record for raw events, with consumers maintaining their
own projections. The CDC pipeline will capture changes from operational databases to feed
events for legacy systems that cannot publish directly.

<!-- skhema:elements event_stream, cdc_pipeline, stream_processor, message_broker -->
<!-- gnosis:concepts Transaction, WebhookEvent, SettlementBatch -->

## Consequences
**Easier:**
- New consumers can subscribe to the event stream without changes to producers
- Replay capability enables re-processing after bug fixes or new consumer onboarding
- Fraud scoring, analytics, and webhook delivery are fully decoupled from the authorization path
- Peak load is absorbed by the stream; consumers scale independently

**Harder:**
- Eventual consistency means downstream views may lag behind the event stream
- Operational complexity increases: the event stream requires monitoring, retention policies, and consumer lag tracking
- Debugging distributed flows requires distributed tracing across producer and consumer boundaries
- Schema evolution requires backward-compatible event formats across all consumer versions
