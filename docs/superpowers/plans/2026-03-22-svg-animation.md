# SVG Arrow Animation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers-extended-cc:subagent-driven-development (if subagents available) or superpowers-extended-cc:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add marching-ant CSS animation to selected arrows in Kroki-rendered SVGs, triggered by a `~` prefix in PlantUML relationship labels.

**Architecture:** A post-processing script parses SVGs as XML, finds `<g id="lnk...">` groups containing `~` in their text, strips the marker, and injects CSS animation on the arrow path. Integrates with existing render.py via `--animate` flag.

**Tech Stack:** Python 3 (stdlib: `xml.etree.ElementTree`, `re`), CSS keyframe animation

---

### Task 0: Test Fixture

**Files:**
- Create: `tests/fixtures/sample-link-groups.svg`

- [ ] **Step 1: Create a minimal test fixture SVG**

This fixture mimics Kroki's PlantUML SVG structure with `<g id="lnk...">` groups. Two links: one with `~` marker (animated), one without (static).

Create `tests/fixtures/sample-link-groups.svg`:

```xml
<?plantuml 1.2026.1?><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300">
<defs/>
<g>
<g id="lnk1" data-source-line="10">
<path d="M 100 150 L 300 150" fill="none" style="stroke:#666666;stroke-width:1;"/>
<polygon fill="#666666" points="300,150 294,146 296,150 294,154" style="stroke:#666666;stroke-width:1;"/>
<text fill="#666666" font-family="sans-serif" font-size="13" lengthAdjust="spacing" x="170" y="143">~Streams</text>
<text fill="#666666" font-family="sans-serif" font-size="13" lengthAdjust="spacing" x="210" y="143">to</text>
<text fill="#666666" font-family="sans-serif" font-size="13" font-style="italic" lengthAdjust="spacing" x="180" y="158">[Avro]</text>
</g>
<g id="lnk2" data-source-line="11">
<path d="M 100 250 L 300 250" fill="none" style="stroke:#666666;stroke-width:1;"/>
<polygon fill="#666666" points="300,250 294,246 296,250 294,254" style="stroke:#666666;stroke-width:1;"/>
<text fill="#666666" font-family="sans-serif" font-size="13" lengthAdjust="spacing" x="180" y="243">Queries</text>
<text fill="#666666" font-family="sans-serif" font-size="13" font-style="italic" lengthAdjust="spacing" x="180" y="258">[SQL]</text>
</g>
<g id="lnk3" data-source-line="12">
<path d="M 100 50 L 300 50" fill="none" style="stroke:#666666;stroke-width:1;"/>
<polygon fill="#666666" points="300,50 294,46 296,50 294,54" style="stroke:#666666;stroke-width:1;"/>
<text fill="#666666" font-family="sans-serif" font-size="13" lengthAdjust="spacing" x="170" y="43">~Loads</text>
<text fill="#666666" font-family="sans-serif" font-size="13" lengthAdjust="spacing" x="200" y="43">to</text>
</g>
</g>
</svg>
```

This has:
- `lnk1`: `~Streams to` — should be animated
- `lnk2`: `Queries` — should NOT be animated
- `lnk3`: `~Loads to` — should be animated

- [ ] **Step 2: Create fixtures directory**

```bash
mkdir -p tests/fixtures
```

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/sample-link-groups.svg
git commit -m "test: add SVG fixture with link groups for animation tests

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 1: Animate Script — Core

**Files:**
- Create: `scripts/animate.py`
- Create: `tests/test_animate.py`

- [ ] **Step 1: Write tests**

Create `tests/test_animate.py`:

```python
"""Tests for the SVG arrow animation post-processor."""
import os
import xml.etree.ElementTree as ET
import pytest
from scripts.animate import animate_svg, MARCHING_ANT_CSS

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "sample-link-groups.svg"
)
NS = "{http://www.w3.org/2000/svg}"


def parse_animated(svg_content: str) -> ET.Element:
    """Parse animated SVG string into an Element."""
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    return ET.fromstring(svg_content)


class TestAnimateSvg:
    def test_returns_string(self):
        source = open(FIXTURE_PATH).read()
        result = animate_svg(source)
        assert isinstance(result, str)

    def test_injects_style_element(self):
        source = open(FIXTURE_PATH).read()
        result = animate_svg(source)
        root = parse_animated(result)
        styles = root.findall(f"{NS}style")
        assert len(styles) >= 1
        assert "marching-ant" in styles[0].text

    def test_animated_path_gets_class(self):
        source = open(FIXTURE_PATH).read()
        result = animate_svg(source)
        root = parse_animated(result)
        # lnk1 has ~Streams — its path should have marching-ant class
        lnk1 = root.find(f".//{NS}g[@id='lnk1']")
        path = lnk1.find(f"{NS}path")
        assert "marching-ant" in (path.get("class") or "")

    def test_static_path_unchanged(self):
        source = open(FIXTURE_PATH).read()
        result = animate_svg(source)
        root = parse_animated(result)
        # lnk2 has Queries (no ~) — its path should NOT have the class
        lnk2 = root.find(f".//{NS}g[@id='lnk2']")
        path = lnk2.find(f"{NS}path")
        assert "marching-ant" not in (path.get("class") or "")

    def test_tilde_stripped_from_text(self):
        source = open(FIXTURE_PATH).read()
        result = animate_svg(source)
        root = parse_animated(result)
        lnk1 = root.find(f".//{NS}g[@id='lnk1']")
        texts = [t.text or "" for t in lnk1.findall(f"{NS}text")]
        for t in texts:
            assert "~" not in t

    def test_multiple_animated_links(self):
        source = open(FIXTURE_PATH).read()
        result = animate_svg(source)
        root = parse_animated(result)
        # lnk1 and lnk3 should both be animated
        for lnk_id in ["lnk1", "lnk3"]:
            g = root.find(f".//{NS}g[@id='{lnk_id}']")
            path = g.find(f"{NS}path")
            assert "marching-ant" in (path.get("class") or ""), f"{lnk_id} not animated"

    def test_no_markers_returns_unchanged(self):
        """SVG with no ~ markers should be returned with no style injected."""
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><g id="lnk1"><path d="M0 0" fill="none" style="stroke:#666;"/><text>Normal</text></g></svg>'
        result = animate_svg(svg)
        assert "marching-ant" not in result

    def test_plantuml_pi_stripped(self):
        source = open(FIXTURE_PATH).read()
        assert "<?plantuml" in source  # fixture has it
        result = animate_svg(source)
        assert "<?plantuml" not in result

    def test_returns_count(self):
        source = open(FIXTURE_PATH).read()
        result, count = animate_svg(source, return_count=True)
        assert count == 2  # lnk1 and lnk3
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/test_animate.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/animate.py`**

```python
#!/usr/bin/env python3
"""Post-process Kroki-rendered SVGs to add marching-ant animation on ~ arrows.

Usage:
    python scripts/animate.py rendered/c4/diagram.svg              # In-place
    python scripts/animate.py rendered/c4/diagram.svg --output out.svg
"""
import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

NS = "http://www.w3.org/2000/svg"
NS_PREFIX = f"{{{NS}}}"

MARCHING_ANT_CSS = """
.marching-ant {
  stroke-dasharray: 6 4;
  stroke-dashoffset: 10;
  animation: marching 0.5s linear infinite;
}
@keyframes marching {
  to { stroke-dashoffset: 0; }
}
""".strip()


def animate_svg(svg_content: str, return_count: bool = False):
    """Add marching-ant animation to arrows marked with ~ in their label text.

    Args:
        svg_content: Raw SVG string (may include <?plantuml?> PI)
        return_count: If True, return (result_str, animated_count) tuple

    Returns:
        Animated SVG string, or (svg_string, count) if return_count=True
    """
    # Strip PlantUML processing instruction
    content = re.sub(r"<\?plantuml[^?]*\?>", "", svg_content)

    ET.register_namespace("", NS)
    root = ET.fromstring(content)

    animated_count = 0

    # Find link groups
    for g in root.iter(f"{NS_PREFIX}g"):
        gid = g.get("id", "")
        if not gid.startswith("lnk"):
            continue

        # Check text children for ~ marker
        has_marker = False
        for text_elem in g.findall(f"{NS_PREFIX}text"):
            text_val = text_elem.text or ""
            if "~" in text_val:
                # Strip ~ from display text
                text_elem.text = text_val.replace("~", "")
                has_marker = True

        if not has_marker:
            continue

        # Add marching-ant class to the arrow path (fill=none)
        for path_elem in g.findall(f"{NS_PREFIX}path"):
            if path_elem.get("fill") == "none":
                existing = path_elem.get("class", "")
                if existing:
                    path_elem.set("class", f"{existing} marching-ant")
                else:
                    path_elem.set("class", "marching-ant")
                animated_count += 1
                break

    # Inject CSS style if any arrows were animated
    if animated_count > 0:
        style = ET.SubElement(root, f"{NS_PREFIX}style")
        style.text = MARCHING_ANT_CSS
        # Move style to first child position
        root.remove(style)
        root.insert(0, style)

    result = ET.tostring(root, encoding="unicode", xml_declaration=False)
    # Add XML declaration for proper SVG
    result = '<?xml version="1.0" encoding="UTF-8"?>\n' + result

    if return_count:
        return result, animated_count
    return result


def main():
    parser = argparse.ArgumentParser(description="Add marching-ant animation to SVG arrows marked with ~")
    parser.add_argument("svg", help="Path to SVG file")
    parser.add_argument("--output", "-o", help="Output path (default: overwrite in-place)")
    args = parser.parse_args()

    if not os.path.isfile(args.svg):
        print(f"File not found: {args.svg}", file=sys.stderr)
        sys.exit(1)

    source = open(args.svg).read()
    result, count = animate_svg(source, return_count=True)

    if count == 0:
        print("No animated arrows found (no ~ markers in link labels)")
        return

    out_path = args.output or args.svg
    with open(out_path, "w") as f:
        f.write(result)
    print(f"Animated {count} arrow(s) -> {out_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/test_animate.py -v
```

Expected: All 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/animate.py tests/test_animate.py
git commit -m "feat: add SVG arrow animation post-processor

Marching-ant CSS animation on arrows marked with ~ prefix.
Group-based detection via <g id=lnk...> elements.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Integrate with render.py

**Files:**
- Modify: `scripts/render.py`

- [ ] **Step 1: Add `--animate` flag to render.py**

Add to the argument parser:
```python
parser.add_argument("--animate", action="store_true", help="Add marching-ant animation to ~ arrows (SVG only)")
```

Add to the `render_file` function, after writing the SVG:
```python
if not dry_run and animate and fmt == "svg":
    from scripts.animate import animate_svg
    svg_content = open(out, "r").read()
    result, count = animate_svg(svg_content, return_count=True)
    if count > 0:
        with open(out, "w") as f:
            f.write(result)
        print(f"  Animated {count} arrow(s)")
```

Pass `animate=args.animate` through the call chain. Add a warning when `--animate` is used with `--png`:
```python
if args.animate and args.png:
    print("Warning: --animate is ignored with --png (SVG only)", file=sys.stderr)
```

- [ ] **Step 2: Run existing render tests to verify no regression**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/test_render.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add scripts/render.py
git commit -m "feat: add --animate flag to render.py for SVG arrow animation

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Update Agent Prompt

**Files:**
- Modify: `prompts/diagram-agent.md`

- [ ] **Step 1: Add animated arrows section to the agent prompt**

Append to `prompts/diagram-agent.md`:

```markdown

### Animated Arrows

To animate a relationship arrow (marching-ant flow effect), prefix the label with `~`:

```plantuml
Rel(event_stream, data_lake, "~Streams to", "Avro/JSON")   ' animated
Rel(data_analyst, data_warehouse, "Queries", "SQL")          ' static
```

Use animation sparingly — only on key data flows to draw attention. Too many animated arrows causes visual fatigue. Good candidates:
- Real-time streaming flows
- Active data pipelines
- Critical integration paths

After rendering, run: `python scripts/animate.py rendered/path/to/diagram.svg`
Or use: `python scripts/render.py diagram.puml --animate`
```

- [ ] **Step 2: Commit**

```bash
git add prompts/diagram-agent.md
git commit -m "docs: add animated arrows guidance to agent prompt

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: End-to-End Smoke Test

**Files:**
- Modify: `diagrams/c4/data-platform-container.puml` (add ~ to 2 arrows)

- [ ] **Step 1: Add `~` markers to two relationships in the data platform diagram**

Edit `diagrams/c4/data-platform-container.puml`, change these two lines:

```
Rel(event_stream, data_lake, "Streams to", "Avro/JSON")
```
to:
```
Rel(event_stream, data_lake, "~Streams to", "Avro/JSON")
```

and:
```
Rel(batch_etl, data_lake, "Loads to", "Parquet")
```
to:
```
Rel(batch_etl, data_lake, "~Loads to", "Parquet")
```

- [ ] **Step 2: Render with animation**

```bash
python scripts/render.py diagrams/c4/data-platform-container.puml --animate
```

Expected:
```
Rendering: diagrams/c4/data-platform-container.puml
  -> rendered/c4/data-platform-container.svg
  Animated 2 arrow(s)
```

- [ ] **Step 3: Verify the SVG contains animation CSS**

```bash
python -c "
svg = open('rendered/c4/data-platform-container.svg').read()
assert 'marching-ant' in svg, 'Missing marching-ant class'
assert 'stroke-dasharray' in svg, 'Missing dash array CSS'
assert '~' not in svg.split('</style>')[1], 'Tilde not stripped from text'
print('Animation verified.')
"
```

- [ ] **Step 4: Open and visually verify**

```bash
xdg-open rendered/c4/data-platform-container.svg
```

Expected: Two arrows (Streams to, Loads to) show flowing dash animation. All other arrows are static.

- [ ] **Step 5: Run full test suite**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add diagrams/c4/data-platform-container.puml
git commit -m "feat: add animated arrows to data platform diagram (streaming flows)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```
