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

1. Parses the SVG as XML
2. Finds `<text>` elements containing `~` — these identify animated relationships
3. Strips the `~` from the display text
4. Finds the associated arrow `<path>` elements (PlantUML renders arrows as paths near/between the text labels)
5. Adds the `marching-ant` CSS class to those paths
6. Injects the animation `<style>` block into the SVG `<defs>`

### CSS injected

```css
.marching-ant {
  stroke-dasharray: 8px;
  stroke-dashoffset: 16px;
  animation: marching 0.5s linear infinite;
}

@keyframes marching {
  to {
    stroke-dashoffset: 0;
  }
}
```

## Arrow Path Detection

PlantUML SVGs structure arrows as:
- A `<path>` for the line (stroke, no fill)
- A `<path>` or `<polygon>` for the arrowhead (filled)
- A `<text>` element for the label, positioned near the arrow

Strategy to match animated text to its arrow path:
1. Find all `<text>` elements containing `~`
2. For each, get its x/y position
3. Find the nearest `<path>` element that has `fill="none"` and a `stroke` attribute (arrow lines, not shapes)
4. Add `marching-ant` class to that path

This spatial matching is robust because PlantUML places labels close to their arrows.

## Script (`scripts/animate.py`)

Usage:
```bash
python scripts/animate.py rendered/c4/data-platform-container.svg          # In-place
python scripts/animate.py rendered/c4/data-platform-container.svg --output animated.svg
```

Behaviour:
1. Parse SVG with `xml.etree.ElementTree`
2. Find `<text>` elements containing `~` anywhere in their text content (including nested `<tspan>`)
3. Strip `~` from display text
4. Find nearest arrow `<path>` for each animated text
5. Add `marching-ant` class
6. Inject `<style>` into `<defs>` (create `<defs>` if missing)
7. Write output

If no `~` markers found, print "No animated arrows found" and exit cleanly (no error).

## Integration with render.py

Add `--animate` flag to `scripts/render.py`:

```bash
python scripts/render.py diagrams/c4/data-platform-container.puml --animate
```

This renders via Kroki then runs the animate post-processor on the output SVG. Convenience only — you can always run `animate.py` separately.

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

## Repo Changes

```
scripts/animate.py           # New: SVG post-processor
tests/test_animate.py        # New: tests
scripts/render.py             # Modified: add --animate flag
prompts/diagram-agent.md      # Modified: add animated arrows section
```

## Out of Scope

- Animation speed customization (fixed 0.5s)
- Per-arrow animation style variations
- JavaScript-based animation
- Animation in PNG output (SVG only)
