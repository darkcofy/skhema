---
session_id: 2026-05-04-emma-finance-deepdive
date: 2026-05-04
participants:
  - Emma Ward (Head of Finance Systems)
  - Alfred (interviewer, EY)
duration_min: 45
format: granola-transcript
location: MeshCo HQ, Finance meeting room
---

# Finance deep-dive — monthly close, reverse-ETL, settlement

## 00:00 — Intro and scope

**Alfred:** Thanks for making time, Emma. We spoke briefly at the kickoff
but I wanted to go deeper on the finance side today. Specifically how
monthly close works end-to-end, and where the mesh needs to land for you
to sign off.

**Emma:** Right. So close is the thing I lose sleep over. We run a five-day
close — the books need to be locked by working day five, and we present
to the group finance team on day seven. The whole point of this engagement,
from my side, is that close stops being a heroic effort every month.

**Alfred:** Walk me through what close actually touches.

**Emma:** OK. The raw material is everything commercial. Orders from POS,
orders from commerce, shipments, refunds, returns, chargebacks. All of that
has to roll up into what we call the **finance feed** — that's the stream
of transactions that goes into SAP at the end of each accounting period.

**Alfred:** Finance feed — is that a system or a dataset?

**Emma:** It's a dataset. It used to be a system — there was a service
called FinanceFeed back in 2019 — but we decommissioned the service and
now it's just the thing we call the outbound-to-SAP curated dataset.
The name stuck.

## 08:12 — The accounting period

**Emma:** So the big concept you need in your ontology is the accounting
period. We run on a 4-4-5 calendar, not calendar months — so period 4 isn't
April, it's weeks 14-17 of our fiscal year. Every commercial event gets
stamped with a period the moment it's captured.

**Alfred:** Stamped where?

**Emma:** At the point of sale, and at the point of commerce order capture.
The POS system calls our period service and gets the right period code
back. If a transaction happens in the last hour of a Sunday that's the
period boundary, and the clocks are even a bit off, we get an exception
that Dan from Treasury has to reconcile manually the next morning.

**Alfred:** Who's Dan?

**Emma:** Dan Kowalski — he runs treasury ops. I should have introduced him
at kickoff. He's the one who owns period-boundary exceptions and the
settlement reconciliation. You'll want him on your list. He's in every
month-end post-mortem.

## 15:40 — Settlement

**Alfred:** You mentioned settlement. Talk me through that.

**Emma:** Settlement is where payments meet the books. When a customer pays
with a card, there's an authorisation, then a capture, then a settlement
file comes back from the acquirer — typically T+2. Settlement tells us
what actually landed in the bank account versus what we thought we'd
captured.

**Alfred:** And the gap between captured and settled is the thing you
reconcile?

**Emma:** Exactly. The gap is what we call the **pending settlement
position**. On a good day it's small, on a bad day it's interesting.
Chargebacks come in later and they back out of settlement — that's where
the finance-side view and the payments-side view disagree, because payments
think a chargeback opens, but finance cares about when it settles.

**Alfred:** So settlement is a concept that belongs to finance, not
payments?

**Emma:** It's both. But the **authority** is us — finance owns the
definition of "settled". Payments owns "captured". If your ontology forces
me to pick one, I want settlement to be mine.

## 23:15 — Reverse-ETL and the SAP pipe

**Alfred:** Let's talk about the SAP side. You mentioned cohort and ARR
figures going back into SAP at kickoff.

**Emma:** Right. So finance lives in SAP but the group finance team wants
more than just transactional roll-ups. They want cohort analysis —
customers acquired in period X, revenue tracked monthly from that cohort —
and ARR for the subscription lines. That analysis lives in the analytics
estate, not SAP. We reverse-ETL it.

**Alfred:** And reverse-ETL is running today?

**Emma:** It's running, yes. The implementation is — I'd say fragile. It's
a Census job that runs nightly. The contract's not formalised. When someone
changes a cohort definition upstream we find out when SAP starts showing
the wrong number. That's the bit I want the mesh to fix — I want the
cohort dataset to be a proper data product with a contract, and I want
SAP to be a first-class consumer.

**Alfred:** So cohort is a data product, and the SAP pipe is a consumer of
that data product under a contract.

**Emma:** Yes. And the contract should have the same teeth as every other
data contract — if someone changes what "cohort" means, it breaks the
contract, CI goes red, nobody deploys until we've agreed the change.

## 31:20 — The report package

**Emma:** The other thing that has to come out of close is the **report
package**. That's the bundle of thirty-ish reports that go to group finance
and the board. Today it's generated in Excel from Power BI extracts.
Painful. Every month someone manually reconciles numbers between the BI
layer and SAP because the definitions have drifted.

**Alfred:** Is the report package a data product in its own right?

**Emma:** I'd say it's a *deliverable* — a curated set of views over
multiple data products. Not a data product itself. The individual things
it's built on — revenue by region, margin by category, the cohort view —
those are data products.

## 38:00 — Sign-off criteria

**Alfred:** What does success look like for you at week eight?

**Emma:** Three things. One: close time goes from five days to three. Two:
the reverse-ETL to SAP is on a contract, with breaking-change detection, so
nobody surprises us. Three: the report package reconciles first time —
no manual intervention between what BI shows and what SAP shows — because
the metric definitions are shared.

**Alfred:** That third one — shared metric definitions — is that mostly
Dave's semantic layer story?

**Emma:** Dave owns the how. I own the *what*. If a metric doesn't pass
through his layer, finance doesn't trust it. But if Dave's layer produces
a number that doesn't tie to SAP, it's also broken. We've spent a year
arguing about this and I'm done.

## 43:00 — Wrap

**Alfred:** Last question. When you hear the phrase "data product", what
comes to mind?

**Emma:** Something with a contract, an owner, and an SLO. The SLO bit is
what finance cares about most — if the close feed is three hours late on
day one, my entire team is late for the rest of the week. Freshness SLO is
the one that matters.

**Alfred:** Perfect. I'll circle back with Dan about the settlement flow,
and send you a draft ontology of the finance concepts before the Thursday
Data Council.

**Emma:** Please do. And put Dan on your list.
