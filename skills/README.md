# skhema skills library

Dual-use methodology playbooks for consultant architects.

Each skill in this directory is **two things at once**:

- **A human-readable best-practices playbook** — read it and apply the methodology by hand, no tooling required.
- **An LLM-executable instruction file** — point any capable LLM at the skill plus your raw material, and the LLM will produce structured output matching the skhema/gnosis schemas.

This is consulting-as-code. The skills *are* the methodology Big-4 partners pay for, in a form that's portable across people, teams, and AI tools.

## Library

### `gnosis/` — Domain discovery (unstructured input → structured worksheets)

| Skill | Produces |
|---|---|
| [extracting-concepts-from-transcripts.md](gnosis/extracting-concepts-from-transcripts.md) | `02_concepts/candidate-concepts.yaml` entries |
| [extracting-glossary-terms.md](gnosis/extracting-glossary-terms.md) | `01_language/glossary-seeds.csv` rows |
| [detecting-terminology-synonyms.md](gnosis/detecting-terminology-synonyms.md) | `01_language/synonym-conflicts.md` entries |
| [extracting-stakeholders.md](gnosis/extracting-stakeholders.md) | `00_scope/stakeholders.yaml` entries |
| [extracting-events-and-lifecycles.md](gnosis/extracting-events-and-lifecycles.md) | `04_behavior/lifecycle-states.yaml` + `events.yaml` |

### `skhema/` — Authoring (best-practice guidance for client-facing outputs)

| Skill | Topic |
|---|---|
| [authoring-structurizr-dsl.md](skhema/authoring-structurizr-dsl.md) | Structuring `workspace.dsl`: people/systems/containers/components, views, styles, `!include` patterns |
| [modelling-with-c4-best-practices.md](skhema/modelling-with-c4-best-practices.md) | When to use L1 vs L2 vs L3; common C4 anti-patterns; data-platform modelling |
| [authoring-reveal-decks.md](skhema/authoring-reveal-decks.md) | Slide structure for client hand-off decks, speaker notes, typography |
| [authoring-adrs.md](skhema/authoring-adrs.md) | Nygard-style ADR structure, linking to C4 elements and gnosis concepts |
| [authoring-living-docs-prose.md](skhema/authoring-living-docs-prose.md) | Companion-markdown voice for diagrams, audience framing |

## Using with an LLM

### Claude Code (native)

```bash
ln -s /path/to/this/repo/skills ~/.claude/skills/skhema
```

Then invoke via natural language: *"Use the extracting-concepts-from-transcripts skill on these transcripts: clients/meshco/transcripts/"*

### ChatGPT / Custom GPT / Gemini Gem

Open the skill's markdown file, copy its body (everything after the frontmatter), and paste into the platform's "Instructions" or "System Prompt" field. Attach your transcripts/source material as files.

### Cursor / Windsurf / Cline

Convert to the platform's rule format:

- **Cursor:** `.cursor/rules/<skill-name>.mdc` — same body, frontmatter fields: `description`, `alwaysApply`, `globs`
- **Windsurf:** `.windsurf/rules/<skill-name>.md` — same body, frontmatter fields
- **Cline:** `.clinerules/<skill-name>.md` — same body

### Local / self-hosted (Ollama, vLLM)

Most local runtimes accept a system-prompt file: pass the skill body via `-f system.md` or equivalent.

## Using as a human playbook

Ignore the frontmatter. Read the skill body as a methodology guide — the `Step-by-step`, `Quality checks`, `Examples`, and `Anti-patterns` sections are written for humans first. Apply the methodology against your source material manually; paste the result into the appropriate gnosis/skhema artifact.

## Conventions

All skills follow the [Anthropic SKILL.md format](https://github.com/obra/superpowers/blob/main/skills/writing-skills/anthropic-best-practices.md):

- `name` — gerund-form ("Extracting…", "Authoring…")
- `description` — third-person, includes trigger context
- Body under 500 lines, concrete I/O examples, forward-slash paths

## Adding a new skill

1. Pick a clear gerund-form name.
2. Write under 500 lines with frontmatter + When-to-use / Inputs / Output format / Step-by-step / Quality checks / Examples / Anti-patterns sections.
3. Include at least one realistic worked example (input → output pair).
4. Test it against a real LLM before committing.
5. Add a row to the library table above.
