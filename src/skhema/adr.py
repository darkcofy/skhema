"""ADR (Architecture Decision Record) parsing and linkage."""
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ADR:
    number: int
    title: str
    status: str
    path: Path
    elements: list[str] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)


_ELEMENT_RE = re.compile(r"<!--\s*skhema:elements\s+(.+?)\s*-->")
_CONCEPT_RE = re.compile(r"<!--\s*gnosis:concepts\s+(.+?)\s*-->")
_ADR_FILE_RE = re.compile(r"^ADR(\d+)-.*\.md$")
_TITLE_RE = re.compile(r"^#\s+ADR\d+:\s*(.+)$", re.MULTILINE)
_STATUS_RE = re.compile(r"^## Status\s*\n+(\w+)", re.MULTILINE)


def parse_adr(path: str) -> ADR:
    """Parse a single ADR markdown file."""
    text = open(path).read()
    filename = os.path.basename(path)

    m = _ADR_FILE_RE.match(filename)
    number = int(m.group(1)) if m else 0

    m = _TITLE_RE.search(text)
    title = m.group(1).strip() if m else filename

    m = _STATUS_RE.search(text)
    status = m.group(1).strip() if m else "Unknown"

    elements = []
    for m in _ELEMENT_RE.finditer(text):
        elements.extend(e.strip() for e in m.group(1).split(","))

    concepts = []
    for m in _CONCEPT_RE.finditer(text):
        concepts.extend(c.strip() for c in m.group(1).split(","))

    return ADR(
        number=number, title=title, status=status,
        path=Path(path), elements=elements, concepts=concepts,
    )


def discover_adrs(client_path: str) -> list[ADR]:
    """Discover and parse all ADR files in client's adrs/ directory."""
    adrs_dir = os.path.join(client_path, "adrs")
    if not os.path.isdir(adrs_dir):
        return []
    adrs = []
    for filename in sorted(os.listdir(adrs_dir)):
        if _ADR_FILE_RE.match(filename):
            adrs.append(parse_adr(os.path.join(adrs_dir, filename)))
    return adrs


def resolve_links(adrs: list[ADR], manifest: dict) -> dict[str, list[ADR]]:
    """Map element IDs to ADRs that reference them."""
    all_ids = set()
    for elements in manifest.values():
        for elem in elements:
            all_ids.add(elem["id"])

    links: dict[str, list[ADR]] = {}
    for adr in adrs:
        for elem_id in adr.elements:
            if elem_id not in all_ids:
                print(f"Warning: ADR{adr.number:02d} references unknown element '{elem_id}'",
                      file=sys.stderr)
                continue
            links.setdefault(elem_id, []).append(adr)
    return links


def resolve_concept_links(adrs: list[ADR]) -> dict[str, list[ADR]]:
    """Map concept names to ADRs that reference them."""
    links: dict[str, list[ADR]] = {}
    for adr in adrs:
        for concept in adr.concepts:
            links.setdefault(concept, []).append(adr)
    return links


def format_adr_list(adrs: list[ADR]) -> str:
    """Format ADR list for terminal display."""
    if not adrs:
        return "No ADRs found."
    lines = []
    for adr in adrs:
        elems = ", ".join(adr.elements) if adr.elements else "none"
        concepts = ", ".join(adr.concepts) if adr.concepts else "none"
        lines.append(f"ADR{adr.number:02d}: {adr.title} [{adr.status}]")
        lines.append(f"  Elements: {elems}")
        lines.append(f"  Concepts: {concepts}")
    return "\n".join(lines)


def format_coverage(adrs: list[ADR], manifest: dict) -> str:
    """Show elements/concepts without ADR coverage."""
    covered_elements = set()
    for adr in adrs:
        covered_elements.update(adr.elements)

    all_elements = set()
    for elements in manifest.values():
        for elem in elements:
            all_elements.add(elem["id"])

    uncovered = sorted(all_elements - covered_elements)
    if not uncovered:
        return "All elements have ADR coverage."
    lines = ["Elements without ADR coverage:"]
    for elem_id in uncovered:
        lines.append(f"  - {elem_id}")
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ADR management")
    parser.add_argument("--client", required=True, help="Client name")
    parser.add_argument("--coverage", action="store_true", help="Show coverage gaps")
    args = parser.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    client_path = os.path.join(root, "clients", args.client)

    if not os.path.isdir(client_path):
        print(f"Client '{args.client}' not found")
        return

    adrs = discover_adrs(client_path)

    if args.coverage:
        from skhema.manifest import parse_manifest
        manifest_path = os.path.join(root, "manifest.yaml")
        manifest = parse_manifest(manifest_path)
        print(format_coverage(adrs, manifest))
    else:
        print(format_adr_list(adrs))


if __name__ == "__main__":
    main()
