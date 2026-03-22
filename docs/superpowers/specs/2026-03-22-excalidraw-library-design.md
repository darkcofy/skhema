# Excalidraw Library Generator: Design Spec

## Overview

A Python script that reads `manifest.yaml` and generates an Excalidraw library file (`.excalidrawlib`) containing all architecture primitives as pre-styled, hand-drawn shapes. Import into excalidraw.com for quick one-shot diagrams.

## Decisions

- **Output:** Single `lib/arch-diagrams.excalidrawlib` file (committed to git)
- **Input:** `manifest.yaml` (same source of truth as PlantUML)
- **Style:** Heavy hand-drawn feel (roughness: 2), yellow hue palette
- **Dependencies:** Python stdlib only (generates JSON)
- **Grouping:** 11 domains, same as PlantUML models

## Repo Additions

```
lib/arch-diagrams.excalidrawlib        # Generated library (committed)
diagrams/excalidraw/.gitkeep           # Where .excalidraw files are saved
scripts/generate-excalidraw-lib.py     # Generator script
```

## Shape Mapping

| C4 Type | Excalidraw Shape | Background | Stroke | strokeStyle |
|---|---|---|---|---|
| Person | Rectangle + person icon text | `#FDE68A` | `#D97706` | `solid` |
| Container | Rounded rectangle | `#FEF3C7` | `#D97706` | `solid` |
| ContainerDb | Rectangle with curved top/bottom lines (cylinder effect) | `#FCD34D` | `#B45309` | `solid` |
| System_Ext | Rectangle | `#F5F5F4` | `#A8A29E` | `dashed` |
| Container_Ext | Rounded rectangle | `#F5F5F4` | `#A8A29E` | `dashed` |

## Shared Shape Properties

- `roughness`: 2 (maximum hand-drawn feel)
- `opacity`: 100
- `fontFamily`: 1 (Excalidraw hand-drawn font)
- `strokeWidth`: 2
- Shape dimensions: 220w x 120h (consistent sizing for library items)
- Text: element name (bold, 20px) + description (normal, 14px) on separate lines

## Library File Format

```json
{
  "type": "excalidrawlib",
  "version": 2,
  "source": "arch-diagrams",
  "libraryItems": [
    {
      "id": "<element_id>",
      "status": "published",
      "name": "<Element Name> (<Domain>)",
      "elements": [
        { /* shape element */ },
        { /* name text element */ },
        { /* description text element */ }
      ],
      "created": <timestamp>
    }
  ]
}
```

Each library item contains:
1. A shape element (rectangle/diamond/etc. based on C4 type)
2. A text element for the element name (bold)
3. A text element for the description (smaller)

Elements are grouped by domain in output order. A domain header item is inserted before each group.

## Generator Script (`scripts/generate-excalidraw-lib.py`)

Usage:
```bash
python scripts/generate-excalidraw-lib.py
```

Behaviour:
1. Read `manifest.yaml` using the same stdlib line parser as `validate.py`
2. For each domain, for each element:
   - Map C4 type to Excalidraw shape properties
   - Generate shape element + text elements
   - Group into a library item
3. Write `lib/arch-diagrams.excalidrawlib` as formatted JSON
4. Output is deterministic (same input = same output) for clean git diffs

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
- Custom Excalidraw shapes beyond rectangles/cylinders
- Excalidraw dark mode theme variant
