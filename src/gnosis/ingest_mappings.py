"""Ingest LLM-extracted source-to-canonical mappings into 03_mappings/source-to-canonical.csv.

Matches the output format of `skills/gnosis/mapping-source-systems-to-concepts.md`.
BYOLLM — input is CSV the user has in their hands.

Shape notes:

- Input/output is CSV (the skill outputs CSV to match the human-editable target).
- Merge is **gentle** (like glossary): existing rows are not clobbered. Notes are
  unioned (new lines appended if different). New rows are appended. Edit the CSV
  by hand to revise an existing mapping — re-ingesting won't overwrite curated content.
- Rows are keyed by the `(source_system, source_entity, source_field)` triple.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

from gnosis._common import run_ingest_cli
from gnosis.ingest import (
    LintWarning,
    SchemaError,
    load_concepts_yaml,
    write_warnings_file,
)


REQUIRED_COLUMNS = {
    "source_system", "source_entity", "source_field",
    "canonical_concept", "canonical_property", "mapping_type", "confidence",
}
OPTIONAL_COLUMNS = {"notes"}
ALLOWED_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS
COLUMN_ORDER = [
    "source_system", "source_entity", "source_field",
    "canonical_concept", "canonical_property", "mapping_type", "confidence", "notes",
]

ALLOWED_MAPPING_TYPES = {"direct", "transform", "foreign_key", "derived", "ambiguous", "unmapped"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

@dataclass
class MappingEntry:
    source_system: str
    source_entity: str
    source_field: str
    canonical_concept: str
    canonical_property: str
    mapping_type: str
    confidence: str
    notes: str = ""


def parse_mapping_rows(header: list[str], rows: list[dict]) -> list[MappingEntry]:
    """Validate CSV header + rows, return MappingEntry list.

    Raises SchemaError on any violation.
    """
    issues: list[str] = []

    header_set = set(header)
    missing = REQUIRED_COLUMNS - header_set
    if missing:
        issues.append(f"missing required column(s): {sorted(missing)}")
    unknown = header_set - ALLOWED_COLUMNS
    if unknown:
        issues.append(f"unknown column(s) in header: {sorted(unknown)}")

    if issues:
        raise SchemaError(issues)

    entries: list[MappingEntry] = []
    seen_keys: set[tuple[str, str, str]] = set()

    for i, row in enumerate(rows):
        local: list[str] = []
        label = f"row[{i}]"

        ss = (row.get("source_system") or "").strip()
        se = (row.get("source_entity") or "").strip()
        sf = (row.get("source_field") or "").strip()

        if not ss:
            local.append(f"{label}: 'source_system' is required")
        if not se:
            local.append(f"{label}: 'source_entity' is required")
        if not sf:
            local.append(f"{label}: 'source_field' is required")

        if ss and se and sf:
            label = f"mapping {ss}.{se}.{sf}"
            key = (ss.casefold(), se.casefold(), sf.casefold())
            if key in seen_keys:
                local.append(f"{label}: duplicate (source_system, source_entity, source_field) in the same ingest")
            seen_keys.add(key)

        mtype = (row.get("mapping_type") or "").strip().lower()
        if mtype not in ALLOWED_MAPPING_TYPES:
            local.append(
                f"{label}: 'mapping_type' must be one of {sorted(ALLOWED_MAPPING_TYPES)}, got '{mtype}'"
            )

        conf = (row.get("confidence") or "").strip().lower()
        if conf not in ALLOWED_CONFIDENCE:
            local.append(
                f"{label}: 'confidence' must be one of {sorted(ALLOWED_CONFIDENCE)}, got '{conf}'"
            )

        cc = (row.get("canonical_concept") or "").strip()
        cp = (row.get("canonical_property") or "").strip()
        notes = (row.get("notes") or "").strip()

        if local:
            issues.extend(local)
            continue

        entries.append(
            MappingEntry(
                source_system=ss,
                source_entity=se,
                source_field=sf,
                canonical_concept=cc,
                canonical_property=cp,
                mapping_type=mtype,
                confidence=conf,
                notes=notes,
            )
        )

    if issues:
        raise SchemaError(issues)

    return entries


def load_mappings_csv(path: str) -> list[MappingEntry]:
    """Load an existing mappings CSV. Returns [] if missing; raises SchemaError if malformed."""
    if not os.path.isfile(path):
        return []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        rows = list(reader)
    # An empty CSV with just a header is valid — no rows to parse.
    if not rows:
        # Still validate the header shape.
        if header:
            parse_mapping_rows(header, [])
        return []
    return parse_mapping_rows(header, rows)


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------

def lint_unknown_canonical_concept(
    entries: list[MappingEntry], known_concepts: set[str]
) -> list[LintWarning]:
    """Flag canonical_concept values that don't match a known concept."""
    known_fold = {c.casefold() for c in known_concepts}
    warnings: list[LintWarning] = []
    for e in entries:
        if not e.canonical_concept:
            continue
        if e.canonical_concept.casefold() not in known_fold:
            warnings.append(
                LintWarning(
                    rule="unknown_canonical_concept",
                    concept=f"{e.source_system}.{e.source_entity}.{e.source_field}",
                    message=(
                        f"canonical_concept '{e.canonical_concept}' is not in "
                        "02_concepts/candidate-concepts.yaml"
                    ),
                )
            )
    return warnings


def lint_low_confidence_without_notes(entries: list[MappingEntry]) -> list[LintWarning]:
    warnings: list[LintWarning] = []
    for e in entries:
        if e.confidence == "low" and not e.notes:
            warnings.append(
                LintWarning(
                    rule="low_confidence_without_notes",
                    concept=f"{e.source_system}.{e.source_entity}.{e.source_field}",
                    message=(
                        "confidence=low with empty notes — document the uncertainty "
                        "so the next reviewer can act on it"
                    ),
                )
            )
    return warnings


def lint_ambiguous_without_notes(entries: list[MappingEntry]) -> list[LintWarning]:
    warnings: list[LintWarning] = []
    for e in entries:
        if e.mapping_type in {"ambiguous", "unmapped"} and not e.notes:
            warnings.append(
                LintWarning(
                    rule="ambiguous_without_notes",
                    concept=f"{e.source_system}.{e.source_entity}.{e.source_field}",
                    message=(
                        f"mapping_type={e.mapping_type} with empty notes — "
                        "explain the ambiguity or no one can resolve it"
                    ),
                )
            )
    return warnings


def run_lints(
    entries: list[MappingEntry], known_concepts: set[str]
) -> list[LintWarning]:
    warnings: list[LintWarning] = []
    warnings.extend(lint_unknown_canonical_concept(entries, known_concepts))
    warnings.extend(lint_low_confidence_without_notes(entries))
    warnings.extend(lint_ambiguous_without_notes(entries))
    return warnings


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

@dataclass
class MergeReport:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def _key(e: MappingEntry) -> tuple[str, str, str]:
    return (e.source_system.casefold(), e.source_entity.casefold(), e.source_field.casefold())


def _pretty(e: MappingEntry) -> str:
    return f"{e.source_system}.{e.source_entity}.{e.source_field}"


def merge_mappings(
    existing: list[MappingEntry], new: list[MappingEntry]
) -> tuple[list[MappingEntry], MergeReport]:
    """Gentle merge keyed by (source_system, source_entity, source_field).

    - New triple → appended.
    - Existing triple → `notes` unioned (new lines appended if different);
      everything else stays as authored. Row is reported 'updated' if notes
      changed, otherwise 'skipped'.
    """
    by_key: dict[tuple[str, str, str], MappingEntry] = {_key(e): e for e in existing}
    order: list[tuple[str, str, str]] = [_key(e) for e in existing]
    report = MergeReport()

    for n in new:
        k = _key(n)
        if k in by_key:
            prev = by_key[k]
            if n.notes and n.notes != prev.notes and n.notes not in (prev.notes or ""):
                merged_notes = prev.notes
                if merged_notes:
                    merged_notes = merged_notes + " | " + n.notes
                else:
                    merged_notes = n.notes
                by_key[k] = MappingEntry(
                    source_system=prev.source_system,
                    source_entity=prev.source_entity,
                    source_field=prev.source_field,
                    canonical_concept=prev.canonical_concept,
                    canonical_property=prev.canonical_property,
                    mapping_type=prev.mapping_type,
                    confidence=prev.confidence,
                    notes=merged_notes,
                )
                report.updated.append(_pretty(prev))
            else:
                report.skipped.append(_pretty(prev))
        else:
            by_key[k] = n
            order.append(k)
            report.added.append(_pretty(n))

    return [by_key[k] for k in order], report


# ---------------------------------------------------------------------------
# CSV writer
# ---------------------------------------------------------------------------

def write_mappings_csv(entries: list[MappingEntry], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMN_ORDER, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for e in entries:
            writer.writerow({
                "source_system": e.source_system,
                "source_entity": e.source_entity,
                "source_field": e.source_field,
                "canonical_concept": e.canonical_concept,
                "canonical_property": e.canonical_property,
                "mapping_type": e.mapping_type,
                "confidence": e.confidence,
                "notes": e.notes,
            })


# ---------------------------------------------------------------------------
# Warnings labels
# ---------------------------------------------------------------------------

MAPPINGS_WARNING_LABELS: dict[str, str] = {
    "unknown_canonical_concept": "Mappings pointing at unknown canonical concepts",
    "low_confidence_without_notes": "Low-confidence mappings without explanatory notes",
    "ambiguous_without_notes": "Ambiguous/unmapped rows without explanatory notes",
}

MAPPINGS_WARNING_ORDER: list[str] = [
    "unknown_canonical_concept",
    "low_confidence_without_notes",
    "ambiguous_without_notes",
]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

@dataclass
class IngestResult:
    merged_count: int
    added: list[str]
    updated: list[str]
    skipped: list[str]
    warnings: list[LintWarning]
    output_path: str
    warnings_path: str


def ingest_mappings(
    workspace_path: str,
    fixture_path: str,
    session: str,
    interviewer: str,
    at: datetime | None = None,
) -> IngestResult:
    if at is None:
        at = datetime.now(timezone.utc)

    if not os.path.isfile(fixture_path):
        raise FileNotFoundError(f"ingest source not found: {fixture_path}")

    with open(fixture_path, newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        rows = list(reader)

    new_entries = parse_mapping_rows(header, rows)

    target_path = os.path.join(workspace_path, "03_mappings", "source-to-canonical.csv")
    existing = load_mappings_csv(target_path)

    known_concepts = {c.name for c in load_concepts_yaml(
        os.path.join(workspace_path, "02_concepts", "candidate-concepts.yaml")
    )}

    warnings = run_lints(new_entries, known_concepts)

    merged, report = merge_mappings(existing, new_entries)

    write_mappings_csv(merged, target_path)

    warnings_path = os.path.join(workspace_path, "ingest-warnings.md")
    write_warnings_file(
        warnings,
        warnings_path,
        session=session,
        interviewer=interviewer,
        at=at,
        item_kind="mapping",
        rule_labels=MAPPINGS_WARNING_LABELS,
        rule_order=MAPPINGS_WARNING_ORDER,
    )

    return IngestResult(
        merged_count=len(merged),
        added=report.added,
        updated=report.updated,
        skipped=report.skipped,
        warnings=warnings,
        output_path=target_path,
        warnings_path=warnings_path,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _print_summary(result: IngestResult, root: str) -> None:
    print(f"Ingested mappings into {os.path.relpath(result.output_path, root)}")
    print(f"  Added:   {len(result.added)}")
    if result.added:
        for m in result.added:
            print(f"    + {m}")
    print(f"  Updated: {len(result.updated)}  [notes union only]")
    print(f"  Skipped: {len(result.skipped)}  (existing mappings — curated content protected)")
    print(f"  Total:   {result.merged_count} mapping(s) in workspace")
    print("")
    if not result.warnings:
        print("Lint: clean — no warnings.")
    else:
        print(f"Lint: {len(result.warnings)} warning(s) — see {os.path.relpath(result.warnings_path, root)}")


def main() -> None:
    run_ingest_cli(
        prog="gnosis ingest mappings",
        description="Ingest LLM-extracted source-to-canonical mappings into 03_mappings/source-to-canonical.csv.",
        source_help="Path to the LLM-output CSV file.",
        ingest_fn=ingest_mappings,
        print_summary=_print_summary,
        schema_error_header="Ingest refused — schema errors in source CSV:",
    )


if __name__ == "__main__":
    main()
