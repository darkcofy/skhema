"""Tests for gnosis.ingest_formalization."""
from __future__ import annotations

import datetime as _dt
import os

import pytest
import yaml

from gnosis.ingest import SchemaError
from gnosis.ingest_formalization import (
    IngestResult,
    ingest_formalization,
    lint_class_without_candidate_concept,
    lint_missing_identifier_property,
    lint_relationship_target_unknown,
    lint_unresolved_synonym_as_class,
    load_unresolved_synonym_terms,
    merge_classes,
    parse_classes,
)


def _fixed_at() -> _dt.datetime:
    return _dt.datetime(2026, 5, 12, 10, 0, 0, tzinfo=_dt.timezone.utc)


def _class(**overrides) -> dict:
    c = {
        "name": "Order",
        "definition": "A customer's purchase intent — one basket at one time.",
        "identifier": "id",
        "properties": ["id", "customer_id", "status"],
    }
    c.update(overrides)
    return c


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class TestParseClasses:
    def test_minimal_valid(self):
        entries = parse_classes([_class()])
        assert entries[0].name == "Order"
        assert entries[0].identifier == "id"
        assert "id" in entries[0].properties

    def test_full_valid(self):
        entries = parse_classes([_class(
            relationships=[{
                "target": "Customer", "type": "belongs_to",
                "label": "placed_by", "cardinality": "N:1",
            }],
            traces_to=["02_concepts/candidate-concepts.yaml#Order"],
        )])
        e = entries[0]
        assert e.relationships[0].target == "Customer"
        assert e.relationships[0].type == "belongs_to"
        assert "02_concepts/candidate-concepts.yaml#Order" in e.traces_to

    def test_missing_name(self):
        bad = _class()
        del bad["name"]
        with pytest.raises(SchemaError):
            parse_classes([bad])

    def test_name_not_pascal_case(self):
        with pytest.raises(SchemaError):
            parse_classes([_class(name="order")])

    def test_definition_too_short(self):
        with pytest.raises(SchemaError):
            parse_classes([_class(definition="short")])

    def test_missing_identifier(self):
        with pytest.raises(SchemaError):
            parse_classes([_class(identifier="")])

    def test_empty_properties(self):
        with pytest.raises(SchemaError):
            parse_classes([_class(properties=[])])

    def test_invalid_relationship_type(self):
        with pytest.raises(SchemaError):
            parse_classes([_class(relationships=[{
                "target": "Customer", "type": "owns",
                "label": "placed_by", "cardinality": "N:1",
            }])])

    def test_invalid_cardinality(self):
        with pytest.raises(SchemaError):
            parse_classes([_class(relationships=[{
                "target": "Customer", "type": "belongs_to",
                "label": "placed_by", "cardinality": "many",
            }])])

    def test_duplicate_name(self):
        with pytest.raises(SchemaError):
            parse_classes([_class(), _class()])


# ---------------------------------------------------------------------------
# load_unresolved_synonym_terms
# ---------------------------------------------------------------------------

class TestLoadUnresolvedSynonymTerms:
    def test_missing_file(self, tmp_path):
        assert load_unresolved_synonym_terms(str(tmp_path / "nope.yaml")) == set()

    def test_unresolved_terms_returned(self, tmp_path):
        path = tmp_path / "syn.yaml"
        path.write_text(yaml.safe_dump([
            {
                "title": "Metric / Measure",
                "type": "near-synonym",
                "severity": "high",
                "terms": ["metric", "measure"],
                "proposed_canonical": None,
            },
        ]))
        terms = load_unresolved_synonym_terms(str(path))
        assert "metric" in terms
        assert "measure" in terms

    def test_resolved_entries_skipped(self, tmp_path):
        path = tmp_path / "syn.yaml"
        path.write_text(yaml.safe_dump([
            {
                "title": "X",
                "type": "synonym",
                "severity": "low",
                "terms": ["x", "y"],
                "proposed_canonical": "x",  # resolved
            },
        ]))
        assert load_unresolved_synonym_terms(str(path)) == set()


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------

class TestLintClassWithoutCandidateConcept:
    def test_unknown_flagged(self):
        entries = parse_classes([_class(name="Ghost")])
        warnings = lint_class_without_candidate_concept(entries, {"Order"})
        assert len(warnings) == 1
        assert warnings[0].concept == "Ghost"

    def test_known_passes(self):
        entries = parse_classes([_class()])
        assert lint_class_without_candidate_concept(entries, {"Order"}) == []


class TestLintUnresolvedSynonymAsClass:
    def test_flagged(self):
        entries = parse_classes([_class(name="Metric", properties=["id", "name"])])
        warnings = lint_unresolved_synonym_as_class(entries, {"metric"})
        assert len(warnings) == 1
        assert warnings[0].rule == "unresolved_synonym_as_class"

    def test_not_in_unresolved_passes(self):
        entries = parse_classes([_class()])
        assert lint_unresolved_synonym_as_class(entries, {"metric"}) == []


class TestLintRelationshipTargetUnknown:
    def test_dangling_flagged(self):
        entries = parse_classes([_class(relationships=[{
            "target": "Ghost", "type": "belongs_to",
            "label": "haunts", "cardinality": "N:1",
        }])])
        warnings = lint_relationship_target_unknown(entries, [])
        assert len(warnings) == 1

    def test_target_in_same_batch_passes(self):
        entries = parse_classes([
            _class(relationships=[{
                "target": "Customer", "type": "belongs_to",
                "label": "placed_by", "cardinality": "N:1",
            }]),
            _class(name="Customer", properties=["id"],
                   definition="A person or org who transacts."),
        ])
        warnings = lint_relationship_target_unknown(entries, [])
        assert warnings == []


class TestLintMissingIdentifierProperty:
    def test_identifier_not_in_properties_flagged(self):
        entries = parse_classes([_class(identifier="id", properties=["name", "status"])])
        warnings = lint_missing_identifier_property(entries)
        assert len(warnings) == 1

    def test_identifier_in_properties_passes(self):
        entries = parse_classes([_class()])
        assert lint_missing_identifier_property(entries) == []


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

class TestMergeClasses:
    def test_new_added(self):
        new = parse_classes([_class()])
        merged, report = merge_classes([], new, session="s", interviewer="al", at=_fixed_at())
        assert len(merged) == 1
        assert report.added == ["Order"]

    def test_properties_unioned(self):
        existing = parse_classes([_class(properties=["id", "customer_id"])])
        new = parse_classes([_class(properties=["id", "total_amount"])])
        merged, _ = merge_classes(existing, new, session="s", interviewer="al", at=_fixed_at())
        assert "customer_id" in merged[0].properties
        assert "total_amount" in merged[0].properties

    def test_relationships_dedup_by_target_and_type(self):
        existing = parse_classes([_class(relationships=[{
            "target": "Customer", "type": "belongs_to",
            "label": "placed_by", "cardinality": "N:1",
        }])])
        # Same target+type → dedup
        new = parse_classes([_class(relationships=[{
            "target": "Customer", "type": "belongs_to",
            "label": "placed_by", "cardinality": "N:1",
        }])])
        merged, _ = merge_classes(existing, new, session="s", interviewer="al", at=_fixed_at())
        assert len(merged[0].relationships) == 1


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def _write_workspace(tmp_path, concepts=None, synonyms=None) -> str:
    workspace = tmp_path / "ontology"
    (workspace / "02_concepts").mkdir(parents=True)
    (workspace / "01_language").mkdir(parents=True)
    (workspace / "05_formalization").mkdir(parents=True)
    if concepts is None:
        concepts = [{
            "name": "Order",
            "domain": "orders",
            "description": "A purchase intent — long enough description for schema.",
            "source_quotes": [{"quote": "q", "source": "Alice", "date": "2026-04-12"}],
        }]
    (workspace / "02_concepts" / "candidate-concepts.yaml").write_text(yaml.safe_dump(concepts))
    if synonyms is not None:
        (workspace / "01_language" / "synonym-conflicts.yaml").write_text(yaml.safe_dump(synonyms))
    return str(workspace)


class TestIngestFormalization:
    def test_fresh_ingest(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.yaml"
        fixture.write_text(yaml.safe_dump([_class()]))
        result = ingest_formalization(
            workspace_path=workspace, fixture_path=str(fixture),
            session="s", interviewer="al", at=_fixed_at(),
        )
        assert isinstance(result, IngestResult)
        assert result.added == ["Order"]
        assert os.path.isfile(os.path.join(workspace, "05_formalization", "ontology.yaml"))

    def test_warnings_written(self, tmp_path):
        workspace = _write_workspace(
            tmp_path,
            synonyms=[{
                "title": "Metric / Measure", "type": "near-synonym",
                "severity": "high", "terms": ["metric", "measure"],
                "proposed_canonical": None,
            }],
        )
        fixture = tmp_path / "f.yaml"
        fixture.write_text(yaml.safe_dump([
            _class(name="Metric", properties=["id", "name"],
                   definition="A business-level measurement with grain and filters."),
            _class(name="Ghost", properties=["id"],
                   definition="This class has no candidate concept peer at all."),
        ]))
        result = ingest_formalization(
            workspace_path=workspace, fixture_path=str(fixture),
            session="s", interviewer="al", at=_fixed_at(),
        )
        rules = {w.rule for w in result.warnings}
        assert "class_without_candidate_concept" in rules  # Ghost, Metric (neither in concepts)
        assert "unresolved_synonym_as_class" in rules       # Metric
        text = open(os.path.join(workspace, "ingest-warnings.md")).read()
        assert "class(s)" in text

    def test_schema_error_writes_nothing(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.yaml"
        fixture.write_text(yaml.safe_dump([_class(name="lowercase")]))
        with pytest.raises(SchemaError):
            ingest_formalization(workspace_path=workspace, fixture_path=str(fixture),
                                 session="s", interviewer="al", at=_fixed_at())
        assert not os.path.isfile(os.path.join(workspace, "05_formalization", "ontology.yaml"))
