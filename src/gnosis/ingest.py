"""Ingest LLM-extracted YAML into a gnosis workspace.

The consultant runs a skill (e.g. `skills/gnosis/extracting-concepts-from-transcripts.md`)
against their LLM of choice, saves the YAML output to a file, and then runs
`gnosis ingest concepts --from <file>`.

This module is responsible for:
  1. Strict schema validation (hard-fail on missing required fields / bad types)
  2. Semantic lint (unknown speakers, dangling relationships, etc.) — non-blocking
  3. Merge into existing candidate-concepts.yaml with last_ingested provenance
  4. Regenerating ontology/ingest-warnings.md

BYOLLM by design — no LLM is called from here. Input is YAML the user already
has in their hands.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone


ALLOWED_CONFIDENCE = {"high", "medium", "low"}


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

@dataclass
class SourceQuote:
    quote: str
    source: str
    date: str  # ISO date string (YYYY-MM-DD)


@dataclass
class ConceptEntry:
    name: str
    domain: str
    description: str
    source_quotes: list[SourceQuote]
    related_to: list[str] = field(default_factory=list)
    confidence: str | None = None
    open_questions: list[str] = field(default_factory=list)
    last_ingested: dict | None = None


class SchemaError(Exception):
    """Raised when the input YAML violates the ConceptEntry schema.

    Carries a list of human-readable issues collected across all entries so
    the caller can show them all at once rather than one-at-a-time.
    """

    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__(f"{len(issues)} schema issue(s)")


def parse_concepts(raw: list) -> list[ConceptEntry]:
    """Convert a list of dicts into validated ConceptEntry objects.

    Raises SchemaError with all collected issues if anything fails.
    """
    if not isinstance(raw, list):
        raise SchemaError(["Top-level YAML must be a list of concept entries"])

    issues: list[str] = []
    entries: list[ConceptEntry] = []

    for i, item in enumerate(raw):
        label = f"entry[{i}]"
        if not isinstance(item, dict):
            issues.append(f"{label}: must be a mapping, got {type(item).__name__}")
            continue

        name = item.get("name")
        if name:
            label = f"concept '{name}'"

        local_issues: list[str] = []

        if not isinstance(name, str) or not name.strip():
            local_issues.append(f"{label}: 'name' is required and must be a non-empty string")
        elif not re.match(r"^[A-Z][A-Za-z0-9]*$", name.strip()):
            local_issues.append(
                f"{label}: 'name' must be PascalCase (start with uppercase, no spaces/hyphens)"
            )

        domain = item.get("domain")
        if not isinstance(domain, str) or not domain.strip():
            local_issues.append(f"{label}: 'domain' is required and must be a non-empty string")

        description = item.get("description")
        if not isinstance(description, str) or len(description.strip()) < 20:
            local_issues.append(
                f"{label}: 'description' is required and must be at least 20 characters"
            )

        source_quotes_raw = item.get("source_quotes")
        source_quotes: list[SourceQuote] = []
        if not isinstance(source_quotes_raw, list) or not source_quotes_raw:
            local_issues.append(f"{label}: 'source_quotes' is required and must be a non-empty list")
        else:
            for j, sq in enumerate(source_quotes_raw):
                sq_label = f"{label} source_quotes[{j}]"
                if not isinstance(sq, dict):
                    local_issues.append(f"{sq_label}: must be a mapping")
                    continue
                quote = sq.get("quote")
                source = sq.get("source")
                sq_date = sq.get("date")
                if not isinstance(quote, str) or not quote.strip():
                    local_issues.append(f"{sq_label}: 'quote' is required and must be a non-empty string")
                if not isinstance(source, str) or not source.strip():
                    local_issues.append(f"{sq_label}: 'source' is required and must be a non-empty string")
                # PyYAML parses unquoted YAML dates (YYYY-MM-DD) to datetime.date objects.
                # Accept either an ISO-format string or a date object and normalise.
                if isinstance(sq_date, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", sq_date.strip()):
                    sq_date_str = sq_date.strip()
                elif hasattr(sq_date, "isoformat"):
                    sq_date_str = sq_date.isoformat()
                else:
                    local_issues.append(f"{sq_label}: 'date' is required and must be ISO format (YYYY-MM-DD)")
                    continue
                if isinstance(quote, str) and isinstance(source, str):
                    source_quotes.append(SourceQuote(quote=quote.strip(), source=source.strip(), date=sq_date_str))

        related_to_raw = item.get("related_to", [])
        related_to: list[str] = []
        if related_to_raw is None:
            related_to = []
        elif isinstance(related_to_raw, list):
            for r in related_to_raw:
                if not isinstance(r, str) or not r.strip():
                    local_issues.append(f"{label}: 'related_to' entries must be non-empty strings")
                else:
                    related_to.append(r.strip())
        else:
            local_issues.append(f"{label}: 'related_to' must be a list of strings")

        confidence = item.get("confidence")
        if confidence is not None:
            if not isinstance(confidence, str) or confidence.strip().lower() not in ALLOWED_CONFIDENCE:
                local_issues.append(
                    f"{label}: 'confidence' must be one of {sorted(ALLOWED_CONFIDENCE)}"
                )
            else:
                confidence = confidence.strip().lower()

        open_questions_raw = item.get("open_questions", [])
        open_questions: list[str] = []
        if open_questions_raw is None:
            open_questions = []
        elif isinstance(open_questions_raw, list):
            for q in open_questions_raw:
                if not isinstance(q, str) or not q.strip():
                    local_issues.append(f"{label}: 'open_questions' entries must be non-empty strings")
                else:
                    open_questions.append(q.strip())
        else:
            local_issues.append(f"{label}: 'open_questions' must be a list of strings")

        if local_issues:
            issues.extend(local_issues)
            continue

        entries.append(
            ConceptEntry(
                name=name.strip(),
                domain=domain.strip(),
                description=description.strip(),
                source_quotes=source_quotes,
                related_to=related_to,
                confidence=confidence,
                open_questions=open_questions,
                last_ingested=item.get("last_ingested"),
            )
        )

    if issues:
        raise SchemaError(issues)

    return entries


def load_concepts_yaml(path: str) -> list[ConceptEntry]:
    """Load and validate a concepts YAML file. Returns [] if file is missing.

    Raises SchemaError if the file exists but fails validation.
    """
    if not os.path.isfile(path):
        return []
    import yaml
    with open(path) as f:
        raw = yaml.safe_load(f) or []
    return parse_concepts(raw)


# ---------------------------------------------------------------------------
# Stakeholder speaker resolution
# ---------------------------------------------------------------------------

def _normalise_name(raw: str) -> str:
    """Normalise a human name for comparison.

    - Strip parenthetical suffixes: 'Alice Chen (Head of X)' → 'Alice Chen'
    - Case-fold and collapse internal whitespace.
    """
    without_paren = re.sub(r"\s*\([^)]*\)\s*", "", raw).strip()
    return re.sub(r"\s+", " ", without_paren).casefold()


def load_stakeholder_names(stakeholders_path: str) -> set[str]:
    """Return a set of normalised stakeholder names from 00_scope/stakeholders.yaml.

    Accepts either a top-level list or a mapping with a 'stakeholders' key.
    Returns an empty set if the file is missing.
    """
    if not os.path.isfile(stakeholders_path):
        return set()
    import yaml
    with open(stakeholders_path) as f:
        data = yaml.safe_load(f) or []
    if isinstance(data, dict):
        data = data.get("stakeholders", [])
    names: set[str] = set()
    for item in data:
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name.strip() and name.strip().upper() != "TBD":
                names.add(_normalise_name(name))
    return names


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LintWarning:
    rule: str
    concept: str
    message: str


def lint_unknown_speakers(
    concepts: list[ConceptEntry], known_speakers: set[str]
) -> list[LintWarning]:
    """Flag source_quote speakers that don't resolve to a stakeholder."""
    warnings: list[LintWarning] = []
    for c in concepts:
        for sq in c.source_quotes:
            if _normalise_name(sq.source) not in known_speakers:
                warnings.append(
                    LintWarning(
                        rule="unknown_speaker",
                        concept=c.name,
                        message=(
                            f"quote attributed to \"{sq.source}\" has no matching stakeholder "
                            "in 00_scope/stakeholders.yaml"
                        ),
                    )
                )
    return warnings


def lint_dangling_related_to(
    concepts: list[ConceptEntry], known_concept_names: set[str]
) -> list[LintWarning]:
    """Flag related_to references that don't resolve to a known concept.

    known_concept_names should be the union of existing + newly-ingested concept names.
    """
    names_normalised = {n.casefold() for n in known_concept_names}
    warnings: list[LintWarning] = []
    for c in concepts:
        for rel in c.related_to:
            if rel.casefold() not in names_normalised:
                warnings.append(
                    LintWarning(
                        rule="dangling_related_to",
                        concept=c.name,
                        message=f"related_to → '{rel}' is not a known concept",
                    )
                )
    return warnings


def lint_low_confidence_missing_questions(
    concepts: list[ConceptEntry],
) -> list[LintWarning]:
    """Flag concepts with confidence=low that have no open_questions."""
    warnings: list[LintWarning] = []
    for c in concepts:
        if c.confidence == "low" and not c.open_questions:
            warnings.append(
                LintWarning(
                    rule="low_confidence_missing_questions",
                    concept=c.name,
                    message=(
                        "confidence=low but open_questions is empty — low-confidence "
                        "entries should document the uncertainty"
                    ),
                )
            )
    return warnings


def run_lints(
    new_concepts: list[ConceptEntry],
    existing_concepts: list[ConceptEntry],
    known_speakers: set[str],
) -> list[LintWarning]:
    """Run all lint rules against the newly-ingested concepts.

    Dangling related_to is checked against the union of existing + new concept
    names so cross-references within a single batch resolve.
    """
    all_names = {c.name for c in existing_concepts} | {c.name for c in new_concepts}
    warnings: list[LintWarning] = []
    warnings.extend(lint_unknown_speakers(new_concepts, known_speakers))
    warnings.extend(lint_dangling_related_to(new_concepts, all_names))
    warnings.extend(lint_low_confidence_missing_questions(new_concepts))
    return warnings


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

@dataclass
class MergeReport:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)


def merge_concepts(
    existing: list[ConceptEntry],
    new: list[ConceptEntry],
    session: str,
    interviewer: str,
    at: datetime,
) -> tuple[list[ConceptEntry], MergeReport]:
    """Merge new concepts into existing, keyed by case-insensitive name.

    - New concept: appended.
    - Existing concept: description/domain/confidence overwritten from new;
      source_quotes/related_to/open_questions unioned (dedup preserves order
      of existing then new).
    - last_ingested provenance is stamped on every touched entry.
    """
    from gnosis._common import make_provenance

    by_key: dict[str, ConceptEntry] = {c.name.casefold(): c for c in existing}
    order: list[str] = [c.name.casefold() for c in existing]
    report = MergeReport()

    provenance = make_provenance(session, interviewer, at)

    for n in new:
        key = n.name.casefold()
        if key in by_key:
            prev = by_key[key]
            merged_quotes = list(prev.source_quotes)
            seen_quotes = {(sq.quote, sq.source) for sq in merged_quotes}
            for sq in n.source_quotes:
                if (sq.quote, sq.source) not in seen_quotes:
                    merged_quotes.append(sq)
                    seen_quotes.add((sq.quote, sq.source))

            merged_related = list(prev.related_to)
            seen_rel = {r.casefold() for r in merged_related}
            for r in n.related_to:
                if r.casefold() not in seen_rel:
                    merged_related.append(r)
                    seen_rel.add(r.casefold())

            merged_questions = list(prev.open_questions)
            seen_q = {q.casefold() for q in merged_questions}
            for q in n.open_questions:
                if q.casefold() not in seen_q:
                    merged_questions.append(q)
                    seen_q.add(q.casefold())

            by_key[key] = ConceptEntry(
                name=prev.name,
                domain=n.domain,
                description=n.description,
                source_quotes=merged_quotes,
                related_to=merged_related,
                confidence=n.confidence if n.confidence is not None else prev.confidence,
                open_questions=merged_questions,
                last_ingested=provenance,
            )
            report.updated.append(prev.name)
        else:
            by_key[key] = ConceptEntry(
                name=n.name,
                domain=n.domain,
                description=n.description,
                source_quotes=n.source_quotes,
                related_to=n.related_to,
                confidence=n.confidence,
                open_questions=n.open_questions,
                last_ingested=provenance,
            )
            order.append(key)
            report.added.append(n.name)

    return [by_key[k] for k in order], report


# ---------------------------------------------------------------------------
# YAML writer
# ---------------------------------------------------------------------------

def write_concepts_yaml(concepts: list[ConceptEntry], path: str) -> None:
    """Serialise concepts to YAML. Stable field order, block style, wide width."""
    from gnosis._common import write_yaml_list

    def to_dict(c: ConceptEntry) -> dict:
        d: dict = {
            "name": c.name,
            "domain": c.domain,
            "description": c.description,
        }
        if c.related_to:
            d["related_to"] = list(c.related_to)
        d["source_quotes"] = [
            {"quote": sq.quote, "source": sq.source, "date": sq.date}
            for sq in c.source_quotes
        ]
        if c.confidence is not None:
            d["confidence"] = c.confidence
        if c.open_questions:
            d["open_questions"] = list(c.open_questions)
        if c.last_ingested is not None:
            d["last_ingested"] = dict(c.last_ingested)
        return d

    write_yaml_list([to_dict(c) for c in concepts], path)


# ---------------------------------------------------------------------------
# Warnings file
# ---------------------------------------------------------------------------

DEFAULT_WARNING_RULE_LABELS: dict[str, str] = {
    "unknown_speaker": "Unknown speakers",
    "dangling_related_to": "Dangling related_to references",
    "low_confidence_missing_questions": "Low-confidence entries missing open_questions",
}

DEFAULT_WARNING_RULE_ORDER: list[str] = [
    "unknown_speaker",
    "dangling_related_to",
    "low_confidence_missing_questions",
]


def write_warnings_file(
    warnings: list[LintWarning],
    path: str,
    session: str,
    interviewer: str,
    at: datetime,
    item_kind: str = "concept",
    rule_labels: dict[str, str] | None = None,
    rule_order: list[str] | None = None,
) -> None:
    """(Re)generate ontology/ingest-warnings.md from the current warnings list.

    File is overwritten each ingest. item_kind is the noun shown in totals
    ("concept", "stakeholder", etc.). rule_labels/rule_order let callers extend
    the section headings and ordering for their own lint rule set; unknown
    rules still render with their rule name.
    """
    if rule_labels is None:
        rule_labels = DEFAULT_WARNING_RULE_LABELS
    if rule_order is None:
        rule_order = DEFAULT_WARNING_RULE_ORDER

    os.makedirs(os.path.dirname(path), exist_ok=True)
    timestamp = at.strftime("%Y-%m-%d %H:%M")

    lines: list[str] = []
    lines.append("# Ingest warnings")
    lines.append("")
    lines.append(
        f"*Last ingest: {timestamp} by {interviewer} (session: `{session}`)*"
    )
    lines.append("")
    lines.append(
        "Generated by `gnosis ingest`. Non-blocking — fix by editing the "
        "workspace or re-ingesting a corrected fixture."
    )
    lines.append("")

    if not warnings:
        lines.append(f"No warnings — all ingested {item_kind}s passed lint.")
        lines.append("")
        with open(path, "w") as f:
            f.write("\n".join(lines))
        return

    by_rule: dict[str, list[LintWarning]] = {}
    for w in warnings:
        by_rule.setdefault(w.rule, []).append(w)

    affected_items: set[str] = {w.concept for w in warnings}

    for rule in rule_order:
        group = by_rule.get(rule, [])
        if not group:
            continue
        label = rule_labels.get(rule, rule)
        lines.append(f"## {label} ({len(group)})")
        lines.append("")
        for w in sorted(group, key=lambda x: (x.concept.casefold(), x.message)):
            lines.append(f"- **{w.concept}** — {w.message}")
        lines.append("")

    for rule in sorted(set(by_rule) - set(rule_order)):
        group = by_rule[rule]
        label = rule_labels.get(rule, rule)
        lines.append(f"## {label} ({len(group)})")
        lines.append("")
        for w in sorted(group, key=lambda x: (x.concept.casefold(), x.message)):
            lines.append(f"- **{w.concept}** — {w.message}")
        lines.append("")

    lines.append(
        f"*Total: {len(warnings)} warning(s) across {len(affected_items)} {item_kind}(s).*"
    )
    lines.append("")

    with open(path, "w") as f:
        f.write("\n".join(lines))


def count_warnings(warnings_path: str) -> int:
    """Quickly count warnings in an existing ingest-warnings.md.

    Parses the total footer line; returns 0 if file missing or clean.
    """
    if not os.path.isfile(warnings_path):
        return 0
    with open(warnings_path) as f:
        content = f.read()
    m = re.search(r"Total:\s*(\d+)\s*warning", content)
    if m:
        return int(m.group(1))
    return 0


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

@dataclass
class IngestResult:
    merged_count: int
    added: list[str]
    updated: list[str]
    warnings: list[LintWarning]
    output_path: str
    warnings_path: str


def ingest_concepts(
    workspace_path: str,
    fixture_path: str,
    session: str,
    interviewer: str,
    at: datetime | None = None,
) -> IngestResult:
    """Orchestrate the concepts ingest: schema-check, lint, merge, write.

    Raises SchemaError on hard schema failure (nothing is written).
    Always writes the warnings file, even on a clean run.
    """
    if at is None:
        at = datetime.now(timezone.utc)

    if not os.path.isfile(fixture_path):
        raise FileNotFoundError(f"ingest source not found: {fixture_path}")

    import yaml
    with open(fixture_path) as f:
        raw = yaml.safe_load(f) or []

    new_concepts = parse_concepts(raw)

    existing_path = os.path.join(workspace_path, "02_concepts", "candidate-concepts.yaml")
    existing_concepts = load_concepts_yaml(existing_path)

    stakeholders_path = os.path.join(workspace_path, "00_scope", "stakeholders.yaml")
    known_speakers = load_stakeholder_names(stakeholders_path)

    warnings = run_lints(new_concepts, existing_concepts, known_speakers)

    merged, report = merge_concepts(
        existing_concepts, new_concepts, session=session, interviewer=interviewer, at=at
    )

    write_concepts_yaml(merged, existing_path)

    warnings_path = os.path.join(workspace_path, "ingest-warnings.md")
    write_warnings_file(warnings, warnings_path, session=session, interviewer=interviewer, at=at)

    return IngestResult(
        merged_count=len(merged),
        added=report.added,
        updated=report.updated,
        warnings=warnings,
        output_path=existing_path,
        warnings_path=warnings_path,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _print_summary(result: IngestResult, root: str) -> None:
    print(f"Ingested concepts into {os.path.relpath(result.output_path, root)}")
    print(f"  Added:   {len(result.added)}  ({', '.join(result.added) if result.added else '—'})")
    print(f"  Updated: {len(result.updated)}  ({', '.join(result.updated) if result.updated else '—'})")
    print(f"  Total:   {result.merged_count} concept(s) in workspace")
    print("")
    if not result.warnings:
        print("Lint: clean — no warnings.")
    else:
        print(f"Lint: {len(result.warnings)} warning(s) — see {os.path.relpath(result.warnings_path, root)}")


def main() -> None:
    from gnosis._common import run_ingest_cli

    run_ingest_cli(
        prog="gnosis ingest concepts",
        description="Ingest LLM-extracted candidate-concepts YAML into 02_concepts/candidate-concepts.yaml.",
        source_help="Path to the LLM-output YAML file.",
        ingest_fn=ingest_concepts,
        print_summary=_print_summary,
        schema_error_header="Ingest refused — schema errors in source YAML:",
    )


if __name__ == "__main__":
    main()
