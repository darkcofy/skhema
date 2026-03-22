# Excalidraw Library Generator: Design Spec

## Overview

A Python script that reads `manifest.yaml` and generates an Excalidraw library file (`.excalidrawlib`) containing all architecture primitives as pre-styled, hand-drawn shapes. Import into excalidraw.com for quick one-shot diagrams.

## Decisions

- **Output:** Single `lib/arch-diagrams.excalidrawlib` file (committed to git)
- **Input:** `manifest.yaml` (same source of truth as PlantUML)
- **Style:** Heavy hand-drawn feel (roughness: 2), yellow hue palette
- **Dependencies:** Python stdlib only (generates JSON)
- **Grouping:** 11 domains (consumers, ingestion, storage, processing, serving, governance, integration, security, iot, ml_platform, genai)

## Repo Additions

```
lib/arch-diagrams.excalidrawlib        # Generated library (committed)
diagrams/excalidraw/.gitkeep           # Where .excalidraw files are saved
scripts/manifest.py                    # Shared manifest parser (new)
scripts/generate-excalidraw-lib.py     # Generator script
```

## Shared Manifest Parser (`scripts/manifest.py`)

New shared module replacing the inline parser in `validate.py`. Returns full element metadata, not just IDs.

```python
def parse_manifest(manifest_path: str) -> dict[str, list[dict]]:
    """Parse manifest.yaml, return {domain: [{id, type, description}, ...]}"""
```

Both `validate.py` and `generate-excalidraw-lib.py` import from this module. `validate.py` refactored to use it.

## Shape Mapping

| C4 Type | Excalidraw `type` | roundness | strokeStyle | Background | Stroke | Label prefix |
|---|---|---|---|---|---|---|
| Person | `rectangle` | `null` (sharp) | `solid` | `#FDE68A` | `#D97706` | `👤 ` |
| Container | `rectangle` | `{"type": 3}` | `solid` | `#FEF3C7` | `#D97706` | none |
| ContainerDb | `rectangle` | `{"type": 3}` | `solid` | `#FCD34D` | `#B45309` | `🗄 ` |
| System_Ext | `rectangle` | `null` (sharp) | `dashed` | `#F5F5F4` | `#A8A29E` | none |
| Container_Ext | `rectangle` | `{"type": 3}` | `dashed` | `#F5F5F4` | `#A8A29E` | none |

Person gets a person emoji prefix, ContainerDb gets a database emoji prefix — simple visual differentiation without custom shapes.

## Shared Shape Properties

- `roughness`: 2 (maximum hand-drawn feel)
- `fillStyle`: `"hachure"` (hand-drawn fill pattern)
- `opacity`: 100
- `fontFamily`: 1 (Excalidraw hand-drawn font — Virgil)
- `strokeWidth`: 2
- `angle`: 0
- `isDeleted`: false
- `locked`: false
- Shape dimensions: 220w x 120h

## Element Grouping

All elements within a library item (shape + text labels) share a `groupIds` array with a common group ID so they drag as a single unit:

```
groupIds: ["{element_id}_group"]
```

The shape element has `boundElements` referencing its text children. Text elements have `containerId` referencing the shape.

## Text Layout

Each library item has one text element inside the shape:

- **Combined text:** `"{prefix}{Element Name}\n{description}"`
- Font size: 16px
- `textAlign`: `"center"`
- `verticalAlign`: `"middle"`
- Text is bound to the shape via `containerId` — Excalidraw auto-centers it

## Deterministic Output

For clean git diffs on regeneration:

- `seed`: `hash(element_id) & 0x7FFFFFFF` (deterministic per element)
- `created`: fixed epoch `1711065600000` (2024-03-22)
- `version`: 1
- `versionNonce`: same as `seed`
- `updated`: same as `created`
- Library items ordered: domains alphabetically, elements alphabetically within domain

## Complete Library Item Example

```json
{
  "id": "data_lake",
  "status": "published",
  "name": "Data Lake (storage)",
  "elements": [
    {
      "id": "data_lake_shape",
      "type": "rectangle",
      "x": 0,
      "y": 0,
      "width": 220,
      "height": 120,
      "angle": 0,
      "strokeColor": "#B45309",
      "backgroundColor": "#FCD34D",
      "fillStyle": "hachure",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 2,
      "opacity": 100,
      "seed": 1234567890,
      "version": 1,
      "versionNonce": 1234567890,
      "updated": 1711065600000,
      "isDeleted": false,
      "groupIds": ["data_lake_group"],
      "frameId": null,
      "index": "a0",
      "link": null,
      "locked": false,
      "roundness": {"type": 3},
      "boundElements": [
        {"id": "data_lake_text", "type": "text"}
      ]
    },
    {
      "id": "data_lake_text",
      "type": "text",
      "x": 10,
      "y": 30,
      "width": 200,
      "height": 60,
      "angle": 0,
      "strokeColor": "#333333",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "strokeStyle": "solid",
      "roughness": 0,
      "opacity": 100,
      "seed": 1234567891,
      "version": 1,
      "versionNonce": 1234567891,
      "updated": 1711065600000,
      "isDeleted": false,
      "groupIds": ["data_lake_group"],
      "frameId": null,
      "index": "a1",
      "link": null,
      "locked": false,
      "roundness": null,
      "boundElements": null,
      "text": "🗄 Data Lake\nRaw + curated zones",
      "fontSize": 16,
      "fontFamily": 1,
      "textAlign": "center",
      "verticalAlign": "middle",
      "containerId": "data_lake_shape",
      "autoResize": true,
      "lineHeight": 1.25
    }
  ],
  "created": 1711065600000
}
```

## Generator Script (`scripts/generate-excalidraw-lib.py`)

Usage:
```bash
python scripts/generate-excalidraw-lib.py
```

Behaviour:
1. Read `manifest.yaml` using `scripts/manifest.py` shared parser
2. For each domain (alphabetical), for each element (alphabetical):
   - Map C4 type to shape properties via the mapping table
   - Generate shape element with deterministic seed
   - Generate bound text element with name + description
   - Group into a library item with shared `groupIds`
3. Write `lib/arch-diagrams.excalidrawlib` as formatted JSON (indent=2)
4. Print summary: "Generated N elements across M domains"

## Workflow

1. Add/modify elements in `manifest.yaml` and model `.puml` files
2. Run `python scripts/generate-excalidraw-lib.py` to regenerate
3. Open excalidraw.com
4. Library icon > Import > select `lib/arch-diagrams.excalidrawlib`
5. Drag elements onto canvas, connect with arrows, save as `.excalidraw`
6. Save `.excalidraw` files to `diagrams/excalidraw/` and commit

## Out of Scope

- Auto-layout or relationship generation
- Bi-directional sync (Excalidraw back to PlantUML)
- Custom Excalidraw shapes beyond styled rectangles
- Excalidraw dark mode theme variant
