"""Ingest LLM-extracted terminology conflicts into 01_language/synonym-conflicts.{yaml,md}.

Matches the output format of `skills/gnosis/detecting-terminology-synonyms.md`
(YAML-as-input contract; gnosis renders the markdown view for humans and the
downstream `terminology_conflict_report` generator).

Canonical source of truth: `01_language/synonym-conflicts.yaml` (merged across
ingests). Rendered view: `01_language/synonym-conflicts.md` — always regenerated
from the YAML, never hand-edited post-ingest.

First-ingest grace: if a hand-authored `synonym-conflicts.md` exists without a
`.yaml` peer, it is renamed to `synonym-conflicts.md.pre-ingest` (once, non-
destructive) so the user's prior work is preserved.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from gnosis._common import make_provenance, run_ingest_cli, write_yaml_list
from gnosis.ingest import (
    LintWarning,
    SchemaError,
    _normalise_name,
    load_stakeholder_names,
    write_warnings_file,
)
from gnosis.ingest_glossary import source_speaker_candidate

ALLOWED_TYPES = {"synonym", "near-synonym", "homonym"}
ALLOWED_SEVERITY = {"high", "medium", "low"}
ALLOWED_POLARITY = {"same", "different"}


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

@dataclass
class EvidenceQuote:
    quote: str
    source: str
    date: str
    polarity: str  # same | different


@dataclass
class UsedByEntry:
    term: str
    speakers: list[str] = field(default_factory=list)


@dataclass
class ConflictEntry:
    title: str
    type: str
    severity: str
    terms: list[str]
    used_by: list[UsedByEntry] = field(default_factory=list)
    evidence: list[EvidenceQuote] = field(default_factory=list)
    proposed_canonical: str | None = None
    rationale: str | None = None
    open_questions: list[str] = field(default_factory=list)
    last_ingested: dict | None = None


def _coerce_str_list(value, label: str, issues: list[str]) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        issues.append(f"{label}: must be a list of strings")
        return []
    out: list[str] = []
    for v in value:
        if not isinstance(v, str) or not v.strip():
            issues.append(f"{label}: entries must be non-empty strings")
        else:
            out.append(v.strip())
    return out


def parse_conflicts(raw: list) -> list[ConflictEntry]:
    if not isinstance(raw, list):
        raise SchemaError(["Top-level YAML must be a list of conflict entries"])

    issues: list[str] = []
    entries: list[ConflictEntry] = []
    seen_titles: set[str] = set()

    for i, item in enumerate(raw):
        label = f"entry[{i}]"
        if not isinstance(item, dict):
            issues.append(f"{label}: must be a mapping, got {type(item).__name__}")
            continue

        title = item.get("title")
        if title:
            label = f"conflict '{title}'"

        local: list[str] = []

        if not isinstance(title, str) or not title.strip():
            local.append(f"{label}: 'title' is required and must be a non-empty string")

        key = (title or "").strip().casefold()
        if title and key in seen_titles:
            local.append(f"{label}: duplicate title within the same ingest")
        seen_titles.add(key)

        ctype = item.get("type")
        if not isinstance(ctype, str) or ctype.strip().lower() not in ALLOWED_TYPES:
            local.append(f"{label}: 'type' must be one of {sorted(ALLOWED_TYPES)}")
        else:
            ctype = ctype.strip().lower()

        severity = item.get("severity")
        if not isinstance(severity, str) or severity.strip().lower() not in ALLOWED_SEVERITY:
            local.append(f"{label}: 'severity' must be one of {sorted(ALLOWED_SEVERITY)}")
        else:
            severity = severity.strip().lower()

        terms = _coerce_str_list(item.get("terms"), f"{label} terms", local)
        if len(terms) < 1:
            local.append(f"{label}: 'terms' must list at least one term")

        used_by_raw = item.get("used_by", [])
        used_by: list[UsedByEntry] = []
        if used_by_raw is None:
            used_by_raw = []
        if not isinstance(used_by_raw, list):
            local.append(f"{label}: 'used_by' must be a list")
        else:
            for j, u in enumerate(used_by_raw):
                u_label = f"{label} used_by[{j}]"
                if not isinstance(u, dict):
                    local.append(f"{u_label}: must be a mapping")
                    continue
                u_term = u.get("term")
                if not isinstance(u_term, str) or not u_term.strip():
                    local.append(f"{u_label}: 'term' is required")
                    continue
                u_speakers = _coerce_str_list(u.get("speakers"), f"{u_label} speakers", local)
                used_by.append(UsedByEntry(term=u_term.strip(), speakers=u_speakers))

        evidence_raw = item.get("evidence", [])
        evidence: list[EvidenceQuote] = []
        if evidence_raw is None:
            evidence_raw = []
        if not isinstance(evidence_raw, list):
            local.append(f"{label}: 'evidence' must be a list")
        else:
            for j, q in enumerate(evidence_raw):
                q_label = f"{label} evidence[{j}]"
                if not isinstance(q, dict):
                    local.append(f"{q_label}: must be a mapping")
                    continue
                quote = q.get("quote")
                source = q.get("source")
                q_date = q.get("date")
                polarity = q.get("polarity")
                if not isinstance(quote, str) or not quote.strip():
                    local.append(f"{q_label}: 'quote' is required")
                if not isinstance(source, str) or not source.strip():
                    local.append(f"{q_label}: 'source' is required")
                if isinstance(q_date, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", q_date.strip()):
                    q_date_str = q_date.strip()
                elif hasattr(q_date, "isoformat"):
                    q_date_str = q_date.isoformat()
                else:
                    local.append(f"{q_label}: 'date' is required (YYYY-MM-DD)")
                    continue
                if not isinstance(polarity, str) or polarity.strip().lower() not in ALLOWED_POLARITY:
                    local.append(f"{q_label}: 'polarity' must be one of {sorted(ALLOWED_POLARITY)}")
                    continue
                if isinstance(quote, str) and isinstance(source, str):
                    evidence.append(EvidenceQuote(
                        quote=quote.strip(),
                        source=source.strip(),
                        date=q_date_str,
                        polarity=polarity.strip().lower(),
                    ))

        proposed = item.get("proposed_canonical")
        if proposed is not None and not isinstance(proposed, str):
            local.append(f"{label}: 'proposed_canonical' must be a string if provided")
        elif isinstance(proposed, str):
            proposed = proposed.strip() or None

        rationale = item.get("rationale")
        if rationale is not None and not isinstance(rationale, str):
            local.append(f"{label}: 'rationale' must be a string if provided")
        elif isinstance(rationale, str):
            rationale = rationale.strip() or None

        open_questions = _coerce_str_list(item.get("open_questions"), f"{label} open_questions", local)

        if local:
            issues.extend(local)
            continue

        entries.append(
            ConflictEntry(
                title=title.strip(),
                type=ctype,
                severity=severity,
                terms=terms,
                used_by=used_by,
                evidence=evidence,
                proposed_canonical=proposed,
                rationale=rationale,
                open_questions=open_questions,
                last_ingested=item.get("last_ingested"),
            )
        )

    if issues:
        raise SchemaError(issues)

    return entries


def load_conflicts_yaml(path: str) -> list[ConflictEntry]:
    if not os.path.isfile(path):
        return []
    import yaml
    with open(path) as f:
        raw = yaml.safe_load(f) or []
    return parse_conflicts(raw)


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------

def lint_insufficient_evidence(entries: list[ConflictEntry]) -> list[LintWarning]:
    """Flag conflicts with fewer than 2 evidence quotes from distinct sources."""
    warnings: list[LintWarning] = []
    for e in entries:
        distinct_sources = {q.source.casefold() for q in e.evidence}
        if len(distinct_sources) < 2:
            warnings.append(
                LintWarning(
                    rule="insufficient_evidence",
                    concept=e.title,
                    message=(
                        f"only {len(distinct_sources)} distinct source(s) in evidence — "
                        "terminology conflicts need at least 2 for cross-speaker corroboration"
                    ),
                )
            )
    return warnings


def lint_unknown_speaker_in_evidence(
    entries: list[ConflictEntry], known_speakers: set[str]
) -> list[LintWarning]:
    """Flag evidence quotes attributed to speakers not in stakeholders.yaml.

    Team/event-like sources (via the glossary source-speaker heuristic) are skipped
    so 'Sales Ops' or 'Platform Team' don't fire.
    """
    warnings: list[LintWarning] = []
    for e in entries:
        seen_unknown: set[str] = set()
        for q in e.evidence:
            candidate = source_speaker_candidate(q.source)
            # `source_speaker_candidate` expects date-prefixed or bare-name input;
            # synonym evidence uses bare name without a date prefix, which the
            # heuristic still handles correctly.
            if candidate is None:
                continue
            if _normalise_name(candidate) in known_speakers:
                continue
            if candidate in seen_unknown:
                continue
            seen_unknown.add(candidate)
            warnings.append(
                LintWarning(
                    rule="unknown_speaker_in_evidence",
                    concept=e.title,
                    message=(
                        f"evidence cites \"{candidate}\" but no matching stakeholder "
                        "in 00_scope/stakeholders.yaml"
                    ),
                )
            )
    return warnings


def lint_proposed_canonical_not_in_terms(entries: list[ConflictEntry]) -> list[LintWarning]:
    warnings: list[LintWarning] = []
    for e in entries:
        if not e.proposed_canonical:
            continue
        normalised_terms = {t.casefold() for t in e.terms}
        if e.proposed_canonical.casefold() not in normalised_terms:
            warnings.append(
                LintWarning(
                    rule="proposed_canonical_not_in_terms",
                    concept=e.title,
                    message=(
                        f"proposed_canonical '{e.proposed_canonical}' is not one of "
                        f"the listed terms {e.terms} — pick an existing term or add it"
                    ),
                )
            )
    return warnings


def run_lints(
    entries: list[ConflictEntry], known_speakers: set[str]
) -> list[LintWarning]:
    warnings: list[LintWarning] = []
    warnings.extend(lint_insufficient_evidence(entries))
    warnings.extend(lint_unknown_speaker_in_evidence(entries, known_speakers))
    warnings.extend(lint_proposed_canonical_not_in_terms(entries))
    return warnings


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

@dataclass
class MergeReport:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)


def merge_conflicts(
    existing: list[ConflictEntry],
    new: list[ConflictEntry],
    session: str,
    interviewer: str,
    at: datetime,
) -> tuple[list[ConflictEntry], MergeReport]:
    by_key: dict[str, ConflictEntry] = {e.title.casefold(): e for e in existing}
    order: list[str] = [e.title.casefold() for e in existing]
    report = MergeReport()

    provenance = make_provenance(session, interviewer, at)

    for n in new:
        key = n.title.casefold()
        if key in by_key:
            prev = by_key[key]

            # Union terms (case-insensitive)
            merged_terms = list(prev.terms)
            seen = {t.casefold() for t in merged_terms}
            for t in n.terms:
                if t.casefold() not in seen:
                    merged_terms.append(t)
                    seen.add(t.casefold())

            # Union evidence (dedup by quote text)
            merged_evidence = list(prev.evidence)
            seen_quotes = {(q.quote, q.source) for q in merged_evidence}
            for q in n.evidence:
                if (q.quote, q.source) not in seen_quotes:
                    merged_evidence.append(q)
                    seen_quotes.add((q.quote, q.source))

            # Union used_by by term (merging speakers within each term)
            used_by_index: dict[str, UsedByEntry] = {u.term.casefold(): u for u in prev.used_by}
            for u in n.used_by:
                k = u.term.casefold()
                if k in used_by_index:
                    existing_u = used_by_index[k]
                    seen_sp = {s.casefold() for s in existing_u.speakers}
                    merged_sp = list(existing_u.speakers)
                    for sp in u.speakers:
                        if sp.casefold() not in seen_sp:
                            merged_sp.append(sp)
                            seen_sp.add(sp.casefold())
                    used_by_index[k] = UsedByEntry(term=existing_u.term, speakers=merged_sp)
                else:
                    used_by_index[k] = u
            merged_used_by = list(used_by_index.values())

            # Union open_questions
            merged_q = list(prev.open_questions)
            seen_q = {q.casefold() for q in merged_q}
            for q in n.open_questions:
                if q.casefold() not in seen_q:
                    merged_q.append(q)
                    seen_q.add(q.casefold())

            by_key[key] = ConflictEntry(
                title=prev.title,
                type=n.type,
                severity=n.severity,
                terms=merged_terms,
                used_by=merged_used_by,
                evidence=merged_evidence,
                proposed_canonical=n.proposed_canonical if n.proposed_canonical is not None else prev.proposed_canonical,
                rationale=n.rationale if n.rationale is not None else prev.rationale,
                open_questions=merged_q,
                last_ingested=provenance,
            )
            report.updated.append(prev.title)
        else:
            by_key[key] = ConflictEntry(
                title=n.title,
                type=n.type,
                severity=n.severity,
                terms=n.terms,
                used_by=n.used_by,
                evidence=n.evidence,
                proposed_canonical=n.proposed_canonical,
                rationale=n.rationale,
                open_questions=n.open_questions,
                last_ingested=provenance,
            )
            order.append(key)
            report.added.append(n.title)

    return [by_key[k] for k in order], report


# ---------------------------------------------------------------------------
# YAML writer
# ---------------------------------------------------------------------------

def write_conflicts_yaml(entries: list[ConflictEntry], path: str) -> None:
    def evidence_to_dict(q: EvidenceQuote) -> dict:
        return {"quote": q.quote, "source": q.source, "date": q.date, "polarity": q.polarity}

    def used_by_to_dict(u: UsedByEntry) -> dict:
        return {"term": u.term, "speakers": list(u.speakers)}

    def to_dict(e: ConflictEntry) -> dict:
        d: dict = {
            "title": e.title,
            "type": e.type,
            "severity": e.severity,
            "terms": list(e.terms),
        }
        if e.used_by:
            d["used_by"] = [used_by_to_dict(u) for u in e.used_by]
        if e.evidence:
            d["evidence"] = [evidence_to_dict(q) for q in e.evidence]
        if e.proposed_canonical is not None:
            d["proposed_canonical"] = e.proposed_canonical
        if e.rationale is not None:
            d["rationale"] = e.rationale
        if e.open_questions:
            d["open_questions"] = list(e.open_questions)
        if e.last_ingested is not None:
            d["last_ingested"] = dict(e.last_ingested)
        return d

    write_yaml_list([to_dict(e) for e in entries], path)


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

_TYPE_HEADING_PREFIX = {
    "synonym": "Synonym",
    "near-synonym": "Near-synonym",
    "homonym": "Homonym",
}


def render_conflicts_markdown(entries: list[ConflictEntry]) -> str:
    lines: list[str] = []
    lines.append("# Terminology synonyms and conflicts")
    lines.append("")
    lines.append(
        "*Auto-generated from `01_language/synonym-conflicts.yaml` by `gnosis ingest synonyms`. "
        "Do not hand-edit — edit the YAML (or re-ingest) and this file will be regenerated.*"
    )
    lines.append("")

    if not entries:
        lines.append("*No conflicts recorded yet.*")
        lines.append("")
        return "\n".join(lines)

    for e in entries:
        prefix = _TYPE_HEADING_PREFIX.get(e.type, e.type.title())
        lines.append(f"## {prefix}: {e.title}")
        lines.append("")
        lines.append(f"- **Terms used:** {', '.join(e.terms)}")
        if e.used_by:
            lines.append("- **Used by:**")
            for u in e.used_by:
                speaker_list = ", ".join(u.speakers) if u.speakers else "(no speakers recorded)"
                lines.append(f'  - "{u.term}" — {speaker_list}')

        same = [q for q in e.evidence if q.polarity == "same"]
        diff = [q for q in e.evidence if q.polarity == "different"]
        if same:
            lines.append("- **Evidence of same meaning:**")
            for q in same:
                lines.append(f'  - {q.source} ({q.date}): "{q.quote}"')
        if diff:
            lines.append("- **Evidence of different meaning:**")
            for q in diff:
                lines.append(f'  - {q.source} ({q.date}): "{q.quote}"')

        lines.append(f"- **Type:** {e.type}")
        lines.append(f"- **Severity:** {e.severity}")
        if e.proposed_canonical:
            rationale = f" — {e.rationale}" if e.rationale else ""
            lines.append(f"- **Proposed canonical:** {e.proposed_canonical}{rationale}")
        elif e.rationale:
            lines.append(f"- **Rationale:** {e.rationale}")
        if e.open_questions:
            lines.append("- **Open questions:**")
            for q in e.open_questions:
                lines.append(f"  - {q}")
        lines.append("")

    return "\n".join(lines)


def write_conflicts_markdown(entries: list[ConflictEntry], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(render_conflicts_markdown(entries))


# ---------------------------------------------------------------------------
# Pre-ingest backup
# ---------------------------------------------------------------------------

def backup_pre_ingest_md(md_path: str, yaml_path: str) -> str | None:
    """If .md exists and .yaml does not, rename .md to .md.pre-ingest and return new path.

    Idempotent: if .md.pre-ingest already exists, do nothing and return None.
    """
    if os.path.isfile(yaml_path):
        return None
    if not os.path.isfile(md_path):
        return None
    backup_path = md_path + ".pre-ingest"
    if os.path.isfile(backup_path):
        return None
    os.rename(md_path, backup_path)
    return backup_path


# ---------------------------------------------------------------------------
# Warnings labels
# ---------------------------------------------------------------------------

SYNONYMS_WARNING_LABELS: dict[str, str] = {
    "insufficient_evidence": "Conflicts with insufficient evidence (<2 distinct sources)",
    "unknown_speaker_in_evidence": "Evidence citing unknown speakers",
    "proposed_canonical_not_in_terms": "Proposed canonical not among listed terms",
}

SYNONYMS_WARNING_ORDER: list[str] = [
    "insufficient_evidence",
    "unknown_speaker_in_evidence",
    "proposed_canonical_not_in_terms",
]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

@dataclass
class IngestResult:
    merged_count: int
    added: list[str]
    updated: list[str]
    warnings: list[LintWarning]
    yaml_path: str
    md_path: str
    backup_path: str | None
    warnings_path: str


def ingest_synonyms(
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

    import yaml
    with open(fixture_path) as f:
        raw = yaml.safe_load(f) or []

    new_entries = parse_conflicts(raw)

    yaml_path = os.path.join(workspace_path, "01_language", "synonym-conflicts.yaml")
    md_path = os.path.join(workspace_path, "01_language", "synonym-conflicts.md")

    backup_path = backup_pre_ingest_md(md_path, yaml_path)

    existing = load_conflicts_yaml(yaml_path)

    stakeholders_path = os.path.join(workspace_path, "00_scope", "stakeholders.yaml")
    known_speakers = load_stakeholder_names(stakeholders_path)

    warnings = run_lints(new_entries, known_speakers)

    merged, report = merge_conflicts(
        existing, new_entries, session=session, interviewer=interviewer, at=at
    )

    write_conflicts_yaml(merged, yaml_path)
    write_conflicts_markdown(merged, md_path)

    warnings_path = os.path.join(workspace_path, "ingest-warnings.md")
    write_warnings_file(
        warnings,
        warnings_path,
        session=session,
        interviewer=interviewer,
        at=at,
        item_kind="conflict",
        rule_labels=SYNONYMS_WARNING_LABELS,
        rule_order=SYNONYMS_WARNING_ORDER,
    )

    return IngestResult(
        merged_count=len(merged),
        added=report.added,
        updated=report.updated,
        warnings=warnings,
        yaml_path=yaml_path,
        md_path=md_path,
        backup_path=backup_path,
        warnings_path=warnings_path,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _print_summary(result: IngestResult, root: str) -> None:
    print(f"Ingested synonyms into {os.path.relpath(result.yaml_path, root)}")
    print(f"  Markdown rendered: {os.path.relpath(result.md_path, root)}")
    if result.backup_path:
        print(f"  Backed up pre-existing markdown: {os.path.relpath(result.backup_path, root)}")
    print(f"  Added:   {len(result.added)}  ({', '.join(result.added) if result.added else '—'})")
    print(f"  Updated: {len(result.updated)}  ({', '.join(result.updated) if result.updated else '—'})")
    print(f"  Total:   {result.merged_count} conflict(s) in workspace")
    print("")
    if not result.warnings:
        print("Lint: clean — no warnings.")
    else:
        print(f"Lint: {len(result.warnings)} warning(s) — see {os.path.relpath(result.warnings_path, root)}")


def main() -> None:
    run_ingest_cli(
        prog="gnosis ingest synonyms",
        description="Ingest LLM-extracted terminology-conflict YAML into 01_language/synonym-conflicts.{yaml,md}.",
        source_help="Path to the LLM-output YAML file.",
        ingest_fn=ingest_synonyms,
        print_summary=_print_summary,
    )


if __name__ == "__main__":
    main()
