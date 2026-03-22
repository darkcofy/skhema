# SVG Arrow Animation: Design Spec

## Overview

A post-processing script that adds marching-ant animation to selected arrows in rendered SVG diagrams. Selective — only arrows whose PlantUML relationship label contains a `~` marker get animated. The marker is stripped from the displayed text.

## Decisions

- **Trigger:** `~` prefix in relationship label (e.g., `Rel(a, b, "~Streams to", "Avro")`)
- **Animation:** CSS marching-ants via `stroke-dasharray` + `stroke-dashoffset` keyframe
- **Output:** Overwrites the SVG in-place (or `--output` for a separate file)
- **Dependencies:** Python stdlib only (XML parsing via `xml.etree.ElementTree`)

## How It Works

### In PlantUML source

```plantuml
Rel(event_stream, data_lake, "~Streams to", "Avro/JSON")   ' animated
Rel(data_analyst, data_warehouse, "Queries", "SQL")          ' static
Rel(batch_etl, data_lake, "~Loads to", "Parquet")           ' animated
```

The `~` prefix marks a relationship for animation. It appears in the PlantUML source but is stripped from the rendered SVG text by the animate script.

### In the rendered SVG

Kroki renders the `~` as part of the label text. The animate script:

1. Strips the `<?plantuml ...?>` processing instruction (invalid XML)
2. Registers the SVG namespace to avoid `ns0:` prefix mangling
3. Iterates over `<g id="lnk...">` link groups
4. Checks if any `<text>` child in the group contains `~`
5. Strips `~` from the first `<text>` element that has it
6. Adds `marching-ant` CSS class to the sibling `<path>` (arrow line) in the same group
7. Injects the animation `<style>` block as first child of `<svg>` root

### CSS injected

```css
.marching-ant {
  stroke-dasharray: 6 4;
  stroke-dashoffset: 10;
  animation: marching 0.5s linear infinite;
}

@keyframes marching {
  to {
    stroke-dashoffset: 0;
  }
}
```

Dash pattern `6 4` (6px dash, 4px gap) tuned for PlantUML's `stroke-width:1` arrows.

## Arrow Path Detection — Group-Based

Kroki/PlantUML renders each relationship as a `<g id="lnk{N}">` group containing:
- One `<path>` for the arrow line (`fill="none"`, has `stroke`)
- One `<polygon>` for the arrowhead (filled)
- One or more `<text>` elements for the label (split per word)

**Algorithm:**
1. Find all `<g>` elements whose `id` starts with `lnk`
2. For each group, check if any child `<text>` element's text content contains `~`
3. If found: strip `~` from that text element, add `marching-ant` class to the sibling `<path>` with `fill="none"`

No spatial matching needed — the DOM grouping is deterministic.

**Note on text splitting:** PlantUML/Kroki splits label text into one `<text>` element per word. The `~` will only appear in the first `<text>` element of the label (e.g., `~Streams` as the first word). Strip `~` from that element only.

## XML Parsing Caveats

1. **Processing instruction:** Kroki SVGs start with `<?plantuml 1.2026.1?>` — must be stripped before `ET.parse()` or it raises `ParseError`
2. **Namespace:** All SVG elements are in `http://www.w3.org/2000/svg`. Must use full namespace in `find()`/`iter()` calls. Register namespace with `ET.register_namespace('', 'http://www.w3.org/2000/svg')` before writing to avoid `ns0:` prefix mangling
3. **Style injection location:** Inject `<style>` as first child of root `<svg>` element (not inside `<defs>`) for broadest browser/renderer support

## Script (`scripts/animate.py`)

Usage:
```bash
python scripts/animate.py rendered/c4/data-platform-container.svg          # In-place
python scripts/animate.py rendered/c4/data-platform-container.svg --output animated.svg
```

Behaviour:
1. Read SVG file as string
2. Strip `<?plantuml ...?>` processing instruction via regex
3. Parse with `xml.etree.ElementTree`
4. Register SVG namespace
5. Iterate `<g id="lnk...">` groups, find `~` in text children
6. Strip `~` from display text, add `marching-ant` class to arrow `<path>`
7. Inject `<style>` element as first child of `<svg>` root
8. Write output (in-place or to `--output` path)

If no `~` markers found, print "No animated arrows found" and exit cleanly (no error).

## Integration with render.py

Add `--animate` flag to `scripts/render.py`:

```bash
python scripts/render.py diagrams/c4/data-platform-container.puml --animate
```

This renders via Kroki then runs the animate post-processor on the output SVG.

**Guard:** `--animate` is ignored with a warning when `--png` is also specified (animation is SVG-only).

## Agent Prompt Update

Add to `prompts/diagram-agent.md`:

```markdown
### Animated Arrows

To animate a relationship arrow (marching-ant flow effect), prefix the label with `~`:

\`\`\`plantuml
Rel(event_stream, data_lake, "~Streams to", "Avro/JSON")   ' animated
Rel(data_analyst, data_warehouse, "Queries", "SQL")          ' static
\`\`\`

Use animation sparingly — only on key data flows to draw attention. Too many animated arrows causes visual fatigue. Good candidates:
- Real-time streaming flows
- Active data pipelines
- Critical integration paths

After rendering, run: `python scripts/animate.py rendered/path/to/diagram.svg`
Or use: `python scripts/render.py diagram.puml --animate`
```

## Test Fixtures

Tests use a committed fixture SVG (`tests/fixtures/sample-link-groups.svg`) containing realistic `<g id="lnk...">` groups with paths, polygons, and text elements. This avoids depending on a live Kroki API call.

## Repo Changes

```
scripts/animate.py                    # New: SVG post-processor
tests/test_animate.py                 # New: tests
tests/fixtures/sample-link-groups.svg # New: test fixture
scripts/render.py                     # Modified: add --animate flag
prompts/diagram-agent.md              # Modified: add animated arrows section
```

## Out of Scope

- Animation speed customization (fixed 0.5s)
- Per-arrow animation style variations
- JavaScript-based animation
- Animation in PNG output (SVG only)
- Arrowhead animation (only the line path animates)
