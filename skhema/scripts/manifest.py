"""Shared manifest.yaml parser for skhema.

Parses the YAML manifest using PyYAML.
Returns full element metadata grouped by domain.
"""
import yaml


def parse_manifest(manifest_path: str) -> dict[str, list[dict]]:
    """Parse manifest.yaml and return {domain: [elements]} using PyYAML."""
    with open(manifest_path) as f:
        data = yaml.safe_load(f)

    result = {}
    for domain_name, domain_data in (data.get("domains") or {}).items():
        elements = []
        for elem_id, elem_props in (domain_data.get("elements") or {}).items():
            elements.append({
                "id": elem_id,
                "type": (elem_props or {}).get("type", ""),
                "description": (elem_props or {}).get("description", ""),
            })
        result[domain_name] = elements
    return result


def parse_manifest_ids(manifest_path: str) -> set[str]:
    """Convenience: return just element IDs (for validate.py compatibility)."""
    ids = set()
    for elements in parse_manifest(manifest_path).values():
        for elem in elements:
            ids.add(elem["id"])
    return ids
