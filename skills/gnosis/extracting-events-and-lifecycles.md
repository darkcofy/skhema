---
name: Extracting events and lifecycle states from process documentation
description: Reads process docs, runbooks, state diagrams, and transcripts and extracts domain events and entity lifecycles. Produces entries for gnosis `04_behavior/lifecycle-states.yaml` and `04_behavior/events.yaml`. Use at gnosis stage 4 (behaviour) once concepts from stage 2 are stable.
---

## When to use this skill

- You have stable candidate concepts from stage 2 (e.g. Transaction, Order, Fraud Case).
- Source material describes *what happens to* those concepts over time — state transitions, triggering events, business rules, runbooks.
- You need to populate both `lifecycle-states.yaml` (state machines) and `events.yaml` (domain events) to feed stage 5 formalisation.

## Inputs

1. **Process documentation** — runbooks, SOPs, state transition diagrams, retrospectives describing failure modes.
2. **Transcripts** — stakeholders describing happy paths, edge cases, and failure recovery.
3. **`02_concepts/candidate-concepts.yaml`** — so you only extract lifecycles for known concepts.

## Output format

Two files, both YAML.

### `04_behavior/lifecycle-states.yaml`

```yaml
- entity: Transaction
  states:
    - name: initiated
      description: Customer has initiated payment but authorisation hasn't started.
    - name: authorised
      description: Card network has confirmed funds available; awaiting capture.
    - name: captured
      description: Funds have been pulled; transaction is complete from the payments side.
    - name: declined
      description: Authorisation failed (soft or hard decline).
    - name: refunded
      description: Merchant has reversed a previously-captured transaction.
    - name: disputed
      description: Customer has opened a chargeback; funds may still be held.
  transitions:
    - from: initiated
      to: authorised
      trigger: authorisation_approved
    - from: initiated
      to: declined
      trigger: authorisation_declined
    - from: authorised
      to: captured
      trigger: eod_batch_close
    - from: captured
      to: refunded
      trigger: refund_initiated
    - from: captured
      to: disputed
      trigger: chargeback_opened
  invariants:
    - A transaction cannot leave the `declined` state once entered.
    - A disputed transaction can be won or lost but does not return to `captured`.
  source_quotes:
    - quote: "Each transaction sits against one payment method, and goes through auth then capture"
      source: Alice Chen
      date: 2026-04-12
```

### `04_behavior/events.yaml`

```yaml
- name: TransactionAuthorised
  domain: payments
  entity: Transaction
  triggered_by: Card network approval response
  carries:
    - transaction_id
    - authorisation_code
    - authorised_amount
    - authorised_at
  consumed_by:
    - Ledger
    - Fraud engine
  source_quotes:
    - quote: "Auth approves, we move to captured at EOD"
      source: Alice Chen
      date: 2026-04-12

- name: ChargebackOpened
  domain: payments
  entity: Transaction
  triggered_by: Customer dispute filed with issuing bank
  carries:
    - transaction_id
    - reason_code
    - opened_at
  consumed_by:
    - Ops dashboard
    - Fraud engine
```

## Step-by-step

1. **For each concept you have evidence for, ask two questions:**
   - What *states* does it pass through? → lifecycle.
   - What *events* signal state transitions or other notable occurrences? → events.
2. **Sketch the state machine.** From happy path:
   - What state does the entity start in?
   - What's the terminal (successful) state?
   - What side-branches exist? (failure, reversal, dispute, cancel)
3. **Name every transition explicitly.** Each transition needs `from`, `to`, `trigger`. The trigger is an event name; this is where lifecycles and events connect.
4. **Write invariants.** Business rules that always hold:
   - "Once declined, a transaction cannot be re-authorised" (terminal state)
   - "A disputed transaction's amount is immutable" (invariant across states)
5. **Enumerate events.** For each triggering/notable event:
   - `name` — past-tense, SubjectVerbed form (TransactionAuthorised, not AuthoriseTransaction)
   - `entity` — the concept the event is about
   - `triggered_by` — who or what emits it
   - `carries` — the payload fields (even if you don't have the full schema yet)
   - `consumed_by` — systems or processes known to react
6. **Cite sources.** Every lifecycle and event gets at least one source quote linking it to a stakeholder or document.

## Quality checks

- [ ] Every lifecycle entity corresponds to a concept in `candidate-concepts.yaml`
- [ ] Every transition has `from`, `to`, `trigger`, and the trigger appears as an event name in `events.yaml`
- [ ] Every event name is past-tense SubjectVerbed form
- [ ] Every lifecycle has at least one terminal state
- [ ] Every lifecycle has at least one source quote
- [ ] Invariants are testable statements, not opinions
- [ ] No events without a known `entity` (orphan events indicate missing concepts)

## Examples

### Input

> "When a fraud case is opened it starts as flagged. Our analyst reviews, either clearing it — that moves to resolved-clear — or confirming fraud — that moves to resolved-confirmed. If the analyst can't decide within 24h it escalates. Once it's resolved-confirmed, we notify the bank."

### Output

**Lifecycle:**

```yaml
- entity: FraudCase
  states:
    - name: flagged
      description: Case automatically raised, awaiting analyst review
    - name: under_review
      description: Analyst has picked up the case
    - name: escalated
      description: 24h timeout reached without analyst decision
    - name: resolved_clear
      description: Analyst confirmed no fraud
    - name: resolved_confirmed
      description: Analyst confirmed fraud; bank notification pending/sent
  transitions:
    - from: flagged
      to: under_review
      trigger: FraudCaseClaimed
    - from: flagged
      to: escalated
      trigger: FraudCaseTimeout24h
    - from: under_review
      to: resolved_clear
      trigger: FraudCaseCleared
    - from: under_review
      to: resolved_confirmed
      trigger: FraudCaseConfirmed
  invariants:
    - resolved_clear and resolved_confirmed are terminal
    - 24h timer starts from flagged state entry
```

**Events:**

```yaml
- name: FraudCaseFlagged
  entity: FraudCase
  triggered_by: Automated fraud engine
  carries: [case_id, transaction_id, risk_score, flagged_at]

- name: FraudCaseConfirmed
  entity: FraudCase
  triggered_by: Analyst decision
  carries: [case_id, analyst_id, resolution_notes, confirmed_at]
  consumed_by:
    - Bank notification service
```

## Anti-patterns

- **Lifecycles for concepts without evidence.** If the transcripts don't describe state transitions for "Merchant", don't invent a merchant lifecycle. Skip it.
- **Present-tense event names.** `AuthorisingTransaction` is wrong; `TransactionAuthorised` is right. Events describe things that *have happened*.
- **Missing terminal states.** Every practical lifecycle has at least one terminal state. If you can't identify one, the state machine is probably wrong.
- **Conflating events with commands.** `RefundTransaction` is a command (imperative); `TransactionRefunded` is the event the command emits. Your output is events, not commands.
- **Skipping invariants.** They feel optional but they're where implicit business rules get captured. Always try to write at least one.
- **Infinite-state machines.** If you find yourself with 20+ states for one entity, you're probably mixing two concepts — split them.
