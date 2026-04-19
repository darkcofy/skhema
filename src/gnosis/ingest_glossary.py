"""Ingest LLM-extracted glossary CSV into 01_language/glossary-seeds.csv.

Matches the output format of `skills/gnosis/extracting-glossary-terms.md`.
BYOLLM — input is CSV the user has in their hands.

Shape notes (vs concepts/stakeholders):

- Input/output is CSV, not YAML. The skill outputs CSV to match the human-editable
  target file.
- Per-row provenance lives inside the `source` column itself (the skill enforces
  "<date> <speaker>" format). No `last_ingested` sidecar for v1 — the `source`
  column IS the provenance.
- Merge is gentle: existing terms are *not* clobbered by a re-ingest. Only `aliases`
  are unioned across ingests (safe additive). Curated `definition` / `notes` / `domain`
  stay as authored. Re-ingest can add new terms but won't overwrite existing ones —
  if you want to revise an existing row, edit the CSV by hand.
"""
from __future__ import annotations

import csv
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from gnosis._common import run_ingest_cli
from gnosis.ingest import (
    LintWarning,
    SchemaError,
    _normalise_name,
    write_warnings_file,
)


REQUIRED_COLUMNS = {"term", "definition", "source"}
OPTIONAL_COLUMNS = {"domain", "aliases", "notes"}
ALLOWED_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS
COLUMN_ORDER = ["term", "definition", "source", "domain", "aliases", "notes"]


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

@dataclass
class GlossaryEntry:
    term: str
    definition: str  # may be empty if notes flags clarification
    source: str
    domain: str = ""
    aliases: list[str] = field(default_factory=list)
    notes: str = ""


def _split_aliases(raw: str) -> list[str]:
    if not raw:
        return []
    return [a.strip() for a in raw.split(",") if a.strip()]


def _join_aliases(aliases: list[str]) -> str:
    return ", ".join(aliases)


def parse_glossary_rows(header: list[str], rows: list[dict]) -> list[GlossaryEntry]:
    """Validate CSV header + rows and return GlossaryEntry objects.

    Header must contain all required columns and only known columns. Each row's
    `term` and `source` must be non-empty; empty `definition` is allowed (the
    skill permits it when `notes` flags a clarification). All collected issues
    are raised in a single SchemaError.
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

    entries: list[GlossaryEntry] = []
    seen_terms: set[str] = set()

    for i, row in enumerate(rows):
        local: list[str] = []
        label = f"row[{i}]"

        term = (row.get("term") or "").strip()
        if not term:
            local.append(f"{label}: 'term' is required and must be non-empty")
        else:
            label = f"term '{term}'"

        source = (row.get("source") or "").strip()
        if not source:
            local.append(f"{label}: 'source' is required and must be non-empty")

        # Detect duplicates within the same ingest — merges are by term, so
        # two rows for the same term in a single ingest is ambiguous input.
        key = term.casefold()
        if term and key in seen_terms:
            local.append(f"{label}: duplicate row for '{term}' in the same ingest")
        seen_terms.add(key)

        definition = (row.get("definition") or "").strip()
        domain = (row.get("domain") or "").strip()
        aliases = _split_aliases((row.get("aliases") or "").strip())
        notes = (row.get("notes") or "").strip()

        if local:
            issues.extend(local)
            continue

        entries.append(
            GlossaryEntry(
                term=term,
                definition=definition,
                source=source,
                domain=domain,
                aliases=aliases,
                notes=notes,
            )
        )

    if issues:
        raise SchemaError(issues)

    return entries


def load_glossary_csv(path: str) -> list[GlossaryEntry]:
    """Load a glossary CSV. Returns [] if missing; raises SchemaError if malformed."""
    if not os.path.isfile(path):
        return []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        rows = list(reader)
    return parse_glossary_rows(header, rows)


# ---------------------------------------------------------------------------
# Source speaker parsing
# ---------------------------------------------------------------------------

_DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}\s+(.+)$")

_NON_PERSON_TOKENS = {
    "team", "council", "board", "workshop", "kickoff", "meeting",
    "session", "chain", "ops", "group", "committee", "standup", "sync",
    "review", "retro", "retrospective", "interview", "deepdive", "deep-dive",
}


def source_speaker_candidate(source: str) -> str | None:
    """Extract a likely-person-name from a glossary `source` cell.

    Format expected: "YYYY-MM-DD <remainder>". If the remainder contains any
    team/event token (Team, Council, Workshop, Kickoff, Interview, etc.), we
    treat it as a non-person source and return None (lint does not fire on
    team-attributed rows).

    Otherwise, if the remainder is 1-4 capitalized words, we treat it as a
    person name and return the remainder.
    """
    m = _DATE_PREFIX.match(source.strip())
    remainder = m.group(1) if m else source.strip()

    if any(tok in remainder.lower().split() for tok in _NON_PERSON_TOKENS):
        return None

    words = remainder.split()
    if 1 <= len(words) <= 4 and all(w[:1].isupper() for w in words):
        return remainder
    return None


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------

_CLARIFICATION_TOKENS = re.compile(
    r"\b(clarif|unclear|TBD|unknown|needs?\s+(?:a\s+)?(?:definition|explanation|clarification))\b",
    re.IGNORECASE,
)


def lint_missing_definition_without_flag(
    entries: list[GlossaryEntry],
) -> list[LintWarning]:
    """Flag rows with empty definition AND no clarification-flag in notes."""
    warnings: list[LintWarning] = []
    for e in entries:
        if e.definition:
            continue
        if e.notes and _CLARIFICATION_TOKENS.search(e.notes):
            continue
        warnings.append(
            LintWarning(
                rule="missing_definition_without_flag",
                concept=e.term,
                message=(
                    "definition is empty but notes doesn't flag a reason — either "
                    "provide a definition or add a note like 'Needs clarification from <stakeholder>'"
                ),
            )
        )
    return warnings


def lint_unknown_speaker_in_source(
    entries: list[GlossaryEntry], known_speakers: set[str]
) -> list[LintWarning]:
    """Flag rows whose `source` looks like a person name but doesn't match a stakeholder.

    Non-person sources (e.g. 'Data Council kickoff', 'Platform Team') are skipped.
    """
    warnings: list[LintWarning] = []
    for e in entries:
        speaker = source_speaker_candidate(e.source)
        if speaker is None:
            continue
        if _normalise_name(speaker) not in known_speakers:
            warnings.append(
                LintWarning(
                    rule="unknown_speaker_in_source",
                    concept=e.term,
                    message=(
                        f"source cites \"{speaker}\" but no matching stakeholder exists in "
                        "00_scope/stakeholders.yaml"
                    ),
                )
            )
    return warnings


def run_lints(
    entries: list[GlossaryEntry], known_speakers: set[str]
) -> list[LintWarning]:
    warnings: list[LintWarning] = []
    warnings.extend(lint_missing_definition_without_flag(entries))
    warnings.extend(lint_unknown_speaker_in_source(entries, known_speakers))
    return warnings


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

@dataclass
class MergeReport:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def merge_glossary(
    existing: list[GlossaryEntry], new: list[GlossaryEntry]
) -> tuple[list[GlossaryEntry], MergeReport]:
    """Additive merge by normalised term.

    - New term → appended.
    - Existing term → aliases are unioned (additive); definition/source/domain/notes
      stay as authored. This protects curated content from noisy re-extractions.
      If the merge produced new aliases, the term is reported as 'updated';
      otherwise as 'skipped'.
    """
    by_key: dict[str, GlossaryEntry] = {e.term.casefold(): e for e in existing}
    order: list[str] = [e.term.casefold() for e in existing]
    report = MergeReport()

    for n in new:
        key = n.term.casefold()
        if key in by_key:
            prev = by_key[key]
            merged_aliases = list(prev.aliases)
            seen = {a.casefold() for a in merged_aliases}
            new_added = 0
            for a in n.aliases:
                if a.casefold() not in seen:
                    merged_aliases.append(a)
                    seen.add(a.casefold())
                    new_added += 1
            if new_added:
                by_key[key] = GlossaryEntry(
                    term=prev.term,
                    definition=prev.definition,
                    source=prev.source,
                    domain=prev.domain,
                    aliases=merged_aliases,
                    notes=prev.notes,
                )
                report.updated.append(prev.term)
            else:
                report.skipped.append(prev.term)
        else:
            by_key[key] = n
            order.append(key)
            report.added.append(n.term)

    return [by_key[k] for k in order], report


# ---------------------------------------------------------------------------
# CSV writer
# ---------------------------------------------------------------------------

def write_glossary_csv(entries: list[GlossaryEntry], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMN_ORDER, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for e in entries:
            writer.writerow({
                "term": e.term,
                "definition": e.definition,
                "source": e.source,
                "domain": e.domain,
                "aliases": _join_aliases(e.aliases),
                "notes": e.notes,
            })


# ---------------------------------------------------------------------------
# Warnings labels for this module
# ---------------------------------------------------------------------------

GLOSSARY_WARNING_LABELS: dict[str, str] = {
    "missing_definition_without_flag": "Missing definition without clarification flag",
    "unknown_speaker_in_source": "Unknown speaker cited in source",
}

GLOSSARY_WARNING_ORDER: list[str] = [
    "missing_definition_without_flag",
    "unknown_speaker_in_source",
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


def ingest_glossary(
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

    new_entries = parse_glossary_rows(header, rows)

    target_path = os.path.join(workspace_path, "01_language", "glossary-seeds.csv")
    existing = load_glossary_csv(target_path)

    stakeholders_path = os.path.join(workspace_path, "00_scope", "stakeholders.yaml")
    # Reuse the concepts-ingest helper — it lives in gnosis.ingest and is module-agnostic.
    from gnosis.ingest import load_stakeholder_names
    known_speakers = load_stakeholder_names(stakeholders_path)

    warnings = run_lints(new_entries, known_speakers)

    merged, report = merge_glossary(existing, new_entries)

    write_glossary_csv(merged, target_path)

    warnings_path = os.path.join(workspace_path, "ingest-warnings.md")
    write_warnings_file(
        warnings,
        warnings_path,
        session=session,
        interviewer=interviewer,
        at=at,
        item_kind="term",
        rule_labels=GLOSSARY_WARNING_LABELS,
        rule_order=GLOSSARY_WARNING_ORDER,
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
    print(f"Ingested glossary into {os.path.relpath(result.output_path, root)}")
    print(f"  Added:   {len(result.added)}  ({', '.join(result.added) if result.added else '—'})")
    print(f"  Updated: {len(result.updated)}  ({', '.join(result.updated) if result.updated else '—'})  [aliases only]")
    print(f"  Skipped: {len(result.skipped)}  (existing terms — curated definitions protected)")
    print(f"  Total:   {result.merged_count} term(s) in glossary")
    print("")
    if not result.warnings:
        print("Lint: clean — no warnings.")
    else:
        print(f"Lint: {len(result.warnings)} warning(s) — see {os.path.relpath(result.warnings_path, root)}")


def main() -> None:
    run_ingest_cli(
        prog="gnosis ingest glossary",
        description="Ingest LLM-extracted glossary CSV into 01_language/glossary-seeds.csv.",
        source_help="Path to the LLM-output CSV file.",
        ingest_fn=ingest_glossary,
        print_summary=_print_summary,
        schema_error_header="Ingest refused — schema errors in source CSV:",
    )


if __name__ == "__main__":
    main()
