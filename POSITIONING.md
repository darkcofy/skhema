# Positioning

*Why skhema + gnosis + skills exists, and what it is vs what it isn't.*

## The problem

Architecture consulting engagements suffer three recurring failures:

1. **Deliverables don't travel.** A polished diagram + a PDF deck + a Confluence page = three artifacts in three formats that drift out of sync the moment someone changes anything.
2. **Discovery is ad-hoc.** Every engagement re-invents the process of going from "we met some stakeholders" to "we have a domain model". New consultants start from zero each time.
3. **Methodology walks out the door.** When a senior architect leaves a practice, their playbooks — the *how* of doing good discovery and modelling — leave with them.

Existing tools solve parts of this:

- **Structurizr** nails C4 modelling as code. Its HTML exports are functional but not partner-ready.
- **arc42** provides a documentation template but no tooling.
- **Backstage** is an internal developer portal, not a client deliverable format.
- **Confluence / Notion / GitBook** are content hubs, not structured discovery tools.

Nothing in the market:

- Guides structured domain discovery with readiness gates.
- Produces client-ready self-contained HTML/PDF artifacts out of the box.
- Packages the *methodology* (not just the tool) in a form both humans and LLMs can execute.

## The three parts

### gnosis — the headliner

A guided domain-discovery workflow. Six staged worksheets — scope, language, concepts, mappings, behaviour, formalisation — each with completion criteria and readiness rules. Deterministic Python tooling scaffolds the workspace and tracks readiness; the *judgement-heavy* extraction work (interview transcripts → candidate concepts) is delegated to skills.

Why this is novel: nothing in the consulting space does staged, readiness-aware domain discovery as a reusable tool. Big-4 firms have internal methodologies for this, but they live in Word docs and partners' heads.

### skhema — the supporting product

A deliverable packager. Consumes PlantUML (exported from Structurizr DSL, or hand-written for sequence / ERD / deployment diagrams) and produces three self-contained HTML outputs:

- **Gallery** — searchable, filterable grid of every diagram with version history and ADR cross-references
- **Living handbook** — cover + TOC + per-section narrative + diagrams + ADRs, print-friendly
- **Reveal.js deck** — responsive presentation for client hand-off, keyboard-nav, speaker notes, PDF-exportable from any browser

Why this layer exists: Structurizr's built-in HTML is functional; client-ready requires Jinja2 templates, typography choices, and opinionated styling. That's this layer's job.

### skills — the force multiplier

A dual-use library of SKILL.md files covering:

- gnosis extraction (transcripts → worksheet entries × 5 skills)
- skhema authoring (Structurizr DSL, C4 best practices, Reveal decks, ADRs, living docs × 5 skills)

**Dual-use** means each file is two things at once:

- A *human-readable best-practices playbook* — read it, apply the methodology by hand, no tooling required.
- An *LLM-executable instruction file* — point any capable LLM at it plus your raw material, get structured output matching gnosis/skhema schemas.

Format follows the [Anthropic SKILL.md spec](https://github.com/obra/superpowers/blob/main/skills/writing-skills/anthropic-best-practices.md): YAML frontmatter + markdown body, under 500 lines per file, gerund-form names, concrete I/O examples.

Why this design:

- **Zero LLM maintenance** — no SDK wrappers, no API versions to chase, no credentials stored here.
- **Platform-agnostic** — works with Claude Code natively; trivially adaptable to Cursor, Windsurf, Cline, ChatGPT, Gemini.
- **Privacy-correct** — this repo never touches client data or credentials; the LLM call happens in the user's tool of choice.
- **Honest positioning** — the skill *is* the methodology, not a wrapper around one.

## Why Structurizr (and not [X])

| Choice | Why we went this way |
|---|---|
| **Structurizr** over Likec4 / Mermaid / raw PlantUML | Mature C4 semantics, single model → multiple views, cross-engine export. skhema delegates modelling entirely to it and focuses on the packaging layer that Structurizr doesn't prioritise. |
| **Reveal.js** over PDF decks | Responsive, self-contained HTML travels via email the same way a PDF does, and looks dramatically better on modern screens + projectors. PDF is one browser print away. |
| **Jinja2 templates** over inline HTML strings | Designers can tweak templates without touching Python. Outputs stay self-contained. |
| **SKILL.md** over Python LLM adapters | Platform-agnostic, zero maintenance, privacy-correct. |
| **dbt / Iceberg / Unity Catalog** in the reference manifest | 2026 data-architecture reality; partners notice when the vocabulary is current. |

## Who this is for

Primary: **Big-4 and independent data / platform / enterprise architecture consultants** who need to hand over polished artifacts and scale their methodology.

Secondary: **solutions architects** running discovery sessions and producing client deliverables.

Tertiary: **internal architecture teams** that want gnosis's staged discovery model plus repeatable deliverable packaging.

## Who this is not for

- Anyone looking for a drag-and-drop diagram editor (use Lucid, Miro, diagrams.net)
- Teams that want a collaborative whiteboard (use FigJam, Miro)
- Organisations that need a hosted SaaS documentation platform (use Confluence, Notion, GitBook)
- Developers wanting an AI product (there's no LLM code in this repo — skills work with the LLM you bring)

## Non-goals

- **No Structurizr Cloud integration.** Lite container only. Cloud is a separate concern.
- **No real LLM calls in the codebase.** Skills are markdown; users run them against their own LLM.
- **No custom C4 DSL.** Structurizr owns this.
- **No arc42 template emission.** Separate product.
- **No Backstage integration.** Different audience.

## Strategic bets

1. **Structurizr will remain the dominant C4-as-code tool** for the foreseeable future. Betting on it is low-risk.
2. **Consultants will increasingly use LLMs for extraction work**, but which LLM varies wildly by firm (EY uses Bedrock; other firms use Azure OpenAI, Anthropic direct, or local). A platform-agnostic skills library insulates us from that choice.
3. **Client-ready HTML deliverables will beat PDF decks** as the default hand-off format over the next 2–3 years. Starting there positions us ahead of the curve.
4. **Methodology packaging is the moat**, not the tooling. Structurizr + Jinja2 + PlantUML is commodity; the *skills library* that captures how to do good discovery and authoring is the defensible asset.
