# Stakeholder-Specific Language

## Purpose
Capture how different stakeholders and teams refer to the same concepts. This is the raw material for identifying synonyms, conflicts, and the eventual canonical glossary.

## Session guide
Run 30-minute interviews with each key stakeholder. For each:

1. Ask: "Walk me through your typical workflow involving [domain]. What do you call the key things you work with?"
2. Ask: "When you say [term], what exactly do you mean?"
3. Ask: "Do other teams use different words for the same thing?"
4. Listen for jargon, abbreviations, and assumed definitions.

Record verbatim — do not normalize yet.

## Capture

## Priya Sharma (Product Owner, Payments)
- **"transaction"** — a single payment attempt, whether it succeeds or fails; the core unit of everything we do
- **"auth"** — short for authorization; the step where we check if the card is good and reserve funds
- **"capture"** — when we actually charge the card after auth; sometimes called "settling" by merchants
- **"settlement"** — the batch process where money moves from acquirer to merchant; happens overnight
- **"refund"** — merchant gives money back; always tied to a specific original transaction
- **"chargeback"** — when the consumer's bank forces a reversal; completely different from a refund
- **"payment method"** — whatever the consumer pays with: card, bank transfer, digital wallet
- Notes: Priya distinguishes clearly between "refund" (voluntary, merchant-initiated) and "chargeback" (involuntary, bank-initiated). She says the fraud team blurs this line.

## Marcus Webb (Payments Architect, Platform Engineering)
- **"txn"** — abbreviation for transaction used in all code and APIs
- **"pre-auth"** — what product calls "auth"; technically it is an authorization hold
- **"void"** — canceling an auth before capture; product sometimes calls this a "cancellation"
- **"settlement batch"** — the daily file we send to the acquirer; contains all captured txns
- **"idempotency key"** — client-generated UUID to prevent duplicate processing on retries
- **"webhook event"** — notification we fire when a txn changes state; merchants subscribe to these
- **"tokenization"** — replacing PAN with a token; we never store raw card numbers
- Notes: Marcus uses technical terms (PAN, BIN, MCC) that product and fraud teams don't use. He says "settlement" in the gateway means something different from "settlement" in the ledger.

## Elena Rodriguez (Fraud Operations Lead, Risk & Compliance)
- **"fraud case"** — an investigation opened when our risk engine flags a suspicious transaction
- **"risk score"** — numeric score (0-1000) assigned to every transaction in real time
- **"dispute"** — when a cardholder formally challenges a charge through their bank
- **"chargeback"** — the financial reversal that results from a lost dispute; we eat the cost
- **"false positive"** — a legitimate transaction we incorrectly blocked; our biggest pain point
- **"representment"** — when we fight a chargeback by providing evidence the charge was valid
- Notes: Elena uses "customer" to mean the consumer (cardholder), while product uses "customer" to mean the merchant. This causes confusion in cross-team meetings.

## David Kim (Merchant Integrations Lead, Partner Engineering)
- **"merchant"** — the business entity; has a legal name, DBA name, and MCC code
- **"merchant account"** — the financial account where we track their balance and payouts
- **"payout"** — when we send accumulated settlement funds to the merchant's bank account
- **"fee schedule"** — the pricing contract: per-txn fees, monthly fees, chargeback fees
- **"integration tier"** — bronze/silver/gold based on API access level and support SLA
- **"onboarding"** — the process of getting a new merchant set up: KYC, contract, API keys
- Notes: David uses "customer" exclusively to mean the merchant (business customer). He was confused when fraud ops referred to "customer disputes" meaning consumer complaints.

## Example

> ## Jane Chen (Product Owner, Payments)
> - **"transaction"** — a single payment attempt, whether it succeeds or fails
> - **"auth"** — the authorization step before capture; engineering calls this "pre-auth"
> - **"settlement"** — when money actually moves; finance calls this "reconciliation"
> - Notes: Jane distinguishes between "refund" (merchant-initiated) and "reversal" (system-initiated)

## Completion criteria
- [x] At least 3 stakeholders interviewed
- [x] 10+ unique terms captured
- [x] Each term has a stakeholder-attributed definition
- [x] Known disagreements flagged
