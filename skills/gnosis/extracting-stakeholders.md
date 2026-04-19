---
name: Extracting stakeholders from kick-off notes and org material
description: Reads kick-off meeting notes, org charts, engagement briefs, or introduction emails and extracts the stakeholder list with roles, interests, and decision rights. Produces entries for gnosis `00_scope/stakeholders.yaml`. Use at gnosis stage 0 (setup) or when a new stakeholder surfaces mid-engagement.
---

## When to use this skill

- Immediately after a kick-off meeting, when you have unstructured notes and need a clean stakeholder list.
- When an organisation's structure is introduced via a document or email.
- When a new person is brought into an in-flight engagement and you need to capture them.

This skill produces a working stakeholder roster. It is not a political map, though `interests` and `influence` fields hint at one — that's deliberate; consulting engagements live or die on stakeholder dynamics.

## Inputs

1. **Source material** — meeting notes, introduction emails, org charts, RACI tables, Confluence people pages.
2. **(Optional)** Existing `stakeholders.yaml` — avoid duplicates.

## Output format

YAML list matching `00_scope/stakeholders.yaml`:

```yaml
- name: Alice Chen
  role: Payments Lead
  team: Engineering · Payments
  email: alice.chen@meshco.example
  interests:
    - Transaction reliability
    - Reducing auth failures
  decision_rights:
    - Payments architecture
    - Vendor selection for card processing
  influence: high        # high | medium | low
  engagement_cadence: weekly  # optional
  notes: Strong preference for incrementalism; wary of big-bang migrations.

- name: Bob Murphy
  role: Operations Manager
  team: Operations
  interests:
    - Chargeback reduction
    - Ops tooling ergonomics
  decision_rights:
    - Ops tool choices
  influence: medium
```

Required: `name`, `role`. Optional but recommended: `team`, `interests`, `decision_rights`, `influence`, `notes`.

## Step-by-step

1. **List every person mentioned** in the source material. Include names that appear in passing — they might be load-bearing and you can cull later.
2. **For each person, capture what the source says.**
   - `role` — their job title or function, verbatim from the material.
   - `team` — organisational unit. Format `<Function> · <Team>` (e.g. "Engineering · Payments").
   - `interests` — what they care about, in their own words or inferred from concerns they raised.
   - `decision_rights` — what they have authority over. This is often implicit ("as Alice is the Payments Lead, she owns...") — capture the inference explicitly.
   - `influence` — how much sway they have in decisions. `high` for people with veto power or budget; `medium` for subject-matter experts; `low` for individual contributors.
3. **Mark ambiguity in `notes`.** If the material is unclear on a person's decision rights, say so: "Notes: unclear whether Alice or her manager signs off on vendor contracts — confirm in next session".
4. **Do not fabricate.** If no interest is stated, leave the field blank. A stakeholder roster with fake interests is worse than a sparse one.
5. **Check for missing roles.** If the engagement mentions "the compliance team" but no compliance stakeholder appears by name, add an entry with `name: TBD` and a `notes:` pointer: "Notes: compliance owner not yet named — ask for introduction".

## Quality checks

- [ ] Every stakeholder has `name` and `role`
- [ ] No fabricated `interests` or `decision_rights` — each must be traceable to the source
- [ ] `influence` ratings reflect the source's tone and evidence, not your assumption
- [ ] Team names use consistent separator format across entries
- [ ] Missing roles flagged with `name: TBD` rather than omitted
- [ ] Email addresses use the domain from the engagement context (if mentioned)
- [ ] No personal opinions in `notes` — only observed or reported behaviour

## Handoff to gnosis

Save your LLM output under `clients/<name>/transcripts/_drafts/` (date-stamped, e.g. `2026-05-07-stakeholders-extraction.yaml`) and hand it to gnosis for validation and merge:

```bash
gnosis ingest stakeholders \
  --from clients/meshco/transcripts/_drafts/2026-05-07-stakeholders-extraction.yaml \
  --client meshco \
  --session 2026-05-07-week3-stakeholders \
  --interviewer alfred
```

What gnosis enforces when you run this:

**Hard schema (refused if violated — nothing is written):**

- Each entry has non-empty `name` and `role`
- If `influence` is set, it is one of `high` / `medium` / `low` / `unknown`
- `interests`, `decision_rights` are lists of non-empty strings if provided
- `email`, if set, contains `@`

**Soft lint (reported to `ontology/ingest-warnings.md`, non-blocking):**

- `missing_decision_rights_on_high_influence` — `influence: high` without at least one `decision_rights` entry (common when a stakeholder is cited as influential but their sign-off surface hasn't been captured yet)
- `tbd_without_notes` — a `name: TBD` placeholder without `notes:` explaining why the role is unfilled and what introduction is needed

Fix warnings by editing `00_scope/stakeholders.yaml` directly, or by correcting the source fixture and re-ingesting.

**Merge behaviour:**

- Named stakeholders are keyed by normalised name (case-fold, paren-suffix stripped). Re-ingesting the same name updates that entry: scalar fields (`role`, `team`, `email`, `influence`, `engagement_cadence`, `notes`) are overwritten; list fields (`interests`, `decision_rights`) are unioned.
- `name: TBD` placeholders are keyed on the compound `(TBD, role, team)` tuple, so multiple TBDs for different roles coexist. When the real person surfaces later, ingest them as a named entry — the TBD stays until you delete it manually, and the `notes:` field on the new entry should reference the overlap.

Every merged entry carries a `last_ingested` block recording the session, interviewer, and timestamp — so later you can trace when each stakeholder was first captured and when their entry was last revised.

Follow-on effect worth knowing: the concepts extraction skill's `unknown_speaker` lint resolves against `00_scope/stakeholders.yaml`. So when a stakeholders ingest adds a previously-unknown speaker, re-running `gnosis ingest concepts` against the same concepts fixture will clear the corresponding warning — closing the loop between stage 0 and stage 2.

## Examples

### Input (kick-off notes excerpt)

```
Kick-off meeting, MeshCo engagement, 2026-04-10

Present:
- Alice Chen — Payments Lead. Has worked on payments for 8 years.
  She wants transaction reliability to improve; auth failure rates
  are her top KPI. She signs off on payment architecture decisions
  and vendor contracts up to £500k.
- Bob Murphy — Ops Manager. Cares about chargeback reduction and
  making ops tooling easier. Bob picks ops tools but doesn't set
  architecture.
- Dave (surname unknown) — joined halfway through, product role.
  Didn't speak much.

Also mentioned:
- "The compliance team" will need to be consulted on data residency.
  We don't yet have a named compliance stakeholder.
```

### Output

```yaml
- name: Alice Chen
  role: Payments Lead
  team: Engineering · Payments
  interests:
    - Transaction reliability
    - Reducing auth failure rates
  decision_rights:
    - Payments architecture sign-off
    - Vendor contracts up to £500k
  influence: high
  notes: 8 years of payments experience; stated auth failure rates as her top KPI.

- name: Bob Murphy
  role: Operations Manager
  team: Operations
  interests:
    - Chargeback reduction
    - Ops tooling ergonomics
  decision_rights:
    - Ops tool selection
  influence: medium
  notes: Explicitly does not set architecture.

- name: Dave
  role: Product (surname unknown)
  team: Product
  influence: low
  notes: Joined kick-off halfway; minimal participation. Confirm full name and scope.

- name: TBD
  role: Compliance owner
  team: Compliance
  interests:
    - Data residency
  influence: unknown
  notes: Named compliance stakeholder not yet introduced. Ask Alice or Bob for an introduction — compliance sign-off is required for data residency decisions.
```

## Anti-patterns

- **Guessing at interests.** If Alice didn't say she cares about X, don't write "interested in X" just because a Payments Lead typically would.
- **Omitting unclear stakeholders.** "Dave" with a missing surname is still worth capturing — if he becomes important, you have a placeholder. If he doesn't, delete him later.
- **Elevating yourself or your team.** This is the *client's* stakeholder list. Your delivery team isn't a stakeholder for scope/decisions (though you may track them separately).
- **Overestimating influence.** A stakeholder who speaks a lot isn't necessarily influential. A stakeholder who has budget authority or veto power is. Use evidence.
- **Writing novel-length `notes`.** Keep notes factual and short. Opinions and political gossip don't belong in an ontology artefact.
- **Merging people.** "Marketing and Design" is not a stakeholder — it's two teams. Split into separate entries even if you only have a placeholder name.
