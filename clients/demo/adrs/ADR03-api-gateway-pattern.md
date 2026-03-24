# ADR03: API Gateway as Unified Ingestion Entry Point

## Status
Accepted

## Context
NovaPay exposes payment capabilities to three distinct caller populations: merchants integrating
directly via REST, partner platforms using GraphQL for flexible data queries, and internal
microservices communicating asynchronously via the message broker. Each population has different
authentication models, rate limits, and payload contracts.

Without a unified entry point, each backend service must independently implement TLS termination,
OAuth token validation, rate limiting, request logging, and API versioning. This duplicated logic
has already caused inconsistencies: one service accepted expired tokens for six days before the
bug was caught. Merchants reported inconsistent error response shapes across endpoints.

Additionally, PCI-DSS requires that all cardholder data entering the platform be immediately
tokenized. This must happen at the ingestion boundary, before raw card data reaches any internal
service. Enforcing this at each individual service is error-prone.

## Decision
A single API gateway will serve as the authoritative entry point for all external traffic.
The gateway enforces authentication (OAuth 2.0 via the identity_provider), rate limiting per
merchant tier, and PCI tokenization at the boundary. Raw card data never reaches internal
services; the gateway exchanges it for a payment method token before routing.

The rest_api and graphql_endpoint integration elements are exposed exclusively behind this
gateway. The auth_gateway collaborates with the api_gateway to enforce security policies.
Internal service-to-service communication continues via the message_broker without traversing
the gateway.

<!-- skhema:elements api_gateway, rest_api, graphql_endpoint, auth_gateway, identity_provider -->
<!-- gnosis:concepts PaymentMethod, Merchant, WebhookEvent, Transaction -->

## Consequences
**Easier:**
- Authentication, rate limiting, and tokenization logic implemented once, enforced uniformly
- Centralized request logging provides a complete audit trail of all external interactions
- API versioning and deprecation managed at the gateway without coordinating backend deployments
- PCI scope is cleanly bounded: no raw card data crosses the gateway into internal services

**Harder:**
- The gateway becomes a critical single point of failure; it must be deployed with high availability and careful capacity planning
- Latency budget is consumed by gateway processing; tokenization and auth validation add overhead to every request
- Gateway configuration sprawl (routing rules, rate limit tiers, plugin chains) requires its own change management discipline
- Debugging requires correlating gateway request logs with downstream service traces
