---
name: Authoring Reveal.js client hand-off decks
description: Guides the structuring of a skhema Reveal.js deck — cover, section dividers, diagram slides, ADR slides, speaker notes, and typography. Use when a client deck feels cluttered or you're producing a new deck template. Assumes skhema deck pipeline (PlantUML → SVG → Jinja2 → deck.html).
---

## When to use this skill

- You've run `skhema deck --client <name>` and the output looks dense, cluttered, or generic.
- You're about to present a deck to a client and want to sanity-check it.
- You're creating a new client and want to know what companion material is worth writing.

## The deck shape skhema produces

Each `skhema deck` run emits a single `deck.html` with this structure:

1. Cover slide (accent-colour background, client name + subtitle + date)
2. Per type:
   - Section divider (C4 Diagrams, Sequence Diagrams, ERDs, Deployment)
   - One slide per diagram in that type
3. Architecture Decisions section (if any ADRs exist)
4. Closing "Thank You" slide

You can't change this structure without editing `src/skhema/templates/deck/deck.html.j2`. You *can* influence what lands on each slide by curating your source material.

## What you can curate

### Diagram ordering

Name your files alphabetically within a type to control order: `01-system-context.puml`, `02-containers.puml`. skhema sorts by filename within type.

### Diagram titles

The slide title is derived from the filename via `kebab-case → Title Case`. `nova-pay-container-view.puml` → `Nova Pay Container View`. Pick filenames that will read well as titles.

### Speaker notes

Drop companion markdown at `clients/<name>/docs/<type>/<stem>.md`. Example: for `diagrams/c4/context.puml` you'd create `docs/c4/context.md`.

The deck template renders this as Reveal.js `<aside class="notes">` — visible only in presenter view (press `S` in the deck). Great for:

- What to say while on this slide
- Anticipated questions
- References to ADRs or external docs

### ADR cross-linking

ADRs in `clients/<name>/adrs/` with comment-tag pointers surface automatically on relevant slides. Pattern inside each ADR:

```markdown
<!-- skhema:elements payment_events, kafka_cluster -->
<!-- gnosis:concepts Transaction, Settlement -->
```

The deck renders them as a dedicated ADR section near the end.

### Theme and accent colour

`clients/<name>/client.yaml`:

```yaml
name: "MeshCo Retail"
subtitle: "Data Platform Architecture"
accent_color: "#D97706"  # the EY/skhema orange; change per client brand
```

## Step-by-step to a presentable deck

1. **Cut diagrams ruthlessly.** A 25-slide deck of diagrams is unpresentable. Remove:
   - Duplicate views (L1 context and L2 containers for the same system — one is enough for exec audiences)
   - Deep-dive L3 components unless they're the centrepiece
   - Any diagram you can't talk to for 90 seconds
2. **Rename files for title quality.** `cluster.puml` reads badly; `kafka-event-bus.puml` reads as `Kafka Event Bus`.
3. **Write speaker notes for top-of-mind slides.** You don't need notes for every slide. Pick the 5–10 diagrams where you'll have scripted talking points. Example for `context.md`:

   ```markdown
   # Context view — speaker notes

   **Opening line:** "This is the 30,000-foot view of the data platform."

   **Flow:**
   - Point at the platform box → "Our system."
   - Sweep left-to-right across external systems → "These are the sources."
   - Highlight data-analyst persona → "And these are who we're serving."

   **Expected question:** "Why isn't Snowflake on this diagram?"
   **Answer:** "It's inside the platform — we'll see it at the next level. L1 shows the world the system lives in."
   ```
4. **Write ADRs for contentious decisions.** Every decision someone might push back on gets an ADR. The deck surfaces them so you can pre-emptively address objections. ADR structure is covered by the authoring-adrs skill.
5. **Set the accent colour to match the client's brand.** Grab the hex from their marketing site. Do *not* use your firm's colour on a client deck — it looks like you didn't put effort in.
6. **Check the deck on the same screen size as the presentation room.** Open in a browser, press `F` for fullscreen, walk through every slide.
7. **Verify the PDF fallback.** Append `?print-pdf` to the URL, print to PDF, verify pages are clean. Some clients will archive the PDF after the session.

## Quality checks

- [ ] Cover slide has the correct client name, subtitle, and date
- [ ] Under 15 diagram slides total unless the engagement explicitly warrants depth
- [ ] Every diagram title reads as a human phrase (check the filename → title mapping)
- [ ] Accent colour matches the client brand
- [ ] Speaker notes exist for at least the opening context slide and the closing decisions slide
- [ ] All SVGs render crisply at full-screen (no squashed text, no cut-off elements)
- [ ] PDF export (`?print-pdf` + browser print) produces a clean file
- [ ] No broken slides (empty diagram blocks, missing titles, etc.)

## Examples

### Structuring a 45-minute workshop deck for MeshCo

- **Cover** — "MeshCo Retail — Data Platform Architecture, April 2026"
- **Section: C4 Diagrams**
  - L1 Context — who uses it, what it talks to
  - L2 Containers — the data-platform building blocks
- **Section: Sequence Diagrams**
  - Order ingestion flow (end-to-end from POS → semantic layer → BI)
- **Section: ERDs** *(skip — not relevant for this engagement)*
- **Section: Architecture Decisions**
  - ADR01: Iceberg for the lakehouse
  - ADR02: Data-contract-first for cross-domain consumption
  - ADR03: Cube for the semantic layer
- **Closing** — Thank You

Speaker notes on L1, L2, and the order flow. No notes on ADRs (the ADR body renders inline).

## Anti-patterns

- **One slide per tiny diagram.** If a diagram takes 5 seconds to explain, merge two diagrams onto one slide in the source material, or drop it.
- **Company logos on cover.** skhema's template doesn't render logos. If a partner asks for logos, do it in the client's branding separately; don't stuff images into skhema.
- **Reading the slide.** If the notes are just a transcript of the slide content, delete them.
- **Inconsistent accent colours.** Half the deck with EY orange, half with the client's blue. Pick one per deck.
- **Presenting without rehearsal.** `F` for fullscreen, walk through every slide, know the transitions. 5 minutes of rehearsal is visible to every client.
- **Leaving ADRs vague.** If an ADR renders with "TBD" or "Draft" in the status pill, that's visible to the client. Either fill it in or remove the ADR.
- **Skipping speaker notes for the closing.** The last slide is where you leave the room — a prompt for the final ask (next step, deliverable, sign-off) is worth writing.
