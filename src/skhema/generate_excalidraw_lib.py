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

from skhema.manifest import parse_manifest

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
        "fillStyle": "cross-hatch",
        "strokeWidth": 1,
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


def build_library(manifest: dict, shape_map: dict) -> dict:
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
        "source": "skhema",
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

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    manifest_path = os.path.join(root, "manifest.yaml")
    manifest = parse_manifest(manifest_path)

    total_elements = sum(len(elems) for elems in manifest.values())
    total_domains = len(manifest)

    if gen_light:
        lib = build_library(manifest, C4_SHAPE_MAP_LIGHT)
        out_path = os.path.join(root, "src", "skhema", "lib", "skhema.excalidrawlib")
        with open(out_path, "w") as f:
            json.dump(lib, f, indent=2)
        print(f"Light: {out_path}")

    if gen_dark:
        lib = build_library(manifest, C4_SHAPE_MAP_DARK)
        out_path = os.path.join(root, "src", "skhema", "lib", "skhema-dark.excalidrawlib")
        with open(out_path, "w") as f:
            json.dump(lib, f, indent=2)
        print(f"Dark:  {out_path}")

    print(f"Generated {total_elements} elements across {total_domains} domains")


if __name__ == "__main__":
    main()
