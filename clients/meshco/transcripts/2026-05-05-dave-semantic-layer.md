---
session_id: 2026-05-05-dave-semantic-layer
date: 2026-05-05
participants:
  - Dave Kim (Analytics Engineering Lead)
  - Alfred (interviewer, EY)
duration_min: 40
format: granola-transcript
location: MeshCo HQ, remote video
---

# Semantic layer deep-dive — metrics, measures, cohorts, and where Cube fits

## 00:00 — The argument we keep having

**Alfred:** Dave, thanks. Before we go deep, set the scene for me — why is
the semantic layer such a sore point internally?

**Dave:** Short version: marketing calls it "revenue", finance calls it
"net revenue", the ML team calls it "target", and BI reports three slightly
different numbers depending on which dashboard you open. We've known this
for a year. The fix is a semantic layer — one place where "revenue" has
one definition, and every consumer pulls from there.

**Alfred:** And you've picked Cube for that?

**Dave:** I've *advocated for* Cube. We're not deployed. Looker was the
default choice because we pay for it, but Looker's semantics only serve
Looker. Cube is headless — it serves BI, reverse-ETL, ML features, APIs,
anything. That matters because the ML team is not going to pull from
Looker, full stop.

## 06:30 — Metric vs measure

**Alfred:** Walk me through how you distinguish a metric from a measure.
I've heard both used in this building and I can't tell if people mean the
same thing.

**Dave:** OK this is the thing that's going to come up in your glossary
work. A **measure** is a column-level aggregate — sum of order_value,
count of distinct customers, that kind of thing. A **metric** is a
measure plus context: grain, filters, business meaning. "Weekly active
customers" is a metric. "Count distinct of customer_id" is a measure.

**Alfred:** And today?

**Dave:** Today nobody draws the line. "Metric" and "measure" are used
interchangeably, including by me on bad days. But for the semantic layer
to work we have to distinguish them. A metric has an owner, a definition,
a grain, a set of approved filters. A measure is just SQL.

**Alfred:** So in the ontology you want them as separate concepts?

**Dave:** Yes. Measure as the SQL-level primitive, Metric as the
business-level deliverable. Measures compose into metrics. Metrics are
what consumers reference.

## 14:00 — Cohorts

**Alfred:** Emma mentioned cohorts yesterday — customer acquisition
cohorts tracked over time. How does that live in the semantic layer?

**Dave:** Cohort is a metric definition with a twist. You define the
cohort once — say, "customers whose first order was in period 4" — and
then you report any metric (revenue, orders, retention) across that
cohort. The cohort is a reusable slice. Cube has first-class support for
this; it's one of the reasons I want it.

**Alfred:** And today cohorts are defined where?

**Dave:** In three places. Marketing has their own definition in Braze.
Finance has one in Power BI. The ML team has one in a notebook. All three
disagree at the edges — Braze includes trial customers, Power BI doesn't,
the ML team depends on who wrote the notebook that week. Classic.

**Alfred:** Cohort is the concept. Cohort definition is the artifact that
pins it down?

**Dave:** Yes. Cohort is the idea. CohortDefinition is the versioned,
owned, contract-backed artifact. If the definition changes, anything
built on it needs to be notified.

## 22:15 — The metric surface

**Alfred:** Something you said earlier — Cube "serves BI, reverse-ETL, ML,
APIs". What do you call the layer where consumers actually touch metrics?

**Dave:** I've been calling it the **metric surface**. It's the outward
face of the semantic layer. BI dashboards hit a surface, reverse-ETL hits
a surface, ML feature pipelines hit a surface. They all go through the
same definitions but through different protocols — SQL for BI, REST for
reverse-ETL, a Python client for ML.

**Alfred:** And each of those surfaces is, what — a data product?

**Dave:** That's where I'm not sure. The underlying metric *definition* is
what I think of as the data product. The surface is more like a consumer
binding. But I could be wrong — some people would say each surface is its
own data product with its own contract.

**Alfred:** We'll park that and come back. What about the new ML lead —
Priya, I think? — where does she sit on this?

**Dave:** Priya's starting in two weeks. She's got strong opinions about
feature stores and she's going to want the metric definitions exposed as
features. I'd expect her to push for Cube over anything Looker-based, but
let's let her speak for herself.

## 29:30 — Contracts on metric definitions

**Alfred:** Coming back to contracts. Today a metric definition can change
and you find out later. What would a contract on a metric definition look
like?

**Dave:** It'd say: here's the metric, here's the grain, here are the
approved filters, here's the SLA on how often it refreshes, here's the
breaking-change policy. If the definition changes materially — say, we
flip from gross to net revenue — that's a breaking change and every
downstream consumer sees a CI red light before it ships.

**Alfred:** Same mechanics as the data product contracts Bob described?

**Dave:** Same mechanics. The metric definition IS a data product, in my
view — it has an owner, a schema (grain + dimensions), an SLO, a contract.
I think we should stop treating metric definitions as a special case.
They're data products with semantic payload.

## 35:00 — What success looks like

**Alfred:** At week eight, what do you need?

**Dave:** Two things from your side. One: an ontology that names metric
vs measure distinctly, so when I push the semantic layer forward I'm not
re-litigating the vocabulary. Two: Cohort, CohortDefinition, and
MetricDefinition modelled as first-class concepts tied into the data
product / data contract model so the contract work applies to them
uniformly.

**Alfred:** And your own side?

**Dave:** A Cube POC shipping by week six, one lighthouse metric
(probably weekly active customers) defined and consumed through it by
BI and one ML feature pipeline.

**Alfred:** Got it. I'll draft the concept entries and include the
metric-vs-measure split. Expect a review ping on Friday.

**Dave:** Appreciate it.
