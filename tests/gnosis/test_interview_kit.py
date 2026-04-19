"""Tests for gnosis.interview_kit — deterministic per-stakeholder kit generation."""
from __future__ import annotations

import datetime as _dt
import os

import yaml

from gnosis.interview_kit import (
    _resolve_stakeholder,
    build_kit,
    render_kit,
    write_kit,
)
from gnosis.ingest_stakeholders import StakeholderEntry


def _fixed_at() -> _dt.datetime:
    return _dt.datetime(2026, 5, 12, 10, 0, 0, tzinfo=_dt.timezone.utc)


def _write_workspace(
    tmp_path,
    stakeholders=None,
    concepts=None,
    synonyms=None,
) -> str:
    workspace = tmp_path / "ontology"
    (workspace / "00_scope").mkdir(parents=True)
    (workspace / "01_language").mkdir(parents=True)
    (workspace / "02_concepts").mkdir(parents=True)
    if stakeholders is not None:
        (workspace / "00_scope" / "stakeholders.yaml").write_text(yaml.safe_dump(stakeholders))
    if concepts is not None:
        (workspace / "02_concepts" / "candidate-concepts.yaml").write_text(yaml.safe_dump(concepts))
    if synonyms is not None:
        (workspace / "01_language" / "synonym-conflicts.yaml").write_text(yaml.safe_dump(synonyms))
    return str(workspace)


def _concept(**overrides) -> dict:
    c = {
        "name": "Order",
        "domain": "orders",
        "description": "A customer's purchase intent — 20+ chars for schema.",
        "source_quotes": [{"quote": "q", "source": "Emma Ward", "date": "2026-05-04"}],
    }
    c.update(overrides)
    return c


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

class TestResolveStakeholder:
    def _stakeholders(self):
        return [
            StakeholderEntry(name="Emma Ward", role="Head of Finance"),
            StakeholderEntry(name="Dave Kim", role="Analytics Lead"),
            StakeholderEntry(name="TBD", role="ML Lead"),
        ]

    def test_exact_match(self):
        s = _resolve_stakeholder("Emma Ward", self._stakeholders())
        assert s is not None
        assert s.name == "Emma Ward"

    def test_case_insensitive(self):
        s = _resolve_stakeholder("emma ward", self._stakeholders())
        assert s is not None
        assert s.name == "Emma Ward"

    def test_prefix_unique(self):
        s = _resolve_stakeholder("emma", self._stakeholders())
        assert s is not None
        assert s.name == "Emma Ward"

    def test_no_match(self):
        assert _resolve_stakeholder("Priya", self._stakeholders()) is None

    def test_tbd_not_selectable(self):
        assert _resolve_stakeholder("TBD", self._stakeholders()) is None


# ---------------------------------------------------------------------------
# Section: open questions
# ---------------------------------------------------------------------------

class TestOpenQuestionsSection:
    def test_questions_attributed_to_stakeholder(self, tmp_path):
        workspace = _write_workspace(
            tmp_path,
            concepts=[
                _concept(open_questions=["Is Dan in scope for period boundaries?"]),
                _concept(name="Settlement", source_quotes=[{"quote": "q", "source": "Alice", "date": "2026-04-12"}],
                         open_questions=["Alice-specific question"]),
            ],
        )
        kit = build_kit(workspace, "Emma Ward", at=_fixed_at())
        open_q_section = next(s for s in kit.sections if "Open questions" in s.heading)
        assert len(open_q_section.items) == 1
        assert "Is Dan in scope" in open_q_section.items[0]

    def test_no_questions_empty_note(self, tmp_path):
        workspace = _write_workspace(tmp_path, concepts=[])
        kit = build_kit(workspace, "Emma Ward", at=_fixed_at())
        rendered = render_kit(kit)
        assert "No outstanding questions" in rendered


# ---------------------------------------------------------------------------
# Section: low-confidence concepts
# ---------------------------------------------------------------------------

class TestLowConfidenceSection:
    def test_low_confidence_concept_surfaced(self, tmp_path):
        workspace = _write_workspace(
            tmp_path,
            concepts=[
                _concept(name="FinanceFeed", confidence="low",
                         description="The outbound dataset feeding SAP — historically a service."),
            ],
        )
        kit = build_kit(workspace, "Emma Ward", at=_fixed_at())
        low_conf = next(s for s in kit.sections if "Low-confidence" in s.heading)
        assert any("FinanceFeed" in item for item in low_conf.items)

    def test_high_confidence_concept_skipped(self, tmp_path):
        workspace = _write_workspace(
            tmp_path,
            concepts=[_concept(confidence="high")],
        )
        kit = build_kit(workspace, "Emma Ward", at=_fixed_at())
        low_conf = next(s for s in kit.sections if "Low-confidence" in s.heading)
        assert low_conf.items == []


# ---------------------------------------------------------------------------
# Section: unresolved synonyms
# ---------------------------------------------------------------------------

class TestUnresolvedSynonymsSection:
    def test_unresolved_involving_stakeholder_surfaced(self, tmp_path):
        workspace = _write_workspace(
            tmp_path,
            synonyms=[{
                "title": "Metric / Measure",
                "type": "near-synonym",
                "severity": "high",
                "terms": ["metric", "measure"],
                "used_by": [
                    {"term": "metric", "speakers": ["Dave Kim", "Emma Ward"]},
                ],
                "proposed_canonical": None,
            }],
        )
        kit = build_kit(workspace, "Emma Ward", at=_fixed_at())
        syn = next(s for s in kit.sections if "terminology" in s.heading.lower())
        assert any("Metric / Measure" in item for item in syn.items)

    def test_resolved_skipped(self, tmp_path):
        workspace = _write_workspace(
            tmp_path,
            synonyms=[{
                "title": "Metric / Measure", "type": "near-synonym",
                "severity": "high", "terms": ["metric", "measure"],
                "used_by": [{"term": "metric", "speakers": ["Emma Ward"]}],
                "proposed_canonical": "metric",
            }],
        )
        kit = build_kit(workspace, "Emma Ward", at=_fixed_at())
        syn = next(s for s in kit.sections if "terminology" in s.heading.lower())
        assert syn.items == []

    def test_stakeholder_not_in_used_by_skipped(self, tmp_path):
        workspace = _write_workspace(
            tmp_path,
            synonyms=[{
                "title": "X / Y", "type": "synonym", "severity": "low",
                "terms": ["x", "y"],
                "used_by": [{"term": "x", "speakers": ["Alice"]}],
                "proposed_canonical": None,
            }],
        )
        kit = build_kit(workspace, "Emma Ward", at=_fixed_at())
        syn = next(s for s in kit.sections if "terminology" in s.heading.lower())
        assert syn.items == []


# ---------------------------------------------------------------------------
# Section: TBDs
# ---------------------------------------------------------------------------

class TestTbdSection:
    def test_tbd_entries_surfaced(self, tmp_path):
        workspace = _write_workspace(
            tmp_path,
            stakeholders=[
                {"name": "Emma Ward", "role": "Head of Finance"},
                {"name": "TBD", "role": "ML Platform Lead", "notes": "Starts in 2 weeks"},
            ],
        )
        kit = build_kit(workspace, "Emma Ward", at=_fixed_at())
        tbd = next(s for s in kit.sections if "TBD" in s.heading)
        assert any("ML Platform Lead" in item for item in tbd.items)


# ---------------------------------------------------------------------------
# Render + write
# ---------------------------------------------------------------------------

class TestRenderAndWrite:
    def test_render_has_heading_and_sections(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        kit = build_kit(workspace, "Emma Ward", at=_fixed_at())
        md = render_kit(kit)
        assert md.startswith("# Interview kit — Emma Ward")
        assert "## Open questions" in md
        assert "## Low-confidence concepts" in md
        assert "## Unresolved terminology" in md
        assert "## TBD stakeholders" in md

    def test_write_creates_file(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        kit = build_kit(workspace, "Emma Ward", at=_fixed_at())
        path = write_kit(kit)
        assert os.path.isfile(path)
        assert path.endswith("2026-05-12-emma-ward.md")
