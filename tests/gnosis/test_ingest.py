"""Tests for gnosis.ingest — schema, lint, merge, warnings, orchestration."""
from __future__ import annotations

import datetime as _dt
import os

import pytest
import yaml

from gnosis.ingest import (
    IngestResult,
    LintWarning,
    SchemaError,
    _normalise_name,
    count_warnings,
    ingest_concepts,
    lint_dangling_related_to,
    lint_low_confidence_missing_questions,
    lint_unknown_speakers,
    load_stakeholder_names,
    merge_concepts,
    parse_concepts,
    run_lints,
    write_concepts_yaml,
    write_warnings_file,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_entry(**overrides) -> dict:
    """Minimum valid ConceptEntry dict (spread with overrides)."""
    entry = {
        "name": "Transaction",
        "domain": "payments",
        "description": "A single transfer of funds initiated by a customer against a payment method.",
        "source_quotes": [
            {
                "quote": "Every transaction starts with an auth",
                "source": "Alice Chen",
                "date": "2026-04-12",
            }
        ],
    }
    entry.update(overrides)
    return entry


def _fixed_at() -> _dt.datetime:
    return _dt.datetime(2026, 5, 6, 14, 30, 0, tzinfo=_dt.timezone.utc)


# ---------------------------------------------------------------------------
# parse_concepts — schema validation
# ---------------------------------------------------------------------------

class TestParseConcepts:
    def test_minimal_valid(self):
        entries = parse_concepts([_minimal_entry()])
        assert len(entries) == 1
        e = entries[0]
        assert e.name == "Transaction"
        assert e.domain == "payments"
        assert len(e.source_quotes) == 1
        assert e.source_quotes[0].quote.startswith("Every transaction")

    def test_full_valid(self):
        entries = parse_concepts([
            _minimal_entry(
                related_to=["Customer", "Merchant"],
                confidence="high",
                open_questions=["Does a failed authorisation still count?"],
            )
        ])
        e = entries[0]
        assert e.related_to == ["Customer", "Merchant"]
        assert e.confidence == "high"
        assert e.open_questions == ["Does a failed authorisation still count?"]

    def test_yaml_date_object_accepted(self, tmp_path):
        # PyYAML parses unquoted ISO dates into datetime.date
        path = tmp_path / "src.yaml"
        path.write_text(
            "- name: Transaction\n"
            "  domain: payments\n"
            "  description: A single transfer of funds against a payment method.\n"
            "  source_quotes:\n"
            "    - quote: It starts with an auth\n"
            "      source: Alice Chen\n"
            "      date: 2026-04-12\n"
        )
        raw = yaml.safe_load(path.read_text())
        entries = parse_concepts(raw)
        assert entries[0].source_quotes[0].date == "2026-04-12"

    def test_top_level_not_a_list(self):
        with pytest.raises(SchemaError) as exc:
            parse_concepts({"concepts": []})
        assert "Top-level YAML must be a list" in exc.value.issues[0]

    def test_missing_name(self):
        entry = _minimal_entry()
        del entry["name"]
        with pytest.raises(SchemaError) as exc:
            parse_concepts([entry])
        assert any("'name' is required" in i for i in exc.value.issues)

    def test_name_not_pascal_case(self):
        with pytest.raises(SchemaError) as exc:
            parse_concepts([_minimal_entry(name="transaction")])
        assert any("PascalCase" in i for i in exc.value.issues)

    def test_name_with_hyphen_rejected(self):
        with pytest.raises(SchemaError):
            parse_concepts([_minimal_entry(name="Data-Product")])

    def test_description_too_short(self):
        with pytest.raises(SchemaError) as exc:
            parse_concepts([_minimal_entry(description="too short")])
        assert any("description" in i.lower() for i in exc.value.issues)

    def test_missing_source_quotes(self):
        entry = _minimal_entry()
        del entry["source_quotes"]
        with pytest.raises(SchemaError) as exc:
            parse_concepts([entry])
        assert any("source_quotes" in i for i in exc.value.issues)

    def test_empty_source_quotes(self):
        with pytest.raises(SchemaError):
            parse_concepts([_minimal_entry(source_quotes=[])])

    def test_source_quote_missing_date(self):
        bad = _minimal_entry()
        bad["source_quotes"] = [{"quote": "...", "source": "Alice"}]
        with pytest.raises(SchemaError) as exc:
            parse_concepts([bad])
        assert any("'date'" in i for i in exc.value.issues)

    def test_invalid_confidence(self):
        with pytest.raises(SchemaError) as exc:
            parse_concepts([_minimal_entry(confidence="maybe")])
        assert any("confidence" in i for i in exc.value.issues)

    def test_multiple_issues_collected(self):
        with pytest.raises(SchemaError) as exc:
            parse_concepts([
                _minimal_entry(name="bad_name"),
                _minimal_entry(name="AlsoBad", description="short"),
            ])
        # At least two distinct issues surface in one exception
        assert len(exc.value.issues) >= 2

    def test_valid_entries_dropped_when_peer_invalid(self):
        """A single invalid entry aborts the whole batch — no partial writes."""
        with pytest.raises(SchemaError):
            parse_concepts([
                _minimal_entry(),  # valid
                _minimal_entry(name="bad"),  # invalid
            ])


# ---------------------------------------------------------------------------
# load_stakeholder_names
# ---------------------------------------------------------------------------

class TestLoadStakeholderNames:
    def test_missing_file(self, tmp_path):
        assert load_stakeholder_names(str(tmp_path / "nope.yaml")) == set()

    def test_list_of_dicts(self, tmp_path):
        path = tmp_path / "stakeholders.yaml"
        path.write_text(
            "- name: Alice Chen\n  role: Lead\n"
            "- name: Bob Murphy\n  role: Eng\n"
        )
        names = load_stakeholder_names(str(path))
        assert "alice chen" in names
        assert "bob murphy" in names

    def test_parenthetical_stripped(self, tmp_path):
        path = tmp_path / "stakeholders.yaml"
        path.write_text("- name: Alice Chen (Head of Data)\n  role: Lead\n")
        assert "alice chen" in load_stakeholder_names(str(path))

    def test_tbd_filtered_out(self, tmp_path):
        path = tmp_path / "stakeholders.yaml"
        path.write_text(
            "- name: Alice Chen\n  role: Lead\n"
            "- name: TBD\n  role: ML Lead\n"
        )
        names = load_stakeholder_names(str(path))
        assert "alice chen" in names
        assert "tbd" not in names

    def test_mapping_with_stakeholders_key(self, tmp_path):
        path = tmp_path / "stakeholders.yaml"
        path.write_text(
            "stakeholders:\n"
            "  - name: Alice Chen\n"
            "    role: Lead\n"
        )
        assert "alice chen" in load_stakeholder_names(str(path))


class TestNormaliseName:
    def test_plain(self):
        assert _normalise_name("Alice Chen") == "alice chen"

    def test_paren_stripped(self):
        assert _normalise_name("Alice Chen (Head of Data)") == "alice chen"

    def test_whitespace_collapsed(self):
        assert _normalise_name("Alice   Chen") == "alice chen"


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------

class TestLintUnknownSpeakers:
    def test_known_speaker_passes(self):
        entries = parse_concepts([_minimal_entry()])
        warnings = lint_unknown_speakers(entries, {"alice chen"})
        assert warnings == []

    def test_unknown_speaker_flagged(self):
        entries = parse_concepts([_minimal_entry()])
        warnings = lint_unknown_speakers(entries, {"bob murphy"})
        assert len(warnings) == 1
        assert warnings[0].rule == "unknown_speaker"
        assert warnings[0].concept == "Transaction"

    def test_paren_suffix_on_source_still_matches(self):
        entries = parse_concepts([
            _minimal_entry(
                source_quotes=[{
                    "quote": "...",
                    "source": "Alice Chen (Head of Data)",
                    "date": "2026-04-12",
                }]
            )
        ])
        assert lint_unknown_speakers(entries, {"alice chen"}) == []


class TestLintDanglingRelatedTo:
    def test_resolved_within_batch(self):
        entries = parse_concepts([
            _minimal_entry(name="Transaction", related_to=["PaymentMethod"]),
            _minimal_entry(name="PaymentMethod"),
        ])
        warnings = lint_dangling_related_to(entries, {c.name for c in entries})
        assert warnings == []

    def test_dangling_flagged(self):
        entries = parse_concepts([
            _minimal_entry(name="Transaction", related_to=["Nonexistent"])
        ])
        warnings = lint_dangling_related_to(entries, {"Transaction"})
        assert len(warnings) == 1
        assert warnings[0].rule == "dangling_related_to"
        assert "Nonexistent" in warnings[0].message

    def test_case_insensitive_resolution(self):
        entries = parse_concepts([
            _minimal_entry(name="Transaction", related_to=["paymentmethod"])
        ])
        warnings = lint_dangling_related_to(entries, {"PaymentMethod", "Transaction"})
        assert warnings == []


class TestLintLowConfidenceMissingQuestions:
    def test_low_without_questions_flagged(self):
        entries = parse_concepts([
            _minimal_entry(confidence="low")
        ])
        warnings = lint_low_confidence_missing_questions(entries)
        assert len(warnings) == 1
        assert warnings[0].rule == "low_confidence_missing_questions"

    def test_low_with_questions_passes(self):
        entries = parse_concepts([
            _minimal_entry(confidence="low", open_questions=["Is this real?"])
        ])
        assert lint_low_confidence_missing_questions(entries) == []

    def test_medium_without_questions_passes(self):
        entries = parse_concepts([_minimal_entry(confidence="medium")])
        assert lint_low_confidence_missing_questions(entries) == []


class TestRunLints:
    def test_combined_run(self):
        new = parse_concepts([
            _minimal_entry(
                name="Transaction",
                related_to=["Ghost"],
                confidence="low",
            ),
        ])
        warnings = run_lints(new, existing_concepts=[], known_speakers={"alice chen"})
        rules = {w.rule for w in warnings}
        # Unknown speaker won't fire (Alice is known); dangling_related_to (Ghost)
        # and low_confidence_missing_questions (low + empty questions) should.
        assert "dangling_related_to" in rules
        assert "low_confidence_missing_questions" in rules

    def test_cross_batch_resolution(self):
        existing = parse_concepts([_minimal_entry(name="Order")])
        new = parse_concepts([
            _minimal_entry(name="Transaction", related_to=["Order"])
        ])
        warnings = run_lints(new, existing, known_speakers={"alice chen"})
        assert not any(w.rule == "dangling_related_to" for w in warnings)


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

class TestMergeConcepts:
    def test_new_concept_appended(self):
        new = parse_concepts([_minimal_entry()])
        merged, report = merge_concepts([], new, session="s1", interviewer="al", at=_fixed_at())
        assert len(merged) == 1
        assert merged[0].name == "Transaction"
        assert report.added == ["Transaction"]
        assert report.updated == []
        assert merged[0].last_ingested == {
            "session": "s1",
            "interviewer": "al",
            "at": "2026-05-06T14:30:00+00:00",
        }

    def test_existing_concept_updated(self):
        existing = parse_concepts([
            _minimal_entry(
                description="Original description of a transaction concept.",
                related_to=["Customer"],
            )
        ])
        new = parse_concepts([
            _minimal_entry(
                description="Revised description of a transaction concept.",
                related_to=["Merchant"],
                source_quotes=[{
                    "quote": "New quote from Bob",
                    "source": "Bob Murphy",
                    "date": "2026-04-14",
                }],
            )
        ])
        merged, report = merge_concepts(existing, new, session="s2", interviewer="al", at=_fixed_at())
        assert len(merged) == 1
        assert report.added == []
        assert report.updated == ["Transaction"]
        m = merged[0]
        assert m.description.startswith("Revised")
        # related_to union, existing first
        assert m.related_to == ["Customer", "Merchant"]
        # source_quotes unioned
        quotes = [sq.quote for sq in m.source_quotes]
        assert "Every transaction starts with an auth" in quotes
        assert "New quote from Bob" in quotes

    def test_source_quote_dedup(self):
        existing = parse_concepts([_minimal_entry()])
        new = parse_concepts([_minimal_entry()])  # identical quote
        merged, _ = merge_concepts(existing, new, session="s", interviewer="al", at=_fixed_at())
        assert len(merged[0].source_quotes) == 1

    def test_case_insensitive_name_match(self):
        existing = parse_concepts([_minimal_entry(name="Transaction")])
        new = parse_concepts([_minimal_entry(name="Transaction")])
        merged, report = merge_concepts(existing, new, session="s", interviewer="al", at=_fixed_at())
        assert len(merged) == 1
        assert report.updated == ["Transaction"]


# ---------------------------------------------------------------------------
# YAML writer round-trip
# ---------------------------------------------------------------------------

class TestWriteConceptsYaml:
    def test_roundtrip(self, tmp_path):
        entries = parse_concepts([
            _minimal_entry(
                related_to=["Customer"],
                confidence="high",
                open_questions=["X?"],
            )
        ])
        entries[0].last_ingested = {"session": "s", "interviewer": "al", "at": "2026-05-06T00:00:00+00:00"}
        path = tmp_path / "out.yaml"
        write_concepts_yaml(entries, str(path))
        raw = yaml.safe_load(path.read_text())
        assert raw[0]["name"] == "Transaction"
        assert raw[0]["confidence"] == "high"
        assert raw[0]["last_ingested"]["session"] == "s"


# ---------------------------------------------------------------------------
# Warnings file
# ---------------------------------------------------------------------------

class TestWriteWarningsFile:
    def test_clean_state(self, tmp_path):
        path = tmp_path / "ingest-warnings.md"
        write_warnings_file([], str(path), session="s", interviewer="al", at=_fixed_at())
        text = path.read_text()
        assert "No warnings" in text
        assert count_warnings(str(path)) == 0

    def test_grouped_by_rule(self, tmp_path):
        warnings = [
            LintWarning(rule="unknown_speaker", concept="Settlement", message="Dan is unknown"),
            LintWarning(rule="dangling_related_to", concept="ReportPackage", message="DataCouncil not found"),
            LintWarning(rule="low_confidence_missing_questions", concept="FinanceFeed", message="no questions"),
        ]
        path = tmp_path / "ingest-warnings.md"
        write_warnings_file(warnings, str(path), session="s", interviewer="al", at=_fixed_at())
        text = path.read_text()
        assert "## Unknown speakers (1)" in text
        assert "## Dangling related_to references (1)" in text
        assert "## Low-confidence entries missing open_questions (1)" in text
        assert "Total: 3 warning(s) across 3 concept(s)" in text
        assert count_warnings(str(path)) == 3


# ---------------------------------------------------------------------------
# Orchestration (ingest_concepts)
# ---------------------------------------------------------------------------

def _write_workspace(tmp_path, stakeholders: list[dict] | None = None) -> str:
    """Build a minimal gnosis workspace under tmp_path and return its path."""
    workspace = tmp_path / "ontology"
    (workspace / "00_scope").mkdir(parents=True)
    (workspace / "02_concepts").mkdir(parents=True)
    sh = stakeholders or [
        {"name": "Alice Chen", "role": "Lead"},
        {"name": "Bob Murphy", "role": "Principal"},
    ]
    (workspace / "00_scope" / "stakeholders.yaml").write_text(yaml.safe_dump(sh))
    return str(workspace)


class TestIngestConcepts:
    def test_fresh_ingest_writes_files(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "fixture.yaml"
        fixture.write_text(yaml.safe_dump([_minimal_entry()]))

        result = ingest_concepts(
            workspace_path=workspace,
            fixture_path=str(fixture),
            session="s1",
            interviewer="al",
            at=_fixed_at(),
        )
        assert isinstance(result, IngestResult)
        assert result.added == ["Transaction"]
        assert result.merged_count == 1
        assert os.path.isfile(os.path.join(workspace, "02_concepts", "candidate-concepts.yaml"))
        assert os.path.isfile(os.path.join(workspace, "ingest-warnings.md"))

    def test_schema_error_writes_nothing(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "fixture.yaml"
        fixture.write_text(yaml.safe_dump([_minimal_entry(name="lowercase")]))

        with pytest.raises(SchemaError):
            ingest_concepts(
                workspace_path=workspace,
                fixture_path=str(fixture),
                session="s1",
                interviewer="al",
                at=_fixed_at(),
            )
        assert not os.path.isfile(os.path.join(workspace, "02_concepts", "candidate-concepts.yaml"))
        assert not os.path.isfile(os.path.join(workspace, "ingest-warnings.md"))

    def test_reingest_merges(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        # Pass 1
        fixture1 = tmp_path / "f1.yaml"
        fixture1.write_text(yaml.safe_dump([_minimal_entry(related_to=["Customer"])]))
        ingest_concepts(workspace_path=workspace, fixture_path=str(fixture1),
                        session="s1", interviewer="al", at=_fixed_at())

        # Pass 2 — different related_to, same concept
        fixture2 = tmp_path / "f2.yaml"
        fixture2.write_text(yaml.safe_dump([_minimal_entry(related_to=["Merchant"])]))
        result = ingest_concepts(workspace_path=workspace, fixture_path=str(fixture2),
                                 session="s2", interviewer="al", at=_fixed_at())
        assert result.updated == ["Transaction"]

        merged_path = os.path.join(workspace, "02_concepts", "candidate-concepts.yaml")
        merged = yaml.safe_load(open(merged_path).read())
        assert merged[0]["related_to"] == ["Customer", "Merchant"]

    def test_lint_warnings_surface_in_file(self, tmp_path):
        workspace = _write_workspace(tmp_path)
        fixture = tmp_path / "f.yaml"
        fixture.write_text(yaml.safe_dump([
            _minimal_entry(
                source_quotes=[{
                    "quote": "...",
                    "source": "Unknown Person",
                    "date": "2026-04-12",
                }],
                related_to=["Ghost"],
                confidence="low",
            )
        ]))

        result = ingest_concepts(workspace_path=workspace, fixture_path=str(fixture),
                                 session="s", interviewer="al", at=_fixed_at())
        rules = {w.rule for w in result.warnings}
        assert "unknown_speaker" in rules
        assert "dangling_related_to" in rules
        assert "low_confidence_missing_questions" in rules

        warnings_text = open(os.path.join(workspace, "ingest-warnings.md")).read()
        assert "Unknown Person" in warnings_text
        assert "Ghost" in warnings_text
