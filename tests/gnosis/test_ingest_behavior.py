"""Tests for gnosis.ingest_behavior — schemas, lint, merge, orchestration."""
from __future__ import annotations

import datetime as _dt
import os

import pytest
import yaml

from gnosis.ingest import SchemaError
from gnosis.ingest_behavior import (
    _is_past_tense,
    ingest_behavior,
    lint_event_not_past_tense,
    lint_unknown_entity,
    lint_unknown_speaker_in_quotes,
    lint_unknown_transition_trigger,
    merge_events,
    merge_lifecycles,
    parse_events,
    parse_lifecycles,
    run_lints,
)


def _fixed_at() -> _dt.datetime:
    return _dt.datetime(2026, 5, 10, 10, 0, 0, tzinfo=_dt.timezone.utc)


def _lifecycle(**overrides) -> dict:
    e = {
        "entity": "Order",
        "states": [
            {"name": "placed", "description": "Customer placed the order."},
            {"name": "paid", "description": "Payment captured."},
        ],
        "transitions": [
            {"from": "placed", "to": "paid", "trigger": "OrderPaid"},
        ],
    }
    e.update(overrides)
    return e


def _event(**overrides) -> dict:
    e = {
        "name": "OrderPaid",
        "domain": "orders",
        "entity": "Order",
        "triggered_by": "Payment capture confirmed",
        "carries": ["order_id", "amount"],
    }
    e.update(overrides)
    return e


# ---------------------------------------------------------------------------
# Lifecycle schema
# ---------------------------------------------------------------------------

class TestParseLifecycles:
    def test_minimal_valid(self):
        out = parse_lifecycles([_lifecycle()])
        assert out[0].entity == "Order"
        assert [s.name for s in out[0].states] == ["placed", "paid"]
        assert out[0].transitions[0].trigger == "OrderPaid"

    def test_missing_entity(self):
        bad = _lifecycle()
        del bad["entity"]
        with pytest.raises(SchemaError):
            parse_lifecycles([bad])

    def test_entity_not_pascal_case(self):
        with pytest.raises(SchemaError):
            parse_lifecycles([_lifecycle(entity="order")])

    def test_single_state_rejected(self):
        with pytest.raises(SchemaError):
            parse_lifecycles([_lifecycle(states=[{"name": "placed", "description": "x"}])])

    def test_state_name_not_snake_case(self):
        with pytest.raises(SchemaError):
            parse_lifecycles([_lifecycle(states=[
                {"name": "Placed", "description": "bad case"},
                {"name": "paid", "description": "ok"},
            ])])

    def test_transition_references_unknown_state(self):
        with pytest.raises(SchemaError) as exc:
            parse_lifecycles([_lifecycle(transitions=[
                {"from": "placed", "to": "delivered", "trigger": "X"},
            ])])
        assert any("'to' state 'delivered'" in i for i in exc.value.issues)

    def test_duplicate_entity(self):
        with pytest.raises(SchemaError):
            parse_lifecycles([_lifecycle(), _lifecycle()])


# ---------------------------------------------------------------------------
# Event schema
# ---------------------------------------------------------------------------

class TestParseEvents:
    def test_minimal_valid(self):
        out = parse_events([_event()])
        assert out[0].name == "OrderPaid"
        assert out[0].carries == ["order_id", "amount"]

    def test_name_not_pascal_case(self):
        with pytest.raises(SchemaError):
            parse_events([_event(name="order_paid")])

    def test_empty_carries(self):
        with pytest.raises(SchemaError) as exc:
            parse_events([_event(carries=[])])
        assert any("carries" in i for i in exc.value.issues)

    def test_missing_domain(self):
        bad = _event()
        del bad["domain"]
        with pytest.raises(SchemaError):
            parse_events([bad])

    def test_duplicate_name(self):
        with pytest.raises(SchemaError):
            parse_events([_event(), _event()])


# ---------------------------------------------------------------------------
# Past-tense heuristic
# ---------------------------------------------------------------------------

class TestIsPastTense:
    def test_regular_ed(self):
        assert _is_past_tense("OrderPlaced")
        assert _is_past_tense("TransactionAuthorised")

    def test_irregular_paid(self):
        assert _is_past_tense("OrderPaid")

    def test_published_detected(self):
        assert _is_past_tense("DataProductPublished")

    def test_imperative_rejected(self):
        assert not _is_past_tense("ShipOrder")
        assert not _is_past_tense("CreateOrder")

    def test_single_word_handled(self):
        assert _is_past_tense("Paid")
        assert not _is_past_tense("Ship")


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------

class TestLintEventNotPastTense:
    def test_imperative_flagged(self):
        events = parse_events([_event(name="ShipOrder")])
        warnings = lint_event_not_past_tense(events)
        assert len(warnings) == 1
        assert warnings[0].rule == "event_not_past_tense"

    def test_past_tense_passes(self):
        events = parse_events([_event(name="OrderPaid")])
        assert lint_event_not_past_tense(events) == []


class TestLintUnknownEntity:
    def test_lifecycle_entity_unknown(self):
        lc = parse_lifecycles([_lifecycle(entity="Ghost")])
        warnings = lint_unknown_entity(lc, [], {"Order"})
        assert len(warnings) == 1
        assert warnings[0].rule == "unknown_entity"
        assert "Ghost" in warnings[0].message

    def test_event_entity_unknown(self):
        ev = parse_events([_event(entity="Ghost")])
        warnings = lint_unknown_entity([], ev, {"Order"})
        assert len(warnings) == 1

    def test_case_insensitive_resolution(self):
        lc = parse_lifecycles([_lifecycle()])
        warnings = lint_unknown_entity(lc, [], {"order"})
        assert warnings == []


class TestLintUnknownTransitionTrigger:
    def test_unknown_trigger_flagged(self):
        lc = parse_lifecycles([_lifecycle(transitions=[
            {"from": "placed", "to": "paid", "trigger": "NonexistentEvent"},
        ])])
        warnings = lint_unknown_transition_trigger(lc, {"OrderPaid"})
        assert len(warnings) == 1
        assert warnings[0].rule == "unknown_transition_trigger"

    def test_known_trigger_passes(self):
        lc = parse_lifecycles([_lifecycle()])
        warnings = lint_unknown_transition_trigger(lc, {"OrderPaid"})
        assert warnings == []


class TestLintUnknownSpeakerInQuotes:
    def test_lifecycle_quote_unknown_flagged(self):
        lc = parse_lifecycles([_lifecycle(source_quotes=[
            {"quote": "...", "source": "Ghost", "date": "2026-04-12"},
        ])])
        warnings = lint_unknown_speaker_in_quotes(lc, [], {"alice chen"})
        assert len(warnings) == 1

    def test_event_quote_unknown_flagged(self):
        ev = parse_events([_event(source_quotes=[
            {"quote": "...", "source": "Ghost", "date": "2026-04-12"},
        ])])
        warnings = lint_unknown_speaker_in_quotes([], ev, {"alice chen"})
        assert len(warnings) == 1


class TestRunLints:
    def test_combined(self):
        lc = parse_lifecycles([_lifecycle(entity="Ghost")])
        ev = parse_events([_event(name="ShipOrder", entity="Order")])
        warnings = run_lints(lc, ev, [], [], known_concepts={"Order"}, known_speakers=set())
        rules = {w.rule for w in warnings}
        assert "unknown_entity" in rules        # Ghost lifecycle
        assert "event_not_past_tense" in rules  # ShipOrder

    def test_trigger_resolved_across_new_batch(self):
        lc = parse_lifecycles([_lifecycle(transitions=[
            {"from": "placed", "to": "paid", "trigger": "OrderPaid"},
        ])])
        ev = parse_events([_event(name="OrderPaid")])
        warnings = run_lints(lc, ev, [], [], known_concepts={"Order"}, known_speakers=set())
        assert not any(w.rule == "unknown_transition_trigger" for w in warnings)


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

class TestMergeLifecycles:
    def test_new_added(self):
        new = parse_lifecycles([_lifecycle()])
        merged, added, updated = merge_lifecycles([], new, session="s", interviewer="al", at=_fixed_at())
        assert len(merged) == 1
        assert added == ["Order"]

    def test_existing_unions_transitions(self):
        existing = parse_lifecycles([_lifecycle()])
        new = parse_lifecycles([_lifecycle(
            states=[
                {"name": "placed", "description": "x"},
                {"name": "paid", "description": "x"},
                {"name": "delivered", "description": "delivered by carrier"},
            ],
            transitions=[
                {"from": "placed", "to": "paid", "trigger": "OrderPaid"},       # duplicate
                {"from": "paid", "to": "delivered", "trigger": "OrderDelivered"},  # new
            ],
        )])
        merged, _, updated = merge_lifecycles(existing, new, session="s", interviewer="al", at=_fixed_at())
        assert updated == ["Order"]
        triggers = [t.trigger for t in merged[0].transitions]
        assert triggers.count("OrderPaid") == 1
        assert "OrderDelivered" in triggers
        state_names = {s.name for s in merged[0].states}
        assert "delivered" in state_names


class TestMergeEvents:
    def test_new_added(self):
        new = parse_events([_event()])
        merged, added, _ = merge_events([], new, session="s", interviewer="al", at=_fixed_at())
        assert added == ["OrderPaid"]

    def test_existing_unions_carries(self):
        existing = parse_events([_event(carries=["order_id"])])
        new = parse_events([_event(carries=["amount"])])
        merged, _, updated = merge_events(existing, new, session="s", interviewer="al", at=_fixed_at())
        assert updated == ["OrderPaid"]
        assert "order_id" in merged[0].carries
        assert "amount" in merged[0].carries


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def _write_workspace(tmp_path, concepts=None, stakeholders=None) -> str:
    workspace = tmp_path / "ontology"
    (workspace / "00_scope").mkdir(parents=True)
    (workspace / "02_concepts").mkdir(parents=True)
    (workspace / "04_behavior").mkdir(parents=True)
    if concepts is None:
        concepts = [{
            "name": "Order",
            "domain": "orders",
            "description": "A customer's purchase intent — a 20+ char description to satisfy schema.",
            "source_quotes": [{"quote": "q", "source": "Alice Chen", "date": "2026-04-12"}],
        }]
    (workspace / "02_concepts" / "candidate-concepts.yaml").write_text(yaml.safe_dump(concepts))
    if stakeholders is None:
        stakeholders = [{"name": "Alice Chen", "role": "Lead"}]
    (workspace / "00_scope" / "stakeholders.yaml").write_text(yaml.safe_dump(stakeholders))
    return str(workspace)


class TestIngestBehavior:
    def test_fresh_ingest_writes_both_files(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.yaml"
        fixture.write_text(yaml.safe_dump({
            "lifecycles": [_lifecycle()],
            "events": [_event()],
        }))
        result = ingest_behavior(
            workspace_path=workspace, fixture_path=str(fixture),
            session="s", interviewer="al", at=_fixed_at(),
        )
        assert result.lifecycles_total == 1
        assert result.events_total == 1
        assert os.path.isfile(os.path.join(workspace, "04_behavior", "lifecycle-states.yaml"))
        assert os.path.isfile(os.path.join(workspace, "04_behavior", "events.yaml"))

    def test_lifecycles_only(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.yaml"
        fixture.write_text(yaml.safe_dump({"lifecycles": [_lifecycle(transitions=[
            {"from": "placed", "to": "paid", "trigger": "OrderPaid"},
        ])]}))
        result = ingest_behavior(
            workspace_path=workspace, fixture_path=str(fixture),
            session="s", interviewer="al", at=_fixed_at(),
        )
        assert result.lifecycles_total == 1
        assert result.events_total == 0
        # events.yaml should not be created since no new events
        assert not os.path.isfile(os.path.join(workspace, "04_behavior", "events.yaml"))
        # but the unknown_transition_trigger lint should fire
        assert any(w.rule == "unknown_transition_trigger" for w in result.warnings)

    def test_empty_input_refused(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.yaml"
        fixture.write_text(yaml.safe_dump({}))
        with pytest.raises(SchemaError):
            ingest_behavior(workspace_path=workspace, fixture_path=str(fixture),
                            session="s", interviewer="al", at=_fixed_at())

    def test_warnings_surface_lint_rules(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.yaml"
        fixture.write_text(yaml.safe_dump({
            "lifecycles": [_lifecycle(entity="Ghost")],   # unknown_entity
            "events": [_event(name="ShipOrder")],         # not_past_tense
        }))
        result = ingest_behavior(workspace_path=workspace, fixture_path=str(fixture),
                                 session="s", interviewer="al", at=_fixed_at())
        rules = {w.rule for w in result.warnings}
        assert "unknown_entity" in rules
        assert "event_not_past_tense" in rules
        text = open(os.path.join(workspace, "ingest-warnings.md")).read()
        assert "entry(s)" in text
