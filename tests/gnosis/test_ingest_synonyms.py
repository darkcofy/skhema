"""Tests for gnosis.ingest_synonyms — schema, lint, merge, render, orchestration."""
from __future__ import annotations

import datetime as _dt
import os

import pytest
import yaml

from gnosis.ingest import SchemaError
from gnosis.ingest_synonyms import (
    IngestResult,
    backup_pre_ingest_md,
    ingest_synonyms,
    lint_insufficient_evidence,
    lint_proposed_canonical_not_in_terms,
    lint_unknown_speaker_in_evidence,
    merge_conflicts,
    parse_conflicts,
    render_conflicts_markdown,
    run_lints,
)


def _fixed_at() -> _dt.datetime:
    return _dt.datetime(2026, 5, 9, 10, 0, 0, tzinfo=_dt.timezone.utc)


def _minimal(**overrides) -> dict:
    entry = {
        "title": "Customer / Account Holder",
        "type": "near-synonym",
        "severity": "high",
        "terms": ["customer", "account holder"],
        "evidence": [
            {"quote": "Every order has a customer", "source": "Alice Chen",
             "date": "2026-04-12", "polarity": "same"},
            {"quote": "KYC targets the account holder", "source": "Carol Singh",
             "date": "2026-04-13", "polarity": "different"},
        ],
    }
    entry.update(overrides)
    return entry


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class TestParseConflicts:
    def test_minimal_valid(self):
        entries = parse_conflicts([_minimal()])
        assert len(entries) == 1
        assert entries[0].type == "near-synonym"
        assert entries[0].severity == "high"
        assert len(entries[0].evidence) == 2

    def test_full_valid(self):
        entries = parse_conflicts([_minimal(
            used_by=[
                {"term": "customer", "speakers": ["Alice Chen"]},
                {"term": "account holder", "speakers": ["Carol Singh"]},
            ],
            proposed_canonical="customer",
            rationale="Highest usage count.",
            open_questions=["Corporate cards?"],
        )])
        e = entries[0]
        assert e.proposed_canonical == "customer"
        assert e.rationale == "Highest usage count."
        assert e.open_questions == ["Corporate cards?"]
        assert len(e.used_by) == 2

    def test_missing_title(self):
        bad = _minimal()
        del bad["title"]
        with pytest.raises(SchemaError) as exc:
            parse_conflicts([bad])
        assert any("'title' is required" in i for i in exc.value.issues)

    def test_invalid_type(self):
        with pytest.raises(SchemaError) as exc:
            parse_conflicts([_minimal(type="synonyms")])  # missing singular form
        assert any("'type'" in i for i in exc.value.issues)

    def test_invalid_severity(self):
        with pytest.raises(SchemaError) as exc:
            parse_conflicts([_minimal(severity="critical")])
        assert any("'severity'" in i for i in exc.value.issues)

    def test_invalid_polarity(self):
        bad = _minimal()
        bad["evidence"][0]["polarity"] = "neutral"
        with pytest.raises(SchemaError):
            parse_conflicts([bad])

    def test_missing_date(self):
        bad = _minimal()
        del bad["evidence"][0]["date"]
        with pytest.raises(SchemaError) as exc:
            parse_conflicts([bad])
        assert any("'date'" in i for i in exc.value.issues)

    def test_duplicate_title(self):
        with pytest.raises(SchemaError) as exc:
            parse_conflicts([_minimal(), _minimal()])
        assert any("duplicate title" in i for i in exc.value.issues)

    def test_empty_terms(self):
        with pytest.raises(SchemaError):
            parse_conflicts([_minimal(terms=[])])


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------

class TestLintInsufficientEvidence:
    def test_one_source_flagged(self):
        entries = parse_conflicts([_minimal(evidence=[
            {"quote": "q", "source": "Alice Chen", "date": "2026-04-12", "polarity": "same"},
        ])])
        warnings = lint_insufficient_evidence(entries)
        assert len(warnings) == 1
        assert warnings[0].rule == "insufficient_evidence"

    def test_same_source_twice_flagged(self):
        entries = parse_conflicts([_minimal(evidence=[
            {"quote": "q1", "source": "Alice Chen", "date": "2026-04-12", "polarity": "same"},
            {"quote": "q2", "source": "Alice Chen", "date": "2026-04-13", "polarity": "same"},
        ])])
        warnings = lint_insufficient_evidence(entries)
        assert len(warnings) == 1  # still only one distinct source

    def test_two_sources_passes(self):
        entries = parse_conflicts([_minimal()])
        assert lint_insufficient_evidence(entries) == []


class TestLintUnknownSpeakerInEvidence:
    def test_unknown_flagged(self):
        entries = parse_conflicts([_minimal(evidence=[
            {"quote": "q1", "source": "Nina Patel", "date": "2026-04-12", "polarity": "same"},
            {"quote": "q2", "source": "Alice Chen", "date": "2026-04-13", "polarity": "same"},
        ])])
        warnings = lint_unknown_speaker_in_evidence(entries, {"alice chen"})
        assert len(warnings) == 1
        assert "Nina Patel" in warnings[0].message

    def test_team_source_skipped(self):
        entries = parse_conflicts([_minimal(evidence=[
            {"quote": "q1", "source": "Platform Team", "date": "2026-04-12", "polarity": "same"},
            {"quote": "q2", "source": "Alice Chen", "date": "2026-04-13", "polarity": "same"},
        ])])
        warnings = lint_unknown_speaker_in_evidence(entries, {"alice chen"})
        assert warnings == []

    def test_all_known_passes(self):
        entries = parse_conflicts([_minimal()])
        assert lint_unknown_speaker_in_evidence(entries, {"alice chen", "carol singh"}) == []


class TestLintProposedCanonicalNotInTerms:
    def test_flagged_when_not_in_terms(self):
        entries = parse_conflicts([_minimal(proposed_canonical="buyer")])
        warnings = lint_proposed_canonical_not_in_terms(entries)
        assert len(warnings) == 1
        assert warnings[0].rule == "proposed_canonical_not_in_terms"

    def test_passes_when_in_terms(self):
        entries = parse_conflicts([_minimal(proposed_canonical="customer")])
        assert lint_proposed_canonical_not_in_terms(entries) == []

    def test_case_insensitive_match(self):
        entries = parse_conflicts([_minimal(proposed_canonical="CUSTOMER")])
        assert lint_proposed_canonical_not_in_terms(entries) == []

    def test_no_proposal_skipped(self):
        entries = parse_conflicts([_minimal()])
        assert lint_proposed_canonical_not_in_terms(entries) == []


class TestRunLints:
    def test_combined(self):
        entries = parse_conflicts([
            _minimal(title="A", evidence=[
                {"quote": "q", "source": "Alice Chen", "date": "2026-04-12", "polarity": "same"},
            ]),  # insufficient
            _minimal(title="B", proposed_canonical="buyer"),  # not in terms
        ])
        warnings = run_lints(entries, {"alice chen", "carol singh"})
        rules = {w.rule for w in warnings}
        assert "insufficient_evidence" in rules
        assert "proposed_canonical_not_in_terms" in rules


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

class TestMergeConflicts:
    def test_new_added(self):
        new = parse_conflicts([_minimal()])
        merged, report = merge_conflicts([], new, session="s", interviewer="al", at=_fixed_at())
        assert len(merged) == 1
        assert report.added == ["Customer / Account Holder"]

    def test_existing_updated_unions_evidence(self):
        existing = parse_conflicts([_minimal()])
        new = parse_conflicts([_minimal(evidence=[
            {"quote": "NEW quote", "source": "Bob Murphy", "date": "2026-04-14", "polarity": "same"},
        ])])
        merged, report = merge_conflicts(existing, new, session="s", interviewer="al", at=_fixed_at())
        quotes = [q.quote for q in merged[0].evidence]
        assert "NEW quote" in quotes
        assert "Every order has a customer" in quotes  # existing preserved
        assert report.updated == ["Customer / Account Holder"]

    def test_case_insensitive_title_match(self):
        existing = parse_conflicts([_minimal(title="Customer / Account Holder")])
        new = parse_conflicts([_minimal(title="customer / account holder")])
        merged, report = merge_conflicts(existing, new, session="s", interviewer="al", at=_fixed_at())
        assert len(merged) == 1
        assert report.updated == ["Customer / Account Holder"]

    def test_used_by_speakers_unioned(self):
        existing = parse_conflicts([_minimal(used_by=[
            {"term": "customer", "speakers": ["Alice Chen"]},
        ])])
        new = parse_conflicts([_minimal(used_by=[
            {"term": "customer", "speakers": ["Bob Murphy"]},
        ])])
        merged, _ = merge_conflicts(existing, new, session="s", interviewer="al", at=_fixed_at())
        speakers = merged[0].used_by[0].speakers
        assert "Alice Chen" in speakers
        assert "Bob Murphy" in speakers

    def test_provenance_stamped(self):
        new = parse_conflicts([_minimal()])
        merged, _ = merge_conflicts([], new, session="s1", interviewer="al", at=_fixed_at())
        assert merged[0].last_ingested == {
            "session": "s1",
            "interviewer": "al",
            "at": "2026-05-09T10:00:00+00:00",
        }


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

class TestRenderConflictsMarkdown:
    def test_empty_state(self):
        md = render_conflicts_markdown([])
        assert "No conflicts recorded yet" in md
        assert md.startswith("# Terminology synonyms and conflicts")

    def test_renders_type_heading(self):
        entries = parse_conflicts([_minimal()])
        md = render_conflicts_markdown(entries)
        assert "## Near-synonym: Customer / Account Holder" in md

    def test_groups_evidence_by_polarity(self):
        entries = parse_conflicts([_minimal()])
        md = render_conflicts_markdown(entries)
        assert "**Evidence of same meaning:**" in md
        assert "**Evidence of different meaning:**" in md

    def test_includes_proposed_canonical_with_rationale(self):
        entries = parse_conflicts([_minimal(
            proposed_canonical="customer",
            rationale="Highest usage count.",
        )])
        md = render_conflicts_markdown(entries)
        assert "**Proposed canonical:** customer — Highest usage count." in md


# ---------------------------------------------------------------------------
# Pre-ingest backup
# ---------------------------------------------------------------------------

class TestBackupPreIngestMd:
    def test_backs_up_when_md_only(self, tmp_path):
        md = tmp_path / "synonym-conflicts.md"
        md.write_text("hand-authored content")
        backup = backup_pre_ingest_md(str(md), str(tmp_path / "synonym-conflicts.yaml"))
        assert backup is not None
        assert not md.exists()
        assert os.path.isfile(backup)

    def test_no_backup_when_yaml_exists(self, tmp_path):
        md = tmp_path / "synonym-conflicts.md"
        yaml_path = tmp_path / "synonym-conflicts.yaml"
        md.write_text("content")
        yaml_path.write_text("[]")
        backup = backup_pre_ingest_md(str(md), str(yaml_path))
        assert backup is None
        assert md.exists()  # untouched

    def test_idempotent_when_backup_exists(self, tmp_path):
        md = tmp_path / "synonym-conflicts.md"
        md.write_text("content")
        pre = tmp_path / "synonym-conflicts.md.pre-ingest"
        pre.write_text("previous backup")
        backup = backup_pre_ingest_md(str(md), str(tmp_path / "synonym-conflicts.yaml"))
        assert backup is None
        # Both files should still exist (first backup wasn't overwritten)
        assert md.exists()
        assert pre.exists()

    def test_no_backup_when_no_md(self, tmp_path):
        backup = backup_pre_ingest_md(
            str(tmp_path / "does-not-exist.md"),
            str(tmp_path / "does-not-exist.yaml"),
        )
        assert backup is None


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def _write_workspace(tmp_path, stakeholders=None, existing_md: str | None = None) -> str:
    workspace = tmp_path / "ontology"
    (workspace / "00_scope").mkdir(parents=True)
    (workspace / "01_language").mkdir(parents=True)
    if stakeholders is None:
        stakeholders = [
            {"name": "Alice Chen", "role": "Lead"},
            {"name": "Carol Singh", "role": "Domain Lead"},
        ]
    (workspace / "00_scope" / "stakeholders.yaml").write_text(yaml.safe_dump(stakeholders))
    if existing_md is not None:
        (workspace / "01_language" / "synonym-conflicts.md").write_text(existing_md)
    return str(workspace)


class TestIngestSynonyms:
    def test_fresh_ingest_writes_yaml_and_md(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.yaml"
        fixture.write_text(yaml.safe_dump([_minimal()]))
        result = ingest_synonyms(
            workspace_path=workspace, fixture_path=str(fixture),
            session="s", interviewer="al", at=_fixed_at(),
        )
        assert isinstance(result, IngestResult)
        assert os.path.isfile(result.yaml_path)
        assert os.path.isfile(result.md_path)
        assert result.added == ["Customer / Account Holder"]

    def test_backs_up_hand_authored_md_on_first_ingest(self, tmp_path):
        workspace = _write_workspace(tmp_path, existing_md="# Hand-authored content\n")
        fixture = tmp_path / "f.yaml"
        fixture.write_text(yaml.safe_dump([_minimal()]))
        result = ingest_synonyms(
            workspace_path=workspace, fixture_path=str(fixture),
            session="s", interviewer="al", at=_fixed_at(),
        )
        assert result.backup_path is not None
        backup_contents = open(result.backup_path).read()
        assert "Hand-authored content" in backup_contents

    def test_no_backup_on_subsequent_ingest(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.yaml"
        fixture.write_text(yaml.safe_dump([_minimal()]))
        # First ingest creates the .yaml
        ingest_synonyms(workspace_path=workspace, fixture_path=str(fixture),
                        session="s1", interviewer="al", at=_fixed_at())
        # Second ingest — .yaml exists, so no backup should happen
        result = ingest_synonyms(workspace_path=workspace, fixture_path=str(fixture),
                                 session="s2", interviewer="al", at=_fixed_at())
        assert result.backup_path is None

    def test_lint_warnings_written(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.yaml"
        # Single-source evidence triggers insufficient_evidence
        fixture.write_text(yaml.safe_dump([_minimal(evidence=[
            {"quote": "q", "source": "Alice Chen", "date": "2026-04-12", "polarity": "same"},
        ])]))
        result = ingest_synonyms(
            workspace_path=workspace, fixture_path=str(fixture),
            session="s", interviewer="al", at=_fixed_at(),
        )
        rules = {w.rule for w in result.warnings}
        assert "insufficient_evidence" in rules
        assert "conflict(s)" in open(os.path.join(workspace, "ingest-warnings.md")).read()

    def test_schema_error_writes_nothing(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.yaml"
        bad = _minimal(severity="apocalyptic")
        fixture.write_text(yaml.safe_dump([bad]))
        with pytest.raises(SchemaError):
            ingest_synonyms(workspace_path=workspace, fixture_path=str(fixture),
                            session="s", interviewer="al", at=_fixed_at())
        assert not os.path.isfile(os.path.join(workspace, "01_language", "synonym-conflicts.yaml"))
