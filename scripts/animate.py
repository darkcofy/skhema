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
