import os
import pytest


class TestParseAdr:
    def test_extracts_title_and_status(self, tmp_path):
        from skhema.adr import parse_adr
        adr_file = tmp_path / "ADR01-test-decision.md"
        adr_file.write_text(
            "# ADR01: Use Kafka\n\n## Status\nAccepted\n\n"
            "## Context\nWe need messaging.\n\n## Decision\nUse Kafka.\n"
        )
        adr = parse_adr(str(adr_file))
        assert adr.number == 1
        assert adr.title == "Use Kafka"
        assert adr.status == "Accepted"

    def test_extracts_element_links(self, tmp_path):
        from skhema.adr import parse_adr
        adr_file = tmp_path / "ADR02-storage.md"
        adr_file.write_text(
            "# ADR02: Storage Choice\n\n## Status\nAccepted\n\n"
            "## Decision\nUse Postgres.\n\n"
            "<!-- skhema:elements payment_db, user_db -->\n"
        )
        adr = parse_adr(str(adr_file))
        assert adr.elements == ["payment_db", "user_db"]

    def test_extracts_concept_links(self, tmp_path):
        from skhema.adr import parse_adr
        adr_file = tmp_path / "ADR03-events.md"
        adr_file.write_text(
            "# ADR03: Events\n\n## Status\nAccepted\n\n"
            "## Decision\nEvent sourcing.\n\n"
            "<!-- gnosis:concepts Event, PaymentReceived -->\n"
        )
        adr = parse_adr(str(adr_file))
        assert adr.concepts == ["Event", "PaymentReceived"]

    def test_no_link_tags(self, tmp_path):
        from skhema.adr import parse_adr
        adr_file = tmp_path / "ADR04-simple.md"
        adr_file.write_text("# ADR04: Simple\n\n## Status\nAccepted\n")
        adr = parse_adr(str(adr_file))
        assert adr.elements == []
        assert adr.concepts == []


class TestDiscoverAdrs:
    def test_finds_adr_files(self, tmp_path):
        from skhema.adr import discover_adrs
        adrs_dir = tmp_path / "adrs"
        adrs_dir.mkdir()
        (adrs_dir / "ADR01-first.md").write_text("# ADR01: First\n\n## Status\nAccepted\n")
        (adrs_dir / "ADR02-second.md").write_text("# ADR02: Second\n\n## Status\nAccepted\n")
        (adrs_dir / "template.md").write_text("# Template\n")
        adrs = discover_adrs(str(tmp_path))
        assert len(adrs) == 2
        assert adrs[0].number == 1
        assert adrs[1].number == 2

    def test_empty_directory(self, tmp_path):
        from skhema.adr import discover_adrs
        adrs_dir = tmp_path / "adrs"
        adrs_dir.mkdir()
        assert discover_adrs(str(tmp_path)) == []

    def test_no_adrs_directory(self, tmp_path):
        from skhema.adr import discover_adrs
        assert discover_adrs(str(tmp_path)) == []


class TestResolveLinks:
    def test_maps_elements_to_adrs(self):
        from skhema.adr import ADR, resolve_links
        from pathlib import Path
        adr = ADR(number=1, title="Test", status="Accepted",
                   path=Path("test.md"), elements=["db_main", "api_gw"],
                   concepts=[])
        manifest = {"storage": [{"id": "db_main"}], "serving": [{"id": "api_gw"}]}
        links = resolve_links([adr], manifest)
        assert "db_main" in links
        assert "api_gw" in links
        assert links["db_main"][0].number == 1


class TestFormatCoverage:
    def test_shows_uncovered_elements(self):
        from skhema.adr import ADR, format_coverage
        from pathlib import Path
        adr = ADR(number=1, title="Test", status="Accepted",
                   path=Path("test.md"), elements=["db_main"],
                   concepts=[])
        manifest = {"storage": [{"id": "db_main"}], "serving": [{"id": "api_gw"}]}
        result = format_coverage([adr], manifest)
        assert "api_gw" in result
        assert "db_main" not in result

    def test_all_covered(self):
        from skhema.adr import ADR, format_coverage
        from pathlib import Path
        adr = ADR(number=1, title="Test", status="Accepted",
                   path=Path("test.md"), elements=["db_main"],
                   concepts=[])
        manifest = {"storage": [{"id": "db_main"}]}
        result = format_coverage([adr], manifest)
        assert "All elements have ADR coverage" in result
