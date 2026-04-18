---
name: Authoring companion prose for the living architecture handbook
description: Guides how to write the optional markdown that appears alongside each diagram in skhema's living-docs handbook — audience framing, voice, what to include vs what to leave out. Use when a client's handbook feels like a pile of diagrams without narrative, or when a new diagram is added and needs companion prose.
---

## When to use this skill

- A client asked "can you send me a document I can share with <audience>?" and you realised `<client>-architecture.html` has no prose.
- You added a new diagram to `clients/<name>/diagrams/` and need companion markdown.
- You're reviewing a handbook and the writing reads inconsistent across sections.

## Where the prose lives

skhema's `skhema docs` picks up markdown from two patterns:

- **Top-level overview** — `clients/<name>/docs/overview.md`. Rendered once between the TOC and the first section.
- **Per-section overview** — `clients/<name>/docs/<type>/_overview.md` (e.g. `docs/c4/_overview.md`). Rendered at the top of that section.
- **Per-diagram prose** — `clients/<name>/docs/<type>/<stem>.md` matching the diagram filename (e.g. for `diagrams/c4/context.puml`, create `docs/c4/context.md`). Rendered below the diagram SVG.

If a file doesn't exist, skhema silently skips it. Prose is optional, not required.

## The reader's journey

The handbook is read in three modes. Good companion prose serves all three:

1. **Scan** — someone flicks through in 3 minutes to "get the gist". They read headings and the first sentence of each paragraph.
2. **Reference** — someone lands on one section to answer a specific question. They read one diagram + its companion prose and bail.
3. **Brief** — a new team member reads the whole thing start-to-finish.

Write so scanning works; reference and brief follow naturally.

## Step-by-step

1. **Start with `overview.md`.** 150–300 words. Answer three questions:
   - What is this architecture for? (business goal, not technology)
   - What are its major parts?
   - What's *not* in this document? (out-of-scope disclaimer)
2. **For each diagram type, write a `_overview.md`.** Short — 80–120 words. Explain:
   - What level of detail this section shows
   - Who should care about it
   - How to read the diagrams (if convention isn't obvious)
3. **For each diagram, decide if it needs prose.**
   - **Yes, write prose if:** the diagram has non-obvious labels, intentional omissions, or represents a contested decision.
   - **No, skip if:** the diagram is self-explanatory or the reader will only glance at it.
4. **Write the diagram prose.** One tight section per diagram. Structure:
   - **What it shows** (one sentence, topology in plain English)
   - **What to notice** (2–4 bullet points — the interesting choices)
   - **What's deliberately not shown** (one sentence if relevant)
5. **Link to ADRs.** If the diagram reflects a recorded decision, end the prose with "See also: ADR<NN>". This anchors the narrative to the decision record.
6. **Revise for voice.** Companion prose is *your voice as the consultant*. Confident, direct, second-person when addressing the reader. Avoid: "It should be noted that…", "In this diagram…", "The above illustrates…".

## Voice reference

**Good voice** (confident, reader-addressed):
> This view shows MeshCo's platform from the outside. The platform itself is one system; everything around it — POS, ERP, the BI audience — is external to our scope. Notice that the ERP appears as a read-only source; updates flow into, not out of, the platform.

**Bad voice** (passive, hedged):
> The diagram above can be seen to illustrate the platform from an external perspective. It should be noted that various systems surround it, and the ERP system is likely intended to be a source.

## Quality checks

- [ ] `overview.md` exists and is under 300 words
- [ ] Each `_overview.md` is under 120 words
- [ ] Per-diagram prose is under 200 words (tighten if longer)
- [ ] No passive voice in narrative sections
- [ ] No "the above"/"as shown in the diagram" — the diagram is right there
- [ ] Links to ADRs where decisions are visible
- [ ] Out-of-scope disclaimer in `overview.md`
- [ ] Specific numbers where they exist (count of concepts, throughput, timelines)

## Examples

### `overview.md` (MeshCo)

```markdown
# MeshCo Data Platform

MeshCo is moving from a single-team, single-warehouse data estate to a federated
mesh model where domain teams publish data products against shared platform
infrastructure. This handbook captures the target-state architecture, the
trade-offs that shaped it, and the decisions recorded along the way.

**What's in this handbook:** the platform system context (L1), its containers
(L2), the transformation and semantic-layer flow (sequence diagrams), and the
architecture decisions that explain the choices.

**What's out of scope:** the operational migration plan, per-domain model
schemas, and the rollout timeline. Those live in `engagement-plan.md` and
the domain-specific engagement briefs.

At time of writing there are four published data products, six more in draft,
and the first production consumer is the finance team's monthly close flow.
```

### `docs/c4/context.md` (L1 companion)

```markdown
# Context view

What it shows: MeshCo's data platform sitting between source systems (POS, ERP,
e-commerce) and consumers (analysts, ML engineers, the BI layer, operational
APIs).

What to notice:
- The platform boundary is deliberately narrow. Analytics apps that live
  *inside* business teams (e.g. the finance close) are consumers, not part of
  the platform.
- The ERP appears twice — once as a source (daily extract) and once as a sink
  (reverse-ETL of finalised customer lifetime value). This asymmetry is
  intentional and backed by ADR03.
- No GenAI surfaces appear at L1 — those are internal to the ML Platform
  container and show up at L3 only.

See also: ADR01 (Iceberg for the lakehouse), ADR03 (Reverse-ETL to ERP).
```

## Anti-patterns

- **Restating the diagram in prose.** If your paragraph is "the diagram shows X connected to Y connected to Z", delete it. The diagram already did that.
- **Consulting-speak.** "Leveraging best-in-class", "industry-standard", "next-generation" — read as marketing, not architecture.
- **Long anecdotes.** Save them for the spoken presentation; the handbook is read asynchronously.
- **Dangling ADR references.** If you write "see ADR05" and ADR05 doesn't exist, you've just created a dangling pointer. Write ADRs first, link second.
- **Copy-pasted prose across clients.** A one-line tell of a sloppy engagement. Each client deserves client-specific voice.
- **No out-of-scope section.** Readers will infer a scope that's wider than you intended. State what's out explicitly.
- **Third-person passive.** "The platform is shown to be consumed by…" is a sentence that sounds important and says nothing. Rewrite as active/direct.
