"""Ingest LLM-extracted stakeholder YAML into 00_scope/stakeholders.yaml.

Matches the output format of `skills/gnosis/extracting-stakeholders.md`.
BYOLLM — input is YAML the user has in their hands.

Follows the same pattern as `gnosis.ingest` (concepts):
  1. Strict schema validation (hard-fail)
  2. Semantic lint (non-blocking) written to ontology/ingest-warnings.md
  3. Merge into stakeholders.yaml with last_ingested provenance

Named stakeholders are keyed by normalised name (case-fold, strip paren
suffixes). TBD placeholders are keyed on the (name, role, team) tuple so
multiple TBDs can coexist.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

from gnosis._common import make_provenance, run_ingest_cli, write_yaml_list
from gnosis.ingest import (
    LintWarning,
    SchemaError,
    _normalise_name,
    write_warnings_file,
)


ALLOWED_INFLUENCE = {"high", "medium", "low", "unknown"}


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

@dataclass
class StakeholderEntry:
    name: str
    role: str
    team: str | None = None
    email: str | None = None
    interests: list[str] = field(default_factory=list)
    decision_rights: list[str] = field(default_factory=list)
    influence: str | None = None
    engagement_cadence: str | None = None
    notes: str | None = None
    last_ingested: dict | None = None


def _is_tbd(name: str) -> bool:
    return name.strip().upper() == "TBD"


def parse_stakeholders(raw: list) -> list[StakeholderEntry]:
    """Validate a raw YAML list and return StakeholderEntry objects.

    Raises SchemaError with all collected issues if anything fails.
    """
    if not isinstance(raw, list):
        raise SchemaError(["Top-level YAML must be a list of stakeholder entries"])

    issues: list[str] = []
    entries: list[StakeholderEntry] = []

    for i, item in enumerate(raw):
        label = f"entry[{i}]"
        if not isinstance(item, dict):
            issues.append(f"{label}: must be a mapping, got {type(item).__name__}")
            continue

        name = item.get("name")
        if name:
            label = f"stakeholder '{name}'"

        local: list[str] = []

        if not isinstance(name, str) or not name.strip():
            local.append(f"{label}: 'name' is required and must be a non-empty string")

        role = item.get("role")
        if not isinstance(role, str) or not role.strip():
            local.append(f"{label}: 'role' is required and must be a non-empty string")

        team = item.get("team")
        if team is not None and (not isinstance(team, str) or not team.strip()):
            local.append(f"{label}: 'team' must be a non-empty string if provided")

        email = item.get("email")
        if email is not None and (not isinstance(email, str) or "@" not in email):
            local.append(f"{label}: 'email' must be a valid address if provided")

        interests = _coerce_str_list(item.get("interests"), f"{label} interests", local)
        decision_rights = _coerce_str_list(item.get("decision_rights"), f"{label} decision_rights", local)

        influence = item.get("influence")
        if influence is not None:
            if not isinstance(influence, str) or influence.strip().lower() not in ALLOWED_INFLUENCE:
                local.append(
                    f"{label}: 'influence' must be one of {sorted(ALLOWED_INFLUENCE)}"
                )
            else:
                influence = influence.strip().lower()

        cadence = item.get("engagement_cadence")
        if cadence is not None and not isinstance(cadence, str):
            local.append(f"{label}: 'engagement_cadence' must be a string if provided")

        notes = item.get("notes")
        if notes is not None and not isinstance(notes, str):
            local.append(f"{label}: 'notes' must be a string if provided")

        if local:
            issues.extend(local)
            continue

        entries.append(
            StakeholderEntry(
                name=name.strip(),
                role=role.strip(),
                team=team.strip() if isinstance(team, str) else None,
                email=email.strip() if isinstance(email, str) else None,
                interests=interests,
                decision_rights=decision_rights,
                influence=influence,
                engagement_cadence=cadence.strip() if isinstance(cadence, str) else None,
                notes=notes.strip() if isinstance(notes, str) else None,
                last_ingested=item.get("last_ingested"),
            )
        )

    if issues:
        raise SchemaError(issues)

    return entries


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


def load_stakeholders_yaml(path: str) -> list[StakeholderEntry]:
    """Load existing stakeholders.yaml. Returns [] if missing. Raises SchemaError if invalid."""
    if not os.path.isfile(path):
        return []
    import yaml
    with open(path) as f:
        raw = yaml.safe_load(f) or []
    if isinstance(raw, dict):
        raw = raw.get("stakeholders", [])
    return parse_stakeholders(raw)


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------

def lint_missing_decision_rights_on_high_influence(
    stakeholders: list[StakeholderEntry],
) -> list[LintWarning]:
    """Flag influence=high entries with no decision_rights documented."""
    warnings: list[LintWarning] = []
    for s in stakeholders:
        if s.influence == "high" and not s.decision_rights:
            warnings.append(
                LintWarning(
                    rule="missing_decision_rights_on_high_influence",
                    concept=s.name,
                    message=(
                        "influence=high but decision_rights is empty — high-influence "
                        "stakeholders should have at least one documented decision right"
                    ),
                )
            )
    return warnings


def lint_tbd_without_notes(
    stakeholders: list[StakeholderEntry],
) -> list[LintWarning]:
    """Flag TBD placeholders that lack notes explaining why/what's missing."""
    warnings: list[LintWarning] = []
    for s in stakeholders:
        if _is_tbd(s.name) and not (s.notes and s.notes.strip()):
            label = f"TBD ({s.role})" if s.role else "TBD"
            warnings.append(
                LintWarning(
                    rule="tbd_without_notes",
                    concept=label,
                    message=(
                        "TBD placeholder has no notes — explain why the role is unfilled "
                        "and what introduction is needed to resolve it"
                    ),
                )
            )
    return warnings


def run_lints(stakeholders: list[StakeholderEntry]) -> list[LintWarning]:
    """Run all stakeholder lint rules against the newly-ingested entries."""
    warnings: list[LintWarning] = []
    warnings.extend(lint_missing_decision_rights_on_high_influence(stakeholders))
    warnings.extend(lint_tbd_without_notes(stakeholders))
    return warnings


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

@dataclass
class MergeReport:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)


def _merge_key(s: StakeholderEntry) -> tuple:
    """Return the dedup key for a stakeholder.

    Named entries key on the normalised name. TBD placeholders key on
    (TBD, role, team) so multiple TBDs for different roles coexist.
    """
    if _is_tbd(s.name):
        return ("__tbd__", (s.role or "").casefold(), (s.team or "").casefold())
    return ("__named__", _normalise_name(s.name))


def merge_stakeholders(
    existing: list[StakeholderEntry],
    new: list[StakeholderEntry],
    session: str,
    interviewer: str,
    at: datetime,
) -> tuple[list[StakeholderEntry], MergeReport]:
    by_key: dict[tuple, StakeholderEntry] = {_merge_key(s): s for s in existing}
    order: list[tuple] = [_merge_key(s) for s in existing]
    report = MergeReport()

    provenance = make_provenance(session, interviewer, at)

    for n in new:
        key = _merge_key(n)
        if key in by_key:
            prev = by_key[key]

            merged_interests = list(prev.interests)
            seen_i = {v.casefold() for v in merged_interests}
            for v in n.interests:
                if v.casefold() not in seen_i:
                    merged_interests.append(v)
                    seen_i.add(v.casefold())

            merged_rights = list(prev.decision_rights)
            seen_r = {v.casefold() for v in merged_rights}
            for v in n.decision_rights:
                if v.casefold() not in seen_r:
                    merged_rights.append(v)
                    seen_r.add(v.casefold())

            by_key[key] = StakeholderEntry(
                name=prev.name,
                role=n.role or prev.role,
                team=n.team if n.team is not None else prev.team,
                email=n.email if n.email is not None else prev.email,
                interests=merged_interests,
                decision_rights=merged_rights,
                influence=n.influence if n.influence is not None else prev.influence,
                engagement_cadence=(
                    n.engagement_cadence if n.engagement_cadence is not None else prev.engagement_cadence
                ),
                notes=n.notes if n.notes is not None else prev.notes,
                last_ingested=provenance,
            )
            report.updated.append(prev.name)
        else:
            by_key[key] = StakeholderEntry(
                name=n.name,
                role=n.role,
                team=n.team,
                email=n.email,
                interests=n.interests,
                decision_rights=n.decision_rights,
                influence=n.influence,
                engagement_cadence=n.engagement_cadence,
                notes=n.notes,
                last_ingested=provenance,
            )
            order.append(key)
            report.added.append(n.name)

    return [by_key[k] for k in order], report


# ---------------------------------------------------------------------------
# YAML writer
# ---------------------------------------------------------------------------

def write_stakeholders_yaml(stakeholders: list[StakeholderEntry], path: str) -> None:
    """Serialise stakeholders to YAML. Stable field order, block style."""
    def to_dict(s: StakeholderEntry) -> dict:
        d: dict = {"name": s.name, "role": s.role}
        if s.team is not None:
            d["team"] = s.team
        if s.email is not None:
            d["email"] = s.email
        if s.interests:
            d["interests"] = list(s.interests)
        if s.decision_rights:
            d["decision_rights"] = list(s.decision_rights)
        if s.influence is not None:
            d["influence"] = s.influence
        if s.engagement_cadence is not None:
            d["engagement_cadence"] = s.engagement_cadence
        if s.notes is not None:
            d["notes"] = s.notes
        if s.last_ingested is not None:
            d["last_ingested"] = dict(s.last_ingested)
        return d

    write_yaml_list([to_dict(s) for s in stakeholders], path)


# ---------------------------------------------------------------------------
# Warnings labels for this module
# ---------------------------------------------------------------------------

STAKEHOLDER_WARNING_LABELS: dict[str, str] = {
    "missing_decision_rights_on_high_influence": "High-influence stakeholders missing decision_rights",
    "tbd_without_notes": "TBD placeholders without notes",
}

STAKEHOLDER_WARNING_ORDER: list[str] = [
    "missing_decision_rights_on_high_influence",
    "tbd_without_notes",
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
    output_path: str
    warnings_path: str


def ingest_stakeholders(
    workspace_path: str,
    fixture_path: str,
    session: str,
    interviewer: str,
    at: datetime | None = None,
) -> IngestResult:
    """Orchestrate the stakeholders ingest."""
    if at is None:
        at = datetime.now(timezone.utc)

    if not os.path.isfile(fixture_path):
        raise FileNotFoundError(f"ingest source not found: {fixture_path}")

    import yaml
    with open(fixture_path) as f:
        raw = yaml.safe_load(f) or []
    if isinstance(raw, dict):
        raw = raw.get("stakeholders", [])

    new_entries = parse_stakeholders(raw)

    target_path = os.path.join(workspace_path, "00_scope", "stakeholders.yaml")
    existing = load_stakeholders_yaml(target_path)

    warnings = run_lints(new_entries)

    merged, report = merge_stakeholders(
        existing, new_entries, session=session, interviewer=interviewer, at=at
    )

    write_stakeholders_yaml(merged, target_path)

    warnings_path = os.path.join(workspace_path, "ingest-warnings.md")
    write_warnings_file(
        warnings,
        warnings_path,
        session=session,
        interviewer=interviewer,
        at=at,
        item_kind="stakeholder",
        rule_labels=STAKEHOLDER_WARNING_LABELS,
        rule_order=STAKEHOLDER_WARNING_ORDER,
    )

    return IngestResult(
        merged_count=len(merged),
        added=report.added,
        updated=report.updated,
        warnings=warnings,
        output_path=target_path,
        warnings_path=warnings_path,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _print_summary(result: IngestResult, root: str) -> None:
    print(f"Ingested stakeholders into {os.path.relpath(result.output_path, root)}")
    print(f"  Added:   {len(result.added)}  ({', '.join(result.added) if result.added else '—'})")
    print(f"  Updated: {len(result.updated)}  ({', '.join(result.updated) if result.updated else '—'})")
    print(f"  Total:   {result.merged_count} stakeholder(s) in workspace")
    print("")
    if not result.warnings:
        print("Lint: clean — no warnings.")
    else:
        print(f"Lint: {len(result.warnings)} warning(s) — see {os.path.relpath(result.warnings_path, root)}")


def main() -> None:
    run_ingest_cli(
        prog="gnosis ingest stakeholders",
        description="Ingest LLM-extracted stakeholder YAML into 00_scope/stakeholders.yaml.",
        source_help="Path to the LLM-output YAML file.",
        ingest_fn=ingest_stakeholders,
        print_summary=_print_summary,
    )


if __name__ == "__main__":
    main()
