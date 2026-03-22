#!/usr/bin/env python3
"""Validate PlantUML files against skhema conventions.

Usage:
    python scripts/validate.py            # Check everything
    python scripts/validate.py diagrams/  # Check only views
"""
import argparse
import os
import re
import sys
from pathlib import Path

# Ensure project root is on sys.path so `scripts.manifest` is importable
# whether invoked as `python scripts/validate.py` or via pytest.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from scripts.manifest import parse_manifest_ids

ELEMENT_PATTERNS = [
    r"^\s*(?:Person|Person_Ext|System|System_Ext|Container|Container_Ext|ContainerDb|ContainerDb_Ext|Component|Component_Ext)\s*\(",
]
ELEMENT_RE = re.compile("|".join(ELEMENT_PATTERNS), re.MULTILINE)

HEX_COLOUR_RE = re.compile(r"#[0-9A-Fa-f]{3,8}(?![0-9A-Fa-f])")

ID_RE = re.compile(
    r"(?:Person|Person_Ext|System|System_Ext|Container|Container_Ext|ContainerDb|ContainerDb_Ext|Component|Component_Ext)\s*\(\s*(\w+)"
)


def check_inline_definitions(source: str, filepath: str) -> list[str]:
    """Check that view-layer files don't define elements inline."""
    errors = []
    if not filepath.startswith("diagrams"):
        return errors
    for i, line in enumerate(source.splitlines(), 1):
        if ELEMENT_RE.match(line):
            errors.append(f"{filepath}:{i}: Inline element definition: {line.strip()}")
    return errors


def check_hardcoded_colours(source: str, filepath: str) -> list[str]:
    """Check that hex colours only appear in theme.puml, templates, and prompts."""
    errors = []
    if filepath.endswith("theme.puml") or filepath.startswith("templates") or filepath.startswith("prompts"):
        return errors
    for i, line in enumerate(source.splitlines(), 1):
        if HEX_COLOUR_RE.search(line):
            errors.append(f"{filepath}:{i}: Hardcoded colour: {line.strip()}")
    return errors


def check_duplicate_ids(models: dict[str, str]) -> list[str]:
    """Check for duplicate element IDs across model files."""
    seen: dict[str, str] = {}
    errors = []
    for filepath, source in models.items():
        for match in ID_RE.finditer(source):
            eid = match.group(1)
            if eid in seen:
                errors.append(
                    f"Duplicate element ID '{eid}' in {filepath} (first seen in {seen[eid]})"
                )
            else:
                seen[eid] = filepath
    return errors


def check_manifest_sync(manifest_path: str, models_dir: str) -> list[str]:
    """Check manifest.yaml matches model file contents."""
    errors = []
    if not os.path.isfile(manifest_path):
        return [f"manifest.yaml not found at {manifest_path}"]

    manifest_ids = parse_manifest_ids(manifest_path)

    file_ids = set()
    for fname in os.listdir(models_dir):
        if fname.endswith(".puml"):
            source = open(os.path.join(models_dir, fname)).read()
            for match in ID_RE.finditer(source):
                file_ids.add(match.group(1))

    missing_from_manifest = file_ids - manifest_ids
    missing_from_files = manifest_ids - file_ids

    for eid in sorted(missing_from_manifest):
        errors.append(f"Element '{eid}' in model files but missing from manifest.yaml")
    for eid in sorted(missing_from_files):
        errors.append(f"Element '{eid}' in manifest.yaml but missing from model files")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate skhema conventions")
    parser.add_argument("path", nargs="?", default=".", help="Path to check")
    args = parser.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    check_path = os.path.abspath(args.path)

    all_errors = []

    puml_files = []
    for dirpath, _, filenames in os.walk(check_path):
        for f in filenames:
            if f.endswith(".puml"):
                puml_files.append(os.path.join(dirpath, f))

    for fpath in sorted(puml_files):
        relpath = os.path.relpath(fpath, root)
        source = open(fpath).read()
        all_errors.extend(check_inline_definitions(source, relpath))
        all_errors.extend(check_hardcoded_colours(source, relpath))

    models_dir = os.path.join(root, "models")
    if os.path.isdir(models_dir):
        models = {}
        for f in os.listdir(models_dir):
            if f.endswith(".puml"):
                fpath = os.path.join(models_dir, f)
                models[f"models/{f}"] = open(fpath).read()
        all_errors.extend(check_duplicate_ids(models))

    manifest_path = os.path.join(root, "manifest.yaml")
    if os.path.isfile(manifest_path) and os.path.isdir(models_dir):
        all_errors.extend(check_manifest_sync(manifest_path, models_dir))

    if all_errors:
        print(f"Found {len(all_errors)} issue(s):\n")
        for e in all_errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("All checks passed.")


if __name__ == "__main__":
    main()
