"""Tests for gnosis.ingest_stakeholders — schema, lint, merge, orchestration."""
from __future__ import annotations

import datetime as _dt
import os

import pytest
import yaml

from gnosis.ingest import SchemaError
from gnosis.ingest_stakeholders import (
    IngestResult,
    StakeholderEntry,
    _is_tbd,
    _merge_key,
    ingest_stakeholders,
    lint_missing_decision_rights_on_high_influence,
    lint_tbd_without_notes,
    merge_stakeholders,
    parse_stakeholders,
    run_lints,
)


def _minimal(**overrides) -> dict:
    entry = {"name": "Alice Chen", "role": "Head of Data Platform"}
    entry.update(overrides)
    return entry


def _fixed_at() -> _dt.datetime:
    return _dt.datetime(2026, 5, 7, 10, 0, 0, tzinfo=_dt.timezone.utc)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class TestParseStakeholders:
    def test_minimal_valid(self):
        entries = parse_stakeholders([_minimal()])
        assert entries[0].name == "Alice Chen"
        assert entries[0].role == "Head of Data Platform"

    def test_full_valid(self):
        entries = parse_stakeholders([
            _minimal(
                team="Engineering · Platform",
                email="alice@meshco.example",
                interests=["Mesh migration"],
                decision_rights=["Platform architecture"],
                influence="high",
                engagement_cadence="weekly",
                notes="Sponsor.",
            )
        ])
        e = entries[0]
        assert e.team == "Engineering · Platform"
        assert e.email == "alice@meshco.example"
        assert e.interests == ["Mesh migration"]
        assert e.influence == "high"

    def test_missing_name(self):
        with pytest.raises(SchemaError) as exc:
            parse_stakeholders([{"role": "X"}])
        assert any("'name' is required" in i for i in exc.value.issues)

    def test_missing_role(self):
        with pytest.raises(SchemaError) as exc:
            parse_stakeholders([{"name": "Alice"}])
        assert any("'role' is required" in i for i in exc.value.issues)

    def test_invalid_influence(self):
        with pytest.raises(SchemaError) as exc:
            parse_stakeholders([_minimal(influence="god-tier")])
        assert any("influence" in i for i in exc.value.issues)

    def test_invalid_email(self):
        with pytest.raises(SchemaError) as exc:
            parse_stakeholders([_minimal(email="not-an-email")])
        assert any("email" in i for i in exc.value.issues)

    def test_influence_normalised_lowercase(self):
        entries = parse_stakeholders([_minimal(influence="HIGH")])
        assert entries[0].influence == "high"

    def test_top_level_not_list(self):
        with pytest.raises(SchemaError):
            parse_stakeholders("not-a-list")


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------

class TestLintMissingDecisionRightsOnHighInfluence:
    def test_flags_high_without_rights(self):
        entries = parse_stakeholders([_minimal(influence="high")])
        warnings = lint_missing_decision_rights_on_high_influence(entries)
        assert len(warnings) == 1
        assert warnings[0].rule == "missing_decision_rights_on_high_influence"
        assert warnings[0].concept == "Alice Chen"

    def test_high_with_rights_passes(self):
        entries = parse_stakeholders([
            _minimal(influence="high", decision_rights=["Budget approval"])
        ])
        assert lint_missing_decision_rights_on_high_influence(entries) == []

    def test_medium_without_rights_passes(self):
        entries = parse_stakeholders([_minimal(influence="medium")])
        assert lint_missing_decision_rights_on_high_influence(entries) == []

    def test_no_influence_set_passes(self):
        entries = parse_stakeholders([_minimal()])
        assert lint_missing_decision_rights_on_high_influence(entries) == []


class TestLintTbdWithoutNotes:
    def test_flags_tbd_without_notes(self):
        entries = parse_stakeholders([{"name": "TBD", "role": "Compliance Lead"}])
        warnings = lint_tbd_without_notes(entries)
        assert len(warnings) == 1
        assert warnings[0].rule == "tbd_without_notes"
        assert "Compliance Lead" in warnings[0].concept

    def test_tbd_with_notes_passes(self):
        entries = parse_stakeholders([
            {"name": "TBD", "role": "Compliance Lead", "notes": "Ask Alice for intro."}
        ])
        assert lint_tbd_without_notes(entries) == []

    def test_named_without_notes_passes(self):
        entries = parse_stakeholders([_minimal()])
        assert lint_tbd_without_notes(entries) == []


class TestRunLints:
    def test_combined(self):
        entries = parse_stakeholders([
            _minimal(influence="high"),                            # flags one rule
            {"name": "TBD", "role": "Compliance Lead"},            # flags the other
        ])
        warnings = run_lints(entries)
        rules = {w.rule for w in warnings}
        assert "missing_decision_rights_on_high_influence" in rules
        assert "tbd_without_notes" in rules


# ---------------------------------------------------------------------------
# Merge key / is_tbd
# ---------------------------------------------------------------------------

class TestMergeKey:
    def test_named_key_normalised(self):
        s = StakeholderEntry(name="Alice Chen (Lead)", role="Lead")
        k = _merge_key(s)
        assert k[0] == "__named__"
        assert k[1] == "alice chen"

    def test_tbd_key_compound(self):
        s1 = StakeholderEntry(name="TBD", role="ML Lead", team="Eng")
        s2 = StakeholderEntry(name="TBD", role="Compliance Lead", team="Legal")
        assert _merge_key(s1) != _merge_key(s2)

    def test_is_tbd_case_insensitive(self):
        assert _is_tbd("tbd")
        assert _is_tbd("TBD")
        assert not _is_tbd("Alice")


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

class TestMergeStakeholders:
    def test_new_appended_with_provenance(self):
        new = parse_stakeholders([_minimal()])
        merged, report = merge_stakeholders([], new, session="s", interviewer="al", at=_fixed_at())
        assert len(merged) == 1
        assert report.added == ["Alice Chen"]
        assert merged[0].last_ingested["session"] == "s"

    def test_existing_updated_unions_interests(self):
        existing = parse_stakeholders([_minimal(interests=["A"])])
        new = parse_stakeholders([_minimal(interests=["B"])])
        merged, report = merge_stakeholders(existing, new, session="s", interviewer="al", at=_fixed_at())
        assert merged[0].interests == ["A", "B"]
        assert report.updated == ["Alice Chen"]

    def test_existing_scalar_overwritten(self):
        existing = parse_stakeholders([_minimal(role="Old Role", influence="medium")])
        new = parse_stakeholders([_minimal(role="New Role", influence="high")])
        merged, _ = merge_stakeholders(existing, new, session="s", interviewer="al", at=_fixed_at())
        assert merged[0].role == "New Role"
        assert merged[0].influence == "high"

    def test_multiple_tbds_coexist(self):
        existing = parse_stakeholders([
            {"name": "TBD", "role": "ML Lead", "notes": "n"},
        ])
        new = parse_stakeholders([
            {"name": "TBD", "role": "Compliance Lead", "notes": "n"},
        ])
        merged, report = merge_stakeholders(existing, new, session="s", interviewer="al", at=_fixed_at())
        assert len(merged) == 2
        assert report.added == ["TBD"]

    def test_case_insensitive_name_match(self):
        existing = parse_stakeholders([_minimal(name="Alice Chen")])
        new = parse_stakeholders([_minimal(name="alice chen")])
        merged, report = merge_stakeholders(existing, new, session="s", interviewer="al", at=_fixed_at())
        assert len(merged) == 1
        assert report.updated == ["Alice Chen"]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def _write_workspace(tmp_path, stakeholders: list[dict] | None = None) -> str:
    workspace = tmp_path / "ontology"
    (workspace / "00_scope").mkdir(parents=True)
    if stakeholders is not None:
        (workspace / "00_scope" / "stakeholders.yaml").write_text(yaml.safe_dump(stakeholders))
    return str(workspace)


class TestIngestStakeholders:
    def test_fresh_ingest(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.yaml"
        fixture.write_text(yaml.safe_dump([_minimal()]))
        result = ingest_stakeholders(
            workspace_path=workspace, fixture_path=str(fixture),
            session="s", interviewer="al", at=_fixed_at(),
        )
        assert isinstance(result, IngestResult)
        assert result.added == ["Alice Chen"]
        assert os.path.isfile(os.path.join(workspace, "00_scope", "stakeholders.yaml"))
        assert os.path.isfile(os.path.join(workspace, "ingest-warnings.md"))

    def test_merge_with_existing(self, tmp_path):
        workspace = _write_workspace(tmp_path, stakeholders=[_minimal(interests=["A"])])
        fixture = tmp_path / "f.yaml"
        fixture.write_text(yaml.safe_dump([_minimal(interests=["B"])]))
        result = ingest_stakeholders(
            workspace_path=workspace, fixture_path=str(fixture),
            session="s", interviewer="al", at=_fixed_at(),
        )
        assert result.updated == ["Alice Chen"]
        data = yaml.safe_load(open(os.path.join(workspace, "00_scope", "stakeholders.yaml")).read())
        assert data[0]["interests"] == ["A", "B"]

    def test_warnings_written(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.yaml"
        fixture.write_text(yaml.safe_dump([
            _minimal(influence="high"),  # triggers one lint rule
        ]))
        ingest_stakeholders(
            workspace_path=workspace, fixture_path=str(fixture),
            session="s", interviewer="al", at=_fixed_at(),
        )
        text = open(os.path.join(workspace, "ingest-warnings.md")).read()
        assert "High-influence stakeholders missing decision_rights" in text
        assert "stakeholder(s)" in text  # item_kind footer

    def test_schema_error_writes_nothing(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.yaml"
        fixture.write_text(yaml.safe_dump([{"name": "Alice"}]))  # missing role
        with pytest.raises(SchemaError):
            ingest_stakeholders(
                workspace_path=workspace, fixture_path=str(fixture),
                session="s", interviewer="al", at=_fixed_at(),
            )
        assert not os.path.isfile(os.path.join(workspace, "00_scope", "stakeholders.yaml"))
