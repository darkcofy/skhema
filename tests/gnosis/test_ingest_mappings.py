"""Tests for gnosis.ingest_mappings."""
from __future__ import annotations

import csv
import datetime as _dt
import os

import pytest
import yaml

from gnosis.ingest import SchemaError
from gnosis.ingest_mappings import (
    IngestResult,
    ingest_mappings,
    lint_ambiguous_without_notes,
    lint_low_confidence_without_notes,
    lint_unknown_canonical_concept,
    merge_mappings,
    parse_mapping_rows,
)


def _fixed_at() -> _dt.datetime:
    return _dt.datetime(2026, 5, 11, 10, 0, 0, tzinfo=_dt.timezone.utc)


def _header() -> list[str]:
    return [
        "source_system", "source_entity", "source_field",
        "canonical_concept", "canonical_property",
        "mapping_type", "confidence", "notes",
    ]


def _row(**overrides) -> dict:
    r = {
        "source_system": "pos",
        "source_entity": "transactions",
        "source_field": "txn_id",
        "canonical_concept": "Transaction",
        "canonical_property": "id",
        "mapping_type": "direct",
        "confidence": "high",
        "notes": "",
    }
    r.update(overrides)
    return r


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class TestParseMappingRows:
    def test_minimal_valid(self):
        entries = parse_mapping_rows(_header(), [_row()])
        assert entries[0].source_system == "pos"
        assert entries[0].mapping_type == "direct"

    def test_missing_required_column(self):
        cols = _header()
        cols.remove("confidence")
        with pytest.raises(SchemaError) as exc:
            parse_mapping_rows(cols, [])
        assert any("missing required column" in i for i in exc.value.issues)

    def test_unknown_column(self):
        cols = _header() + ["weight"]
        with pytest.raises(SchemaError) as exc:
            parse_mapping_rows(cols, [])
        assert any("unknown column" in i for i in exc.value.issues)

    def test_invalid_mapping_type(self):
        with pytest.raises(SchemaError):
            parse_mapping_rows(_header(), [_row(mapping_type="magical")])

    def test_invalid_confidence(self):
        with pytest.raises(SchemaError):
            parse_mapping_rows(_header(), [_row(confidence="certain")])

    def test_missing_source_system(self):
        with pytest.raises(SchemaError):
            parse_mapping_rows(_header(), [_row(source_system="")])

    def test_duplicate_triple_rejected(self):
        with pytest.raises(SchemaError) as exc:
            parse_mapping_rows(_header(), [_row(), _row()])
        assert any("duplicate" in i for i in exc.value.issues)

    def test_duplicate_case_insensitive(self):
        with pytest.raises(SchemaError):
            parse_mapping_rows(_header(), [
                _row(source_system="POS"),
                _row(source_system="pos"),
            ])


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------

class TestLintUnknownCanonicalConcept:
    def test_unknown_flagged(self):
        entries = parse_mapping_rows(_header(), [_row(canonical_concept="Ghost")])
        warnings = lint_unknown_canonical_concept(entries, {"Transaction", "Order"})
        assert len(warnings) == 1
        assert "Ghost" in warnings[0].message

    def test_known_passes(self):
        entries = parse_mapping_rows(_header(), [_row(canonical_concept="Transaction")])
        assert lint_unknown_canonical_concept(entries, {"Transaction"}) == []

    def test_empty_canonical_skipped(self):
        entries = parse_mapping_rows(_header(), [_row(
            canonical_concept="", canonical_property="",
            mapping_type="unmapped", notes="finance-internal",
        )])
        assert lint_unknown_canonical_concept(entries, set()) == []

    def test_case_insensitive(self):
        entries = parse_mapping_rows(_header(), [_row(canonical_concept="transaction")])
        assert lint_unknown_canonical_concept(entries, {"Transaction"}) == []


class TestLintLowConfidenceWithoutNotes:
    def test_low_no_notes_flagged(self):
        entries = parse_mapping_rows(_header(), [_row(confidence="low", notes="")])
        warnings = lint_low_confidence_without_notes(entries)
        assert len(warnings) == 1

    def test_low_with_notes_passes(self):
        entries = parse_mapping_rows(_header(), [_row(confidence="low", notes="ambiguous")])
        assert lint_low_confidence_without_notes(entries) == []

    def test_medium_without_notes_passes(self):
        entries = parse_mapping_rows(_header(), [_row(confidence="medium", notes="")])
        assert lint_low_confidence_without_notes(entries) == []


class TestLintAmbiguousWithoutNotes:
    def test_ambiguous_no_notes_flagged(self):
        entries = parse_mapping_rows(_header(), [_row(
            mapping_type="ambiguous", canonical_concept="", canonical_property="", notes="",
        )])
        warnings = lint_ambiguous_without_notes(entries)
        assert len(warnings) == 1

    def test_unmapped_no_notes_flagged(self):
        entries = parse_mapping_rows(_header(), [_row(
            mapping_type="unmapped", canonical_concept="", canonical_property="", notes="",
        )])
        warnings = lint_ambiguous_without_notes(entries)
        assert len(warnings) == 1

    def test_ambiguous_with_notes_passes(self):
        entries = parse_mapping_rows(_header(), [_row(
            mapping_type="ambiguous", canonical_concept="", canonical_property="",
            notes="supplier PO vs customer order",
        )])
        assert lint_ambiguous_without_notes(entries) == []


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

class TestMergeMappings:
    def test_new_added(self):
        new = parse_mapping_rows(_header(), [_row()])
        merged, report = merge_mappings([], new)
        assert len(merged) == 1
        assert report.added == ["pos.transactions.txn_id"]

    def test_identical_row_skipped(self):
        existing = parse_mapping_rows(_header(), [_row()])
        new = parse_mapping_rows(_header(), [_row()])
        merged, report = merge_mappings(existing, new)
        assert report.skipped == ["pos.transactions.txn_id"]
        assert report.updated == []

    def test_new_notes_unioned(self):
        existing = parse_mapping_rows(_header(), [_row(notes="Primary key")])
        new = parse_mapping_rows(_header(), [_row(notes="Also used for fraud cross-ref")])
        merged, report = merge_mappings(existing, new)
        assert report.updated == ["pos.transactions.txn_id"]
        assert "Primary key" in merged[0].notes
        assert "Also used for fraud cross-ref" in merged[0].notes

    def test_canonical_not_clobbered(self):
        existing = parse_mapping_rows(_header(), [_row(
            canonical_concept="Transaction", notes="curated",
        )])
        new = parse_mapping_rows(_header(), [_row(
            canonical_concept="Ghost", notes="curated",  # LLM hallucination
        )])
        merged, _ = merge_mappings(existing, new)
        assert merged[0].canonical_concept == "Transaction"

    def test_case_insensitive_key(self):
        existing = parse_mapping_rows(_header(), [_row(source_system="POS")])
        new = parse_mapping_rows(_header(), [_row(source_system="pos", notes="new")])
        merged, report = merge_mappings(existing, new)
        assert len(merged) == 1
        assert report.updated == ["POS.transactions.txn_id"]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def _write_workspace(tmp_path, concepts=None) -> str:
    workspace = tmp_path / "ontology"
    (workspace / "02_concepts").mkdir(parents=True)
    (workspace / "03_mappings").mkdir(parents=True)
    if concepts is None:
        concepts = [{
            "name": "Transaction",
            "domain": "payments",
            "description": "A single transfer of funds — long enough description.",
            "source_quotes": [{"quote": "q", "source": "Alice", "date": "2026-04-12"}],
        }]
    (workspace / "02_concepts" / "candidate-concepts.yaml").write_text(yaml.safe_dump(concepts))
    return str(workspace)


class TestIngestMappings:
    def test_fresh_ingest(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.csv"
        with open(fixture, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=_header())
            w.writeheader()
            w.writerow(_row())
        result = ingest_mappings(
            workspace_path=workspace, fixture_path=str(fixture),
            session="s", interviewer="al", at=_fixed_at(),
        )
        assert isinstance(result, IngestResult)
        assert result.added == ["pos.transactions.txn_id"]
        assert os.path.isfile(os.path.join(workspace, "03_mappings", "source-to-canonical.csv"))

    def test_lint_warnings_written(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.csv"
        with open(fixture, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=_header())
            w.writeheader()
            w.writerow(_row(canonical_concept="Ghost"))  # unknown_canonical_concept
            w.writerow(_row(
                source_field="customer_ref",
                canonical_concept="", canonical_property="",
                mapping_type="ambiguous", confidence="low", notes="",
            ))  # both low_confidence_without_notes AND ambiguous_without_notes
        result = ingest_mappings(
            workspace_path=workspace, fixture_path=str(fixture),
            session="s", interviewer="al", at=_fixed_at(),
        )
        rules = {w.rule for w in result.warnings}
        assert "unknown_canonical_concept" in rules
        assert "low_confidence_without_notes" in rules
        assert "ambiguous_without_notes" in rules
        text = open(os.path.join(workspace, "ingest-warnings.md")).read()
        assert "mapping(s)" in text

    def test_schema_error_writes_nothing(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.csv"
        with open(fixture, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=_header())
            w.writeheader()
            w.writerow(_row(mapping_type="magical"))
        with pytest.raises(SchemaError):
            ingest_mappings(workspace_path=workspace, fixture_path=str(fixture),
                            session="s", interviewer="al", at=_fixed_at())
