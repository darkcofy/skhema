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
