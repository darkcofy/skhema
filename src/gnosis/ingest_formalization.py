"""Ingest LLM-synthesised canonical ontology into 05_formalization/ontology.yaml.

Matches the output format of `skills/gnosis/formalizing-ontology-from-workspace.md`.
BYOLLM — input is YAML the user has in their hands.

Formalisation is the engagement's deliverable: a set of classes with identifiers,
properties, and relationships. Unlike the other ingests, the source of truth is
the workspace itself — the LLM rolls up prior stages, gnosis validates the result
against those stages.
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
    load_concepts_yaml,
    write_warnings_file,
)


ALLOWED_RELATIONSHIP_TYPES = {"has_one", "has_many", "belongs_to", "references"}
ALLOWED_CARDINALITIES = {"1:1", "1:N", "N:1", "N:M"}


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

@dataclass
class Relationship:
    target: str
    type: str
    label: str
    cardinality: str


@dataclass
class ClassEntry:
    name: str
    definition: str
    identifier: str
    properties: list[str]
    relationships: list[Relationship] = field(default_factory=list)
    traces_to: list[str] = field(default_factory=list)
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


def parse_classes(raw: list) -> list[ClassEntry]:
    if not isinstance(raw, list):
        raise SchemaError(["Top-level YAML must be a list of class entries"])

    issues: list[str] = []
    entries: list[ClassEntry] = []
    seen: set[str] = set()

    for i, item in enumerate(raw):
        label = f"entry[{i}]"
        if not isinstance(item, dict):
            issues.append(f"{label}: must be a mapping")
            continue

        name = item.get("name")
        if name:
            label = f"class '{name}'"
        local: list[str] = []

        if not isinstance(name, str) or not name.strip():
            local.append(f"{label}: 'name' is required")
        elif not re.match(r"^[A-Z][A-Za-z0-9]*$", name.strip()):
            local.append(f"{label}: 'name' must be PascalCase")
        else:
            key = name.strip().casefold()
            if key in seen:
                local.append(f"{label}: duplicate class name in the same ingest")
            seen.add(key)

        definition = item.get("definition")
        if not isinstance(definition, str) or len(definition.strip()) < 20:
            local.append(f"{label}: 'definition' is required and must be at least 20 characters")

        identifier = item.get("identifier")
        if not isinstance(identifier, str) or not identifier.strip():
            local.append(f"{label}: 'identifier' is required")

        properties = _coerce_str_list(item.get("properties"), f"{label} properties", local)
        if not properties:
            local.append(f"{label}: 'properties' must contain at least one property name")

        relationships_raw = item.get("relationships", [])
        relationships: list[Relationship] = []
        if relationships_raw is None:
            relationships_raw = []
        if not isinstance(relationships_raw, list):
            local.append(f"{label}: 'relationships' must be a list")
        else:
            for j, r in enumerate(relationships_raw):
                r_label = f"{label} relationships[{j}]"
                if not isinstance(r, dict):
                    local.append(f"{r_label}: must be a mapping")
                    continue
                target = r.get("target")
                rtype = r.get("type")
                rlabel = r.get("label")
                card = r.get("cardinality")
                if not isinstance(target, str) or not re.match(r"^[A-Z][A-Za-z0-9]*$", target.strip() if isinstance(target, str) else ""):
                    local.append(f"{r_label}: 'target' is required and must be PascalCase")
                if not isinstance(rtype, str) or rtype.strip().lower() not in ALLOWED_RELATIONSHIP_TYPES:
                    local.append(f"{r_label}: 'type' must be one of {sorted(ALLOWED_RELATIONSHIP_TYPES)}")
                if not isinstance(rlabel, str) or not rlabel.strip():
                    local.append(f"{r_label}: 'label' is required")
                # PyYAML parses unquoted `1:1` as the sexagesimal integer 61.
                # Silently accept that so consultants aren't punished for a YAML quirk.
                if card == 61:
                    card = "1:1"
                if not isinstance(card, str) or card.strip() not in ALLOWED_CARDINALITIES:
                    local.append(f"{r_label}: 'cardinality' must be one of {sorted(ALLOWED_CARDINALITIES)}")
                if isinstance(target, str) and isinstance(rtype, str) and isinstance(rlabel, str) and isinstance(card, str):
                    relationships.append(Relationship(
                        target=target.strip(),
                        type=rtype.strip().lower(),
                        label=rlabel.strip(),
                        cardinality=card.strip(),
                    ))

        traces_to = _coerce_str_list(item.get("traces_to"), f"{label} traces_to", local)

        if local:
            issues.extend(local)
            continue

        entries.append(ClassEntry(
            name=name.strip(),
            definition=definition.strip(),
            identifier=identifier.strip(),
            properties=properties,
            relationships=relationships,
            traces_to=traces_to,
            last_ingested=item.get("last_ingested"),
        ))

    if issues:
        raise SchemaError(issues)

    return entries


def load_ontology_yaml(path: str) -> list[ClassEntry]:
    if not os.path.isfile(path):
        return []
    import yaml
    with open(path) as f:
        raw = yaml.safe_load(f) or []
    if not isinstance(raw, list):
        return []
    return parse_classes(raw)


# ---------------------------------------------------------------------------
# Helpers for reading prior-stage artefacts
# ---------------------------------------------------------------------------

def load_unresolved_synonym_terms(synonyms_yaml_path: str) -> set[str]:
    """Return the case-folded term set from synonym-conflicts entries that have
    `proposed_canonical: null` (i.e. unresolved).

    Missing file → empty set.
    """
    if not os.path.isfile(synonyms_yaml_path):
        return set()
    import yaml
    with open(synonyms_yaml_path) as f:
        raw = yaml.safe_load(f) or []
    if not isinstance(raw, list):
        return set()
    unresolved: set[str] = set()
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        proposed = entry.get("proposed_canonical")
        if proposed is not None and str(proposed).strip():
            continue  # resolved — skip
        terms = entry.get("terms", [])
        if isinstance(terms, list):
            for t in terms:
                if isinstance(t, str) and t.strip():
                    unresolved.add(t.strip().casefold())
    return unresolved


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------

def lint_class_without_candidate_concept(
    entries: list[ClassEntry], known_concepts: set[str]
) -> list[LintWarning]:
    known_fold = {c.casefold() for c in known_concepts}
    warnings: list[LintWarning] = []
    for c in entries:
        if c.name.casefold() not in known_fold:
            warnings.append(
                LintWarning(
                    rule="class_without_candidate_concept",
                    concept=c.name,
                    message=(
                        f"class '{c.name}' has no matching concept in "
                        "02_concepts/candidate-concepts.yaml — formalisation has drifted from discovery"
                    ),
                )
            )
    return warnings


def lint_unresolved_synonym_as_class(
    entries: list[ClassEntry], unresolved_terms: set[str]
) -> list[LintWarning]:
    """Flag class names that appear as terms in unresolved synonym conflicts."""
    warnings: list[LintWarning] = []
    for c in entries:
        if c.name.casefold() in unresolved_terms:
            warnings.append(
                LintWarning(
                    rule="unresolved_synonym_as_class",
                    concept=c.name,
                    message=(
                        f"'{c.name}' is a term in an unresolved synonym-conflicts entry — "
                        "close the conflict (set proposed_canonical) before promoting to a class"
                    ),
                )
            )
    return warnings


def lint_relationship_target_unknown(
    new_entries: list[ClassEntry], existing_entries: list[ClassEntry]
) -> list[LintWarning]:
    """Relationship targets must resolve to a class in this ontology (new ∪ existing)."""
    all_classes = {c.name.casefold() for c in new_entries} | {c.name.casefold() for c in existing_entries}
    warnings: list[LintWarning] = []
    for c in new_entries:
        for r in c.relationships:
            if r.target.casefold() not in all_classes:
                warnings.append(
                    LintWarning(
                        rule="relationship_target_unknown",
                        concept=c.name,
                        message=(
                            f"relationship {r.label} → '{r.target}' (type={r.type}) "
                            "points at a class that isn't in this ontology"
                        ),
                    )
                )
    return warnings


def lint_missing_identifier_property(entries: list[ClassEntry]) -> list[LintWarning]:
    """The class's `identifier` must appear in its `properties` list."""
    warnings: list[LintWarning] = []
    for c in entries:
        props_fold = {p.casefold() for p in c.properties}
        if c.identifier.casefold() not in props_fold:
            warnings.append(
                LintWarning(
                    rule="missing_identifier_property",
                    concept=c.name,
                    message=(
                        f"declared identifier '{c.identifier}' is not among the class's "
                        f"properties {c.properties}"
                    ),
                )
            )
    return warnings


def run_lints(
    new_entries: list[ClassEntry],
    existing_entries: list[ClassEntry],
    known_concepts: set[str],
    unresolved_synonyms: set[str],
) -> list[LintWarning]:
    warnings: list[LintWarning] = []
    warnings.extend(lint_class_without_candidate_concept(new_entries, known_concepts))
    warnings.extend(lint_unresolved_synonym_as_class(new_entries, unresolved_synonyms))
    warnings.extend(lint_relationship_target_unknown(new_entries, existing_entries))
    warnings.extend(lint_missing_identifier_property(new_entries))
    return warnings


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

@dataclass
class MergeReport:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)


def merge_classes(
    existing: list[ClassEntry],
    new: list[ClassEntry],
    session: str,
    interviewer: str,
    at: datetime,
) -> tuple[list[ClassEntry], MergeReport]:
    by_key: dict[str, ClassEntry] = {c.name.casefold(): c for c in existing}
    order: list[str] = [c.name.casefold() for c in existing]
    report = MergeReport()

    provenance = make_provenance(session, interviewer, at)

    for n in new:
        key = n.name.casefold()
        if key in by_key:
            prev = by_key[key]

            merged_props = list(prev.properties)
            seen_p = {p.casefold() for p in merged_props}
            for p in n.properties:
                if p.casefold() not in seen_p:
                    merged_props.append(p)
                    seen_p.add(p.casefold())

            merged_rel = list(prev.relationships)
            seen_r = {(r.target.casefold(), r.type) for r in merged_rel}
            for r in n.relationships:
                k = (r.target.casefold(), r.type)
                if k not in seen_r:
                    merged_rel.append(r)
                    seen_r.add(k)

            merged_traces = list(prev.traces_to)
            seen_t = {t.casefold() for t in merged_traces}
            for t in n.traces_to:
                if t.casefold() not in seen_t:
                    merged_traces.append(t)
                    seen_t.add(t.casefold())

            by_key[key] = ClassEntry(
                name=prev.name,
                definition=n.definition,
                identifier=n.identifier,
                properties=merged_props,
                relationships=merged_rel,
                traces_to=merged_traces,
                last_ingested=provenance,
            )
            report.updated.append(prev.name)
        else:
            by_key[key] = ClassEntry(
                name=n.name,
                definition=n.definition,
                identifier=n.identifier,
                properties=n.properties,
                relationships=n.relationships,
                traces_to=n.traces_to,
                last_ingested=provenance,
            )
            order.append(key)
            report.added.append(n.name)

    return [by_key[k] for k in order], report


# ---------------------------------------------------------------------------
# YAML writer
# ---------------------------------------------------------------------------

def write_ontology_yaml(entries: list[ClassEntry], path: str) -> None:
    def rel_to_dict(r: Relationship) -> dict:
        return {"target": r.target, "type": r.type, "label": r.label, "cardinality": r.cardinality}

    def to_dict(c: ClassEntry) -> dict:
        d: dict = {
            "name": c.name,
            "definition": c.definition,
            "identifier": c.identifier,
            "properties": list(c.properties),
        }
        if c.relationships:
            d["relationships"] = [rel_to_dict(r) for r in c.relationships]
        if c.traces_to:
            d["traces_to"] = list(c.traces_to)
        if c.last_ingested is not None:
            d["last_ingested"] = dict(c.last_ingested)
        return d

    write_yaml_list([to_dict(c) for c in entries], path)


# ---------------------------------------------------------------------------
# Warnings labels
# ---------------------------------------------------------------------------

FORMALIZATION_WARNING_LABELS: dict[str, str] = {
    "class_without_candidate_concept": "Classes without a matching candidate concept",
    "unresolved_synonym_as_class": "Classes whose name is an unresolved synonym-conflict term",
    "relationship_target_unknown": "Relationship targets not in this ontology",
    "missing_identifier_property": "Classes whose identifier is not in their properties",
}

FORMALIZATION_WARNING_ORDER: list[str] = [
    "class_without_candidate_concept",
    "unresolved_synonym_as_class",
    "relationship_target_unknown",
    "missing_identifier_property",
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


def ingest_formalization(
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

    new_entries = parse_classes(raw)

    target_path = os.path.join(workspace_path, "05_formalization", "ontology.yaml")
    existing = load_ontology_yaml(target_path)

    known_concepts = {c.name for c in load_concepts_yaml(
        os.path.join(workspace_path, "02_concepts", "candidate-concepts.yaml")
    )}
    unresolved_terms = load_unresolved_synonym_terms(
        os.path.join(workspace_path, "01_language", "synonym-conflicts.yaml")
    )

    warnings = run_lints(new_entries, existing, known_concepts, unresolved_terms)

    merged, report = merge_classes(
        existing, new_entries, session=session, interviewer=interviewer, at=at,
    )

    write_ontology_yaml(merged, target_path)

    warnings_path = os.path.join(workspace_path, "ingest-warnings.md")
    write_warnings_file(
        warnings, warnings_path, session=session, interviewer=interviewer, at=at,
        item_kind="class",
        rule_labels=FORMALIZATION_WARNING_LABELS,
        rule_order=FORMALIZATION_WARNING_ORDER,
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
    print(f"Ingested formalization into {os.path.relpath(result.output_path, root)}")
    print(f"  Added:   {len(result.added)}  ({', '.join(result.added) if result.added else '—'})")
    print(f"  Updated: {len(result.updated)}  ({', '.join(result.updated) if result.updated else '—'})")
    print(f"  Total:   {result.merged_count} class(es) in ontology")
    print("")
    if not result.warnings:
        print("Lint: clean — no warnings.")
    else:
        print(f"Lint: {len(result.warnings)} warning(s) — see {os.path.relpath(result.warnings_path, root)}")


def main() -> None:
    run_ingest_cli(
        prog="gnosis ingest formalization",
        description="Ingest LLM-synthesised canonical ontology into 05_formalization/ontology.yaml.",
        source_help="Path to the LLM-output YAML file.",
        ingest_fn=ingest_formalization,
        print_summary=_print_summary,
    )


if __name__ == "__main__":
    main()
