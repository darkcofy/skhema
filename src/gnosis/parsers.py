"""File parsers for counting entries in YAML, CSV, and Markdown files.

Used by the readiness engine to determine artifact readiness based on
file content thresholds.
"""
import csv
import re
import os


def count_yaml_entries(path: str) -> int:
    """Count top-level entries in a YAML file using PyYAML."""
    import yaml
    if not os.path.isfile(path):
        return 0
    with open(path) as f:
        data = yaml.safe_load(f)
    if data is None:
        return 0
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        return len(data)
    return 0


def count_csv_rows(path: str) -> int:
    """Count data rows in a CSV file, excluding the header row. Blank rows skipped."""
    if not os.path.isfile(path):
        return 0
    with open(path, "r", newline="") as f:
        reader = csv.reader(f)
        rows = [row for row in reader if any(cell.strip() for cell in row)]
    return max(0, len(rows) - 1)


def count_md_entries(path: str) -> int:
    """Count H2 headings with non-empty body content.

    Supports two markdown shapes:
      1. Template-style files with a `## Capture` section followed by H2 subsections,
         optionally terminated by `## Completion criteria` (original authoring workflow).
      2. Flat auto-generated files where H2 sections sit directly under the H1 title
         (e.g. the synonym-conflicts.md rendered by `gnosis ingest synonyms`).

    In shape (1), scan only inside the Capture block. Otherwise count all H2 sections
    in the document.
    """
    if not os.path.isfile(path):
        return 0
    with open(path, "r") as f:
        content = f.read()

    capture_match = re.search(r"^## Capture\s*$", content, re.MULTILINE)
    if capture_match:
        after_capture = content[capture_match.end():]
        end_match = re.search(r"^## Completion criteria\s*$", after_capture, re.MULTILINE)
        section_text = after_capture[:end_match.start()] if end_match else after_capture
    else:
        section_text = content

    headings = list(re.finditer(r"^## (.+)$", section_text, re.MULTILINE))
    count = 0
    for i, heading in enumerate(headings):
        start = heading.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(section_text)
        body = section_text[start:end].strip()
        if body:
            count += 1
    return count


def check_md_sections(path: str, section_names: list[str]) -> dict[str, bool]:
    """Check if named H2 sections exist and have non-empty content."""
    result = {name: False for name in section_names}
    if not os.path.isfile(path):
        return result
    with open(path, "r") as f:
        content = f.read()
    headings = list(re.finditer(r"^## (.+)$", content, re.MULTILINE))
    for i, heading in enumerate(headings):
        heading_name = heading.group(1).strip().lower()
        start = heading.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(content)
        body = content[start:end].strip()
        for name in section_names:
            if heading_name == name.lower() and body:
                result[name] = True
    return result


def count_md_checkboxes(path: str) -> tuple[int, int]:
    """Count checked and total checkboxes. Returns (checked, total)."""
    if not os.path.isfile(path):
        return 0, 0
    with open(path, "r") as f:
        content = f.read()
    checked = len(re.findall(r"^\s*- \[x\]", content, re.MULTILINE | re.IGNORECASE))
    unchecked = len(re.findall(r"^\s*- \[ \]", content, re.MULTILINE))
    return checked, checked + unchecked


def is_template_only(path: str, template_content: str) -> bool:
    """Check if a file's content is identical to its template."""
    if not os.path.isfile(path):
        return True
    with open(path, "r") as f:
        content = f.read()
    return content == template_content
