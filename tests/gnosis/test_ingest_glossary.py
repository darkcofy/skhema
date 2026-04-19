"""Tests for gnosis.ingest_glossary — schema, lint, merge, orchestration."""
from __future__ import annotations

import csv
import datetime as _dt
import os

import pytest
import yaml

from gnosis.ingest import SchemaError
from gnosis.ingest_glossary import (
    GlossaryEntry,
    IngestResult,
    ingest_glossary,
    lint_missing_definition_without_flag,
    lint_unknown_speaker_in_source,
    load_glossary_csv,
    merge_glossary,
    parse_glossary_rows,
    source_speaker_candidate,
    write_glossary_csv,
)


def _fixed_at() -> _dt.datetime:
    return _dt.datetime(2026, 5, 8, 10, 0, 0, tzinfo=_dt.timezone.utc)


def _header() -> list[str]:
    return ["term", "definition", "source", "domain", "aliases", "notes"]


def _row(**overrides) -> dict:
    r = {
        "term": "Transaction",
        "definition": "A single transfer of funds against a payment method.",
        "source": "2026-04-12 Alice Chen",
        "domain": "payments",
        "aliases": "txn, tx",
        "notes": "",
    }
    r.update(overrides)
    return r


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class TestParseGlossaryRows:
    def test_minimal_valid(self):
        entries = parse_glossary_rows(["term", "definition", "source"], [
            {"term": "Transaction", "definition": "A transfer of funds", "source": "Alice"},
        ])
        assert len(entries) == 1
        assert entries[0].term == "Transaction"

    def test_full_valid(self):
        entries = parse_glossary_rows(_header(), [_row()])
        e = entries[0]
        assert e.aliases == ["txn", "tx"]
        assert e.domain == "payments"

    def test_missing_required_column(self):
        with pytest.raises(SchemaError) as exc:
            parse_glossary_rows(["term", "definition"], [])
        assert any("missing required column" in i for i in exc.value.issues)

    def test_unknown_column_rejected(self):
        with pytest.raises(SchemaError) as exc:
            parse_glossary_rows(["term", "definition", "source", "colour"], [])
        assert any("unknown column" in i for i in exc.value.issues)

    def test_empty_term_rejected(self):
        with pytest.raises(SchemaError) as exc:
            parse_glossary_rows(_header(), [_row(term="")])
        assert any("'term' is required" in i for i in exc.value.issues)

    def test_empty_source_rejected(self):
        with pytest.raises(SchemaError) as exc:
            parse_glossary_rows(_header(), [_row(source="")])
        assert any("'source' is required" in i for i in exc.value.issues)

    def test_empty_definition_allowed(self):
        entries = parse_glossary_rows(_header(), [_row(definition="")])
        assert entries[0].definition == ""

    def test_duplicate_term_rejected(self):
        with pytest.raises(SchemaError) as exc:
            parse_glossary_rows(_header(), [_row(), _row(term="transaction")])
        assert any("duplicate" in i for i in exc.value.issues)


# ---------------------------------------------------------------------------
# Source speaker parser
# ---------------------------------------------------------------------------

class TestSourceSpeakerCandidate:
    def test_person_name_extracted(self):
        assert source_speaker_candidate("2026-04-12 Alice Chen") == "Alice Chen"

    def test_bare_person_name(self):
        assert source_speaker_candidate("Alice Chen") == "Alice Chen"

    def test_team_skipped(self):
        assert source_speaker_candidate("2026-04-16 Platform Team") is None

    def test_council_skipped(self):
        assert source_speaker_candidate("2026-04-16 Data Council kickoff") is None

    def test_workshop_skipped(self):
        assert source_speaker_candidate("2026-04-16 Architecture Workshop") is None

    def test_unstructured_skipped(self):
        assert source_speaker_candidate("from a slack thread last week") is None


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------

class TestLintMissingDefinitionWithoutFlag:
    def test_empty_definition_no_notes_flagged(self):
        entries = parse_glossary_rows(_header(), [_row(definition="", notes="")])
        warnings = lint_missing_definition_without_flag(entries)
        assert len(warnings) == 1
        assert warnings[0].rule == "missing_definition_without_flag"

    def test_empty_definition_with_clarification_note_passes(self):
        entries = parse_glossary_rows(_header(), [
            _row(definition="", notes="Needs clarification from Alice"),
        ])
        assert lint_missing_definition_without_flag(entries) == []

    def test_empty_definition_with_tbd_note_passes(self):
        entries = parse_glossary_rows(_header(), [_row(definition="", notes="TBD")])
        assert lint_missing_definition_without_flag(entries) == []

    def test_full_definition_passes(self):
        entries = parse_glossary_rows(_header(), [_row()])
        assert lint_missing_definition_without_flag(entries) == []


class TestLintUnknownSpeakerInSource:
    def test_unknown_speaker_flagged(self):
        entries = parse_glossary_rows(_header(), [_row(source="2026-05-05 Nina Patel")])
        warnings = lint_unknown_speaker_in_source(entries, {"alice chen", "bob murphy"})
        assert len(warnings) == 1
        assert warnings[0].rule == "unknown_speaker_in_source"
        assert "Nina Patel" in warnings[0].message

    def test_known_speaker_passes(self):
        entries = parse_glossary_rows(_header(), [_row(source="2026-04-12 Alice Chen")])
        assert lint_unknown_speaker_in_source(entries, {"alice chen"}) == []

    def test_team_source_skipped(self):
        entries = parse_glossary_rows(_header(), [_row(source="2026-04-16 Platform Team")])
        # Even with empty known_speakers, team-source should not fire.
        assert lint_unknown_speaker_in_source(entries, set()) == []


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

class TestMergeGlossary:
    def test_new_term_added(self):
        new = parse_glossary_rows(_header(), [_row()])
        merged, report = merge_glossary([], new)
        assert merged[0].term == "Transaction"
        assert report.added == ["Transaction"]

    def test_existing_term_with_new_aliases_updated(self):
        existing = parse_glossary_rows(_header(), [_row(aliases="txn")])
        new = parse_glossary_rows(_header(), [_row(aliases="tx")])
        merged, report = merge_glossary(existing, new)
        assert merged[0].aliases == ["txn", "tx"]
        assert report.updated == ["Transaction"]
        assert report.skipped == []

    def test_existing_term_no_new_aliases_skipped(self):
        existing = parse_glossary_rows(_header(), [_row()])
        new = parse_glossary_rows(_header(), [_row()])  # identical
        merged, report = merge_glossary(existing, new)
        assert report.skipped == ["Transaction"]
        assert report.updated == []

    def test_definition_not_clobbered(self):
        existing = parse_glossary_rows(_header(), [
            _row(definition="Curated definition."),
        ])
        new = parse_glossary_rows(_header(), [
            _row(definition="A totally different LLM take on it.", aliases="other-alias"),
        ])
        merged, _ = merge_glossary(existing, new)
        assert merged[0].definition == "Curated definition."
        assert "other-alias" in merged[0].aliases

    def test_source_not_clobbered(self):
        existing = parse_glossary_rows(_header(), [
            _row(source="2026-04-01 Original Author"),
        ])
        new = parse_glossary_rows(_header(), [
            _row(source="2026-05-08 New Author", aliases="new"),
        ])
        merged, _ = merge_glossary(existing, new)
        assert merged[0].source == "2026-04-01 Original Author"

    def test_case_insensitive_term_match(self):
        existing = parse_glossary_rows(_header(), [_row(term="Transaction")])
        new = parse_glossary_rows(_header(), [_row(term="transaction", aliases="new-alias")])
        merged, report = merge_glossary(existing, new)
        assert len(merged) == 1
        assert "Transaction" in report.updated


# ---------------------------------------------------------------------------
# CSV round-trip
# ---------------------------------------------------------------------------

class TestCsvRoundTrip:
    def test_write_then_read(self, tmp_path):
        entries = [
            GlossaryEntry(term="Transaction", definition="A transfer", source="Alice",
                          domain="payments", aliases=["txn", "tx"], notes="note"),
        ]
        path = tmp_path / "glossary.csv"
        write_glossary_csv(entries, str(path))
        loaded = load_glossary_csv(str(path))
        assert loaded[0].term == "Transaction"
        assert loaded[0].aliases == ["txn", "tx"]
        assert loaded[0].notes == "note"

    def test_header_order_stable(self, tmp_path):
        entries = [GlossaryEntry(term="T", definition="d", source="s")]
        path = tmp_path / "g.csv"
        write_glossary_csv(entries, str(path))
        with open(path) as f:
            header = csv.DictReader(f).fieldnames
        assert header == ["term", "definition", "source", "domain", "aliases", "notes"]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def _write_workspace(tmp_path, stakeholders=None, existing_glossary=None) -> str:
    workspace = tmp_path / "ontology"
    (workspace / "00_scope").mkdir(parents=True)
    (workspace / "01_language").mkdir(parents=True)
    if stakeholders is None:
        stakeholders = [{"name": "Alice Chen", "role": "Lead"}]
    (workspace / "00_scope" / "stakeholders.yaml").write_text(yaml.safe_dump(stakeholders))
    if existing_glossary is not None:
        path = workspace / "01_language" / "glossary-seeds.csv"
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=_header())
            w.writeheader()
            for row in existing_glossary:
                full = {k: "" for k in _header()}
                full.update(row)
                w.writerow(full)
    return str(workspace)


class TestIngestGlossary:
    def test_fresh_ingest(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.csv"
        with open(fixture, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=_header())
            w.writeheader()
            w.writerow(_row())
        result = ingest_glossary(
            workspace_path=workspace, fixture_path=str(fixture),
            session="s", interviewer="al", at=_fixed_at(),
        )
        assert isinstance(result, IngestResult)
        assert result.added == ["Transaction"]
        assert os.path.isfile(os.path.join(workspace, "01_language", "glossary-seeds.csv"))
        assert os.path.isfile(os.path.join(workspace, "ingest-warnings.md"))

    def test_warnings_written(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.csv"
        with open(fixture, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=_header())
            w.writeheader()
            w.writerow(_row(definition="", notes=""))  # missing_definition_without_flag
            w.writerow(_row(term="Cube", source="2026-05-05 Nina Patel"))  # unknown_speaker
        result = ingest_glossary(
            workspace_path=workspace, fixture_path=str(fixture),
            session="s", interviewer="al", at=_fixed_at(),
        )
        rules = {w.rule for w in result.warnings}
        assert "missing_definition_without_flag" in rules
        assert "unknown_speaker_in_source" in rules
        assert "term(s)" in open(os.path.join(workspace, "ingest-warnings.md")).read()

    def test_schema_error_writes_nothing(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.csv"
        with open(fixture, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["term", "definition"])  # missing source
            w.writeheader()
            w.writerow({"term": "X", "definition": "y"})
        with pytest.raises(SchemaError):
            ingest_glossary(
                workspace_path=workspace, fixture_path=str(fixture),
                session="s", interviewer="al", at=_fixed_at(),
            )
        assert not os.path.isfile(os.path.join(workspace, "01_language", "glossary-seeds.csv"))

    def test_existing_term_not_clobbered(self, tmp_path):
        workspace = _write_workspace(
            tmp_path,
            existing_glossary=[{
                "term": "Transaction",
                "definition": "Curated definition.",
                "source": "2026-04-01 Original",
                "domain": "payments",
                "aliases": "txn",
                "notes": "",
            }],
        )
        fixture = tmp_path / "f.csv"
        with open(fixture, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=_header())
            w.writeheader()
            w.writerow(_row(definition="LLM reworded take.", source="2026-05-08 Alice Chen", aliases="tx"))
        result = ingest_glossary(
            workspace_path=workspace, fixture_path=str(fixture),
            session="s", interviewer="al", at=_fixed_at(),
        )
        assert result.updated == ["Transaction"]
        assert result.added == []
        with open(os.path.join(workspace, "01_language", "glossary-seeds.csv")) as f:
            rows = list(csv.DictReader(f))
        assert rows[0]["definition"] == "Curated definition."
        assert "tx" in rows[0]["aliases"]
        assert "txn" in rows[0]["aliases"]
