# Excalidraw Library Generator Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers-extended-cc:subagent-driven-development (if subagents available) or superpowers-extended-cc:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate Excalidraw library files (light + dark mode) from `manifest.yaml` so architecture primitives can be dragged onto excalidraw.com canvases.

**Architecture:** A shared manifest parser (`scripts/manifest.py`) feeds both the existing `validate.py` and the new generator. The generator maps C4 types to Excalidraw shape properties and outputs `.excalidrawlib` JSON.

**Tech Stack:** Python 3 (stdlib only), JSON, Excalidraw library format v2

---

### Task 0: Shared Manifest Parser

**Files:**
- Create: `scripts/manifest.py`
- Create: `tests/test_manifest.py`
- Modify: `scripts/validate.py` (refactor to use shared parser)

- [ ] **Step 1: Write tests for the shared parser**

Create `tests/test_manifest.py`:

```python
"""Tests for the shared manifest parser."""
import os
import pytest
from scripts.manifest import parse_manifest


class TestParseManifest:
    def test_parses_domains(self, tmp_path):
        manifest = tmp_path / "manifest.yaml"
        manifest.write_text("""version: "1.0"

domains:
  storage:
    file: models/storage.puml
    elements:
      data_lake:
        type: ContainerDb
        description: "Raw + curated zones"
      data_warehouse:
        type: ContainerDb
        description: "Dimensional models"

diagrams: []
""")
        result = parse_manifest(str(manifest))
        assert "storage" in result
        assert len(result["storage"]) == 2

    def test_element_fields(self, tmp_path):
        manifest = tmp_path / "manifest.yaml"
        manifest.write_text("""version: "1.0"

domains:
  consumers:
    file: models/consumers.puml
    elements:
      data_analyst:
        type: Person
        description: "Queries data via BI/SQL tools"

diagrams: []
""")
        result = parse_manifest(str(manifest))
        elem = result["consumers"][0]
        assert elem["id"] == "data_analyst"
        assert elem["type"] == "Person"
        assert elem["description"] == "Queries data via BI/SQL tools"

    def test_multiple_domains(self, tmp_path):
        manifest = tmp_path / "manifest.yaml"
        manifest.write_text("""version: "1.0"

domains:
  consumers:
    file: models/consumers.puml
    elements:
      data_analyst:
        type: Person
        description: "Queries data"
  storage:
    file: models/storage.puml
    elements:
      data_lake:
        type: ContainerDb
        description: "Raw zones"

diagrams: []
""")
        result = parse_manifest(str(manifest))
        assert len(result) == 2
        assert "consumers" in result
        assert "storage" in result

    def test_real_manifest(self):
        """Test against the actual project manifest."""
        manifest_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "manifest.yaml"
        )
        if not os.path.isfile(manifest_path):
            pytest.skip("No manifest.yaml in project root")
        result = parse_manifest(manifest_path)
        assert len(result) == 11  # 11 domains
        # Spot-check a known element
        storage_ids = [e["id"] for e in result["storage"]]
        assert "data_lake" in storage_ids
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/test_manifest.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/manifest.py`**

```python
"""Shared manifest.yaml parser for arch-diagrams.

Parses the YAML manifest using line-based parsing (no PyYAML dependency).
Returns full element metadata grouped by domain.
"""
import os


def parse_manifest(manifest_path: str) -> dict[str, list[dict]]:
    """Parse manifest.yaml, return {domain: [{id, type, description}, ...]}.

    Manifest structure uses 2-space indentation:
      domains:          (indent 0)
        <domain>:       (indent 2)
          file: ...     (indent 4)
          elements:     (indent 4)
            <id>:       (indent 6) <- element ID
              type: ... (indent 8) <- element type
              description: ... (indent 8) <- element description
    """
    domains: dict[str, list[dict]] = {}
    current_domain = None
    current_element_id = None
    current_element: dict = {}
    in_domains = False
    in_elements = False

    with open(manifest_path) as f:
        for line in f:
            raw = line.rstrip("\n")
            if not raw.strip():
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            stripped = raw.strip()

            # Top-level "domains:" section
            if indent == 0 and stripped == "domains:":
                in_domains = True
                in_elements = False
                continue

            if not in_domains:
                continue

            # Exit domains section on another top-level key
            if indent == 0 and stripped.endswith(":"):
                # Save last element
                if current_domain and current_element_id and current_element:
                    current_element["id"] = current_element_id
                    domains.setdefault(current_domain, []).append(current_element)
                in_domains = False
                continue

            # Domain name (indent 2)
            if indent == 2 and stripped.endswith(":"):
                # Save previous element if any
                if current_domain and current_element_id and current_element:
                    current_element["id"] = current_element_id
                    domains.setdefault(current_domain, []).append(current_element)
                    current_element_id = None
                    current_element = {}
                current_domain = stripped.rstrip(":")
                in_elements = False
                continue

            # "elements:" marker (indent 4)
            if indent == 4 and stripped == "elements:":
                in_elements = True
                continue

            if not in_elements:
                continue

            # Element ID (indent 6)
            if indent == 6 and stripped.endswith(":"):
                # Save previous element
                if current_element_id and current_element:
                    current_element["id"] = current_element_id
                    domains.setdefault(current_domain, []).append(current_element)
                current_element_id = stripped.rstrip(":")
                current_element = {}
                continue

            # Element properties (indent 8)
            if indent == 8 and ":" in stripped:
                key, _, value = stripped.partition(":")
                value = value.strip().strip('"')
                current_element[key.strip()] = value

    # Save last element
    if current_domain and current_element_id and current_element:
        current_element["id"] = current_element_id
        domains.setdefault(current_domain, []).append(current_element)

    return domains


def parse_manifest_ids(manifest_path: str) -> set[str]:
    """Convenience: return just element IDs (for validate.py compatibility)."""
    ids = set()
    for elements in parse_manifest(manifest_path).values():
        for elem in elements:
            ids.add(elem["id"])
    return ids
```

- [ ] **Step 4: Run tests**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/test_manifest.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Refactor `validate.py` to use shared parser**

Replace `parse_manifest_element_ids()` and its call site in `validate.py`:

1. Remove the `parse_manifest_element_ids` function entirely
2. Add `from scripts.manifest import parse_manifest_ids` at the top
3. In `check_manifest_sync`, replace `manifest_ids = parse_manifest_element_ids(manifest_path)` with `manifest_ids = parse_manifest_ids(manifest_path)`

- [ ] **Step 6: Run all existing tests to verify no regressions**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/ -v
```

Expected: All tests PASS (render + validate + manifest).

- [ ] **Step 7: Run validation against real repo**

```bash
python scripts/validate.py
```

Expected: "All checks passed."

- [ ] **Step 8: Commit**

```bash
git add scripts/manifest.py tests/test_manifest.py scripts/validate.py
git commit -m "refactor: extract shared manifest parser, refactor validate.py

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 1: Excalidraw Library Generator — Light Mode

**Files:**
- Create: `scripts/generate-excalidraw-lib.py`
- Create: `tests/test_generate_excalidraw.py`

- [ ] **Step 1: Write tests**

Create `tests/test_generate_excalidraw.py`:

```python
"""Tests for the Excalidraw library generator."""
import json
import os
import pytest
from scripts.generate_excalidraw_lib import (
    build_library_item,
    build_library,
    C4_SHAPE_MAP_LIGHT,
)


class TestBuildLibraryItem:
    def test_container_shape(self):
        item = build_library_item(
            element_id="data_lake",
            name="Data Lake",
            description="Raw + curated zones",
            c4_type="ContainerDb",
            domain="storage",
            shape_map=C4_SHAPE_MAP_LIGHT,
        )
        assert item["id"] == "data_lake"
        assert item["name"] == "Data Lake (storage)"
        assert item["status"] == "published"
        assert len(item["elements"]) == 2  # shape + text

    def test_shape_properties(self):
        item = build_library_item(
            element_id="auth_gateway",
            name="Auth Gateway",
            description="API auth enforcement",
            c4_type="Container",
            domain="security",
            shape_map=C4_SHAPE_MAP_LIGHT,
        )
        shape = item["elements"][0]
        assert shape["type"] == "rectangle"
        assert shape["roughness"] == 2
        assert shape["backgroundColor"] == "#FEF3C7"
        assert shape["strokeColor"] == "#D97706"
        assert shape["strokeStyle"] == "solid"
        assert shape["roundness"] == {"type": 3}

    def test_external_dashed(self):
        item = build_library_item(
            element_id="firewall",
            name="Firewall",
            description="Network perimeter",
            c4_type="Container_Ext",
            domain="security",
            shape_map=C4_SHAPE_MAP_LIGHT,
        )
        shape = item["elements"][0]
        assert shape["strokeStyle"] == "dashed"
        assert shape["backgroundColor"] == "#F5F5F4"

    def test_person_emoji_prefix(self):
        item = build_library_item(
            element_id="data_analyst",
            name="Data Analyst",
            description="Queries data",
            c4_type="Person",
            domain="consumers",
            shape_map=C4_SHAPE_MAP_LIGHT,
        )
        text = item["elements"][1]
        assert text["text"].startswith("👤")

    def test_db_emoji_prefix(self):
        item = build_library_item(
            element_id="data_lake",
            name="Data Lake",
            description="Raw zones",
            c4_type="ContainerDb",
            domain="storage",
            shape_map=C4_SHAPE_MAP_LIGHT,
        )
        text = item["elements"][1]
        assert text["text"].startswith("🗄")

    def test_group_ids_shared(self):
        item = build_library_item(
            element_id="test_elem",
            name="Test",
            description="Desc",
            c4_type="Container",
            domain="test",
            shape_map=C4_SHAPE_MAP_LIGHT,
        )
        shape = item["elements"][0]
        text = item["elements"][1]
        assert shape["groupIds"] == text["groupIds"]
        assert len(shape["groupIds"]) == 1

    def test_text_bound_to_shape(self):
        item = build_library_item(
            element_id="test_elem",
            name="Test",
            description="Desc",
            c4_type="Container",
            domain="test",
            shape_map=C4_SHAPE_MAP_LIGHT,
        )
        shape = item["elements"][0]
        text = item["elements"][1]
        assert text["containerId"] == shape["id"]
        assert {"id": text["id"], "type": "text"} in shape["boundElements"]

    def test_deterministic_seed(self):
        item1 = build_library_item("x", "X", "d", "Container", "t", C4_SHAPE_MAP_LIGHT)
        item2 = build_library_item("x", "X", "d", "Container", "t", C4_SHAPE_MAP_LIGHT)
        assert item1["elements"][0]["seed"] == item2["elements"][0]["seed"]


class TestBuildLibrary:
    def test_structure(self):
        manifest = {
            "storage": [
                {"id": "data_lake", "type": "ContainerDb", "description": "Raw zones"},
            ]
        }
        lib = build_library(manifest, C4_SHAPE_MAP_LIGHT)
        assert lib["type"] == "excalidrawlib"
        assert lib["version"] == 2
        assert len(lib["libraryItems"]) == 1

    def test_valid_json(self):
        manifest = {
            "storage": [
                {"id": "data_lake", "type": "ContainerDb", "description": "Raw zones"},
            ]
        }
        lib = build_library(manifest, C4_SHAPE_MAP_LIGHT)
        # Should be serializable
        output = json.dumps(lib, indent=2)
        parsed = json.loads(output)
        assert parsed["type"] == "excalidrawlib"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/test_generate_excalidraw.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/generate_excalidraw_lib.py`**

Note: filename uses underscores for Python import compatibility, CLI alias via `generate-excalidraw-lib.py` symlink if desired.

```python
#!/usr/bin/env python3
"""Generate Excalidraw library files from manifest.yaml.

Usage:
    python scripts/generate_excalidraw_lib.py            # Both light + dark
    python scripts/generate_excalidraw_lib.py --light     # Light only
    python scripts/generate_excalidraw_lib.py --dark      # Dark only
"""
import argparse
import json
import os
import sys
import time

from scripts.manifest import parse_manifest

# --- Shape maps ---

C4_SHAPE_MAP_LIGHT = {
    "Person":        {"bg": "#FDE68A", "stroke": "#D97706", "text": "#333333", "strokeStyle": "solid", "roundness": None,          "prefix": "👤 "},
    "Container":     {"bg": "#FEF3C7", "stroke": "#D97706", "text": "#333333", "strokeStyle": "solid", "roundness": {"type": 3}, "prefix": ""},
    "ContainerDb":   {"bg": "#FCD34D", "stroke": "#B45309", "text": "#333333", "strokeStyle": "solid", "roundness": {"type": 3}, "prefix": "🗄 "},
    "System_Ext":    {"bg": "#F5F5F4", "stroke": "#A8A29E", "text": "#666666", "strokeStyle": "dashed", "roundness": None,          "prefix": ""},
    "Container_Ext": {"bg": "#F5F5F4", "stroke": "#A8A29E", "text": "#666666", "strokeStyle": "dashed", "roundness": {"type": 3}, "prefix": ""},
}

C4_SHAPE_MAP_DARK = {
    "Person":        {"bg": "#92400E", "stroke": "#FCD34D", "text": "#FDE68A", "strokeStyle": "solid", "roundness": None,          "prefix": "👤 "},
    "Container":     {"bg": "#78350F", "stroke": "#D97706", "text": "#FEF3C7", "strokeStyle": "solid", "roundness": {"type": 3}, "prefix": ""},
    "ContainerDb":   {"bg": "#713F12", "stroke": "#EAB308", "text": "#FEF9C3", "strokeStyle": "solid", "roundness": {"type": 3}, "prefix": "🗄 "},
    "System_Ext":    {"bg": "#44403C", "stroke": "#78716C", "text": "#D6D3D1", "strokeStyle": "dashed", "roundness": None,          "prefix": ""},
    "Container_Ext": {"bg": "#44403C", "stroke": "#78716C", "text": "#D6D3D1", "strokeStyle": "dashed", "roundness": {"type": 3}, "prefix": ""},
}


def _seed(element_id: str) -> int:
    """Deterministic seed from element ID."""
    return hash(element_id) & 0x7FFFFFFF


def build_library_item(
    element_id: str,
    name: str,
    description: str,
    c4_type: str,
    domain: str,
    shape_map: dict,
) -> dict:
    """Build a single Excalidraw library item (shape + bound text)."""
    props = shape_map.get(c4_type, shape_map["Container"])  # fallback
    now = int(time.time() * 1000)
    seed = _seed(element_id)
    shape_id = f"{element_id}_shape"
    text_id = f"{element_id}_text"
    group_id = f"{element_id}_group"

    prefix = props["prefix"]
    label = f"{prefix}{name}\n{description}"

    shape = {
        "id": shape_id,
        "type": "rectangle",
        "x": 0,
        "y": 0,
        "width": 220,
        "height": 120,
        "angle": 0,
        "strokeColor": props["stroke"],
        "backgroundColor": props["bg"],
        "fillStyle": "hachure",
        "strokeWidth": 2,
        "strokeStyle": props["strokeStyle"],
        "roughness": 2,
        "opacity": 100,
        "seed": seed,
        "version": 1,
        "versionNonce": seed,
        "updated": now,
        "isDeleted": False,
        "groupIds": [group_id],
        "frameId": None,
        "index": "a0",
        "link": None,
        "locked": False,
        "roundness": props["roundness"],
        "boundElements": [{"id": text_id, "type": "text"}],
    }

    text = {
        "id": text_id,
        "type": "text",
        "x": 10,
        "y": 30,
        "width": 200,
        "height": 60,
        "angle": 0,
        "strokeColor": props["text"],
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "seed": seed + 1,
        "version": 1,
        "versionNonce": seed + 1,
        "updated": now,
        "isDeleted": False,
        "groupIds": [group_id],
        "frameId": None,
        "index": "a1",
        "link": None,
        "locked": False,
        "roundness": None,
        "boundElements": None,
        "text": label,
        "fontSize": 16,
        "fontFamily": 1,
        "textAlign": "center",
        "verticalAlign": "middle",
        "containerId": shape_id,
        "autoResize": True,
        "lineHeight": 1.25,
    }

    return {
        "id": element_id,
        "status": "published",
        "name": f"{name} ({domain})",
        "elements": [shape, text],
        "created": now,
    }


def build_library(manifest: dict[str, list[dict]], shape_map: dict) -> dict:
    """Build the full Excalidraw library from parsed manifest data."""
    items = []
    for domain in sorted(manifest.keys()):
        for elem in sorted(manifest[domain], key=lambda e: e["id"]):
            # Convert snake_case ID to Title Case name
            name = elem.get("id", "").replace("_", " ").title()
            # Use manifest description, or element name if missing
            if "description" in elem:
                # Strip surrounding quotes if present
                desc = elem["description"].strip('"')
            else:
                desc = name
            items.append(build_library_item(
                element_id=elem["id"],
                name=name,
                description=desc,
                c4_type=elem.get("type", "Container"),
                domain=domain,
                shape_map=shape_map,
            ))

    return {
        "type": "excalidrawlib",
        "version": 2,
        "source": "arch-diagrams",
        "libraryItems": items,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate Excalidraw library from manifest")
    parser.add_argument("--light", action="store_true", help="Generate light mode only")
    parser.add_argument("--dark", action="store_true", help="Generate dark mode only")
    args = parser.parse_args()

    # Default: generate both
    gen_light = not args.dark or args.light
    gen_dark = not args.light or args.dark
    if not args.light and not args.dark:
        gen_light = True
        gen_dark = True

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_path = os.path.join(root, "manifest.yaml")
    manifest = parse_manifest(manifest_path)

    total_elements = sum(len(elems) for elems in manifest.values())
    total_domains = len(manifest)

    if gen_light:
        lib = build_library(manifest, C4_SHAPE_MAP_LIGHT)
        out_path = os.path.join(root, "lib", "arch-diagrams.excalidrawlib")
        with open(out_path, "w") as f:
            json.dump(lib, f, indent=2)
        print(f"Light: {out_path}")

    if gen_dark:
        lib = build_library(manifest, C4_SHAPE_MAP_DARK)
        out_path = os.path.join(root, "lib", "arch-diagrams-dark.excalidrawlib")
        with open(out_path, "w") as f:
            json.dump(lib, f, indent=2)
        print(f"Dark:  {out_path}")

    print(f"Generated {total_elements} elements across {total_domains} domains")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/test_generate_excalidraw.py -v
```

Expected: All 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_excalidraw_lib.py tests/test_generate_excalidraw.py
git commit -m "feat: add Excalidraw library generator with light + dark mode

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Generate Libraries & Smoke Test

**Files:**
- Create: `lib/arch-diagrams.excalidrawlib` (generated)
- Create: `lib/arch-diagrams-dark.excalidrawlib` (generated)
- Create: `diagrams/excalidraw/.gitkeep`

- [ ] **Step 1: Create excalidraw diagrams directory**

```bash
mkdir -p diagrams/excalidraw && touch diagrams/excalidraw/.gitkeep
```

- [ ] **Step 2: Run generator**

```bash
python scripts/generate_excalidraw_lib.py
```

Expected output:
```
Light: /home/alfred/code/arch-diagrams/lib/arch-diagrams.excalidrawlib
Dark:  /home/alfred/code/arch-diagrams/lib/arch-diagrams-dark.excalidrawlib
Generated 60 elements across 11 domains
```

- [ ] **Step 3: Validate generated JSON is well-formed**

```bash
python -c "
import json
light = json.load(open('lib/arch-diagrams.excalidrawlib'))
dark = json.load(open('lib/arch-diagrams-dark.excalidrawlib'))
print(f'Light: {len(light[\"libraryItems\"])} items')
print(f'Dark:  {len(dark[\"libraryItems\"])} items')
assert light['type'] == 'excalidrawlib'
assert dark['type'] == 'excalidrawlib'
assert len(light['libraryItems']) == len(dark['libraryItems'])
print('Valid.')
"
```

- [ ] **Step 4: Spot-check a known element in light mode**

```bash
python -c "
import json
lib = json.load(open('lib/arch-diagrams.excalidrawlib'))
for item in lib['libraryItems']:
    if item['id'] == 'data_lake':
        shape = item['elements'][0]
        text = item['elements'][1]
        print(f'Name: {item[\"name\"]}')
        print(f'BG: {shape[\"backgroundColor\"]}')
        print(f'Stroke: {shape[\"strokeColor\"]}')
        print(f'Text: {text[\"text\"]}')
        print(f'GroupIds match: {shape[\"groupIds\"] == text[\"groupIds\"]}')
        break
"
```

Expected:
```
Name: Data Lake (storage)
BG: #FCD34D
Stroke: #B45309
Text: 🗄 Data Lake
Raw + curated zones
GroupIds match: True
```

- [ ] **Step 5: Spot-check dark mode variant**

```bash
python -c "
import json
lib = json.load(open('lib/arch-diagrams-dark.excalidrawlib'))
for item in lib['libraryItems']:
    if item['id'] == 'data_lake':
        shape = item['elements'][0]
        print(f'Dark BG: {shape[\"backgroundColor\"]}')
        print(f'Dark Stroke: {shape[\"strokeColor\"]}')
        break
"
```

Expected:
```
Dark BG: #713F12
Dark Stroke: #EAB308
```

- [ ] **Step 6: Run full test suite**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git add lib/arch-diagrams.excalidrawlib lib/arch-diagrams-dark.excalidrawlib diagrams/excalidraw/.gitkeep
git commit -m "feat: generate Excalidraw libraries (light + dark, 60 elements)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```
