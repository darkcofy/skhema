"""Tests for file parsers — entry counting for YAML, CSV, and Markdown."""

from gnosis.parsers import (
    count_yaml_entries,
    count_csv_rows,
    count_md_entries,
    check_md_sections,
    count_md_checkboxes,
    is_template_only,
)


class TestCountYamlEntries:
    def test_list_entries(self, tmp_path):
        f = tmp_path / "items.yaml"
        f.write_text("- name: Alice\n  role: PM\n- name: Bob\n  role: Dev\n- name: Carol\n  role: QA\n")
        assert count_yaml_entries(str(f)) == 3

    def test_mapping_keys(self, tmp_path):
        f = tmp_path / "map.yaml"
        f.write_text("transaction:\n  type: core\naccount:\n  type: entity\n")
        assert count_yaml_entries(str(f)) == 2

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.yaml"
        f.write_text("")
        assert count_yaml_entries(str(f)) == 0

    def test_comments_only(self, tmp_path):
        f = tmp_path / "comments.yaml"
        f.write_text("# Schema: name, role\n# Example:\n# - name: Alice\n")
        assert count_yaml_entries(str(f)) == 0

    def test_file_with_comment_header_and_entries(self, tmp_path):
        f = tmp_path / "with_header.yaml"
        f.write_text("# Stakeholders for this engagement\n# Schema: name, role, department\n- name: Alice\n  role: PM\n- name: Bob\n  role: Dev\n")
        assert count_yaml_entries(str(f)) == 2


class TestCountCsvRows:
    def test_rows_with_header(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("term,definition,source\napple,a fruit,glossary\nbanana,another fruit,glossary\n")
        assert count_csv_rows(str(f)) == 2

    def test_empty_csv(self, tmp_path):
        f = tmp_path / "empty.csv"
        f.write_text("term,definition,source\n")
        assert count_csv_rows(str(f)) == 0

    def test_header_only_no_newline(self, tmp_path):
        f = tmp_path / "header.csv"
        f.write_text("col1,col2,col3")
        assert count_csv_rows(str(f)) == 0

    def test_skips_blank_rows(self, tmp_path):
        f = tmp_path / "blanks.csv"
        f.write_text("term,def\napple,fruit\n\n\nbanana,fruit\n")
        assert count_csv_rows(str(f)) == 2


class TestCountMdEntries:
    def test_entries_under_capture(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text(
            "# Title\n\n"
            "## Purpose\nSome text.\n\n"
            "## Capture\n\n"
            "## Term One\nDefinition here.\n\n"
            "## Term Two\nAnother definition.\n\n"
            "## Completion criteria\n- [ ] Done\n"
        )
        assert count_md_entries(str(f)) == 2

    def test_no_capture_falls_back_to_all_h2(self, tmp_path):
        """For auto-generated files without ## Capture, count all H2 with content."""
        f = tmp_path / "no_capture.md"
        f.write_text("# Title\n\n## Purpose\nText.\n\n## Other\nStuff.\n")
        assert count_md_entries(str(f)) == 2

    def test_no_capture_empty_h2_not_counted(self, tmp_path):
        """Empty H2 sections still don't count in flat mode."""
        f = tmp_path / "no_capture_empty.md"
        f.write_text("# Title\n\n## Section A\n\n## Section B\nHas content.\n")
        assert count_md_entries(str(f)) == 1

    def test_empty_capture_section(self, tmp_path):
        f = tmp_path / "empty_capture.md"
        f.write_text("# Title\n\n## Capture\n\n## Completion criteria\n- [ ] Done\n")
        assert count_md_entries(str(f)) == 0


class TestCheckMdSections:
    def test_sections_present(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text(
            "# Engagement\n\n"
            "## domain\nPayments platform.\n\n"
            "## outcomes\nCanonical model.\n\n"
            "## out_of_scope\nReporting.\n"
        )
        result = check_md_sections(str(f), ["domain", "outcomes", "out_of_scope"])
        assert result == {"domain": True, "outcomes": True, "out_of_scope": True}

    def test_section_missing(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# Engagement\n\n## domain\nPayments.\n")
        result = check_md_sections(str(f), ["domain", "outcomes"])
        assert result == {"domain": True, "outcomes": False}

    def test_section_present_but_empty(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# Engagement\n\n## domain\n\n## outcomes\nSome content.\n")
        result = check_md_sections(str(f), ["domain", "outcomes"])
        assert result == {"domain": False, "outcomes": True}


class TestCountMdCheckboxes:
    def test_counts_checkboxes(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text(
            "## Completion criteria\n"
            "- [x] First done\n"
            "- [ ] Second pending\n"
            "- [x] Third done\n"
        )
        checked, total = count_md_checkboxes(str(f))
        assert checked == 2
        assert total == 3

    def test_no_checkboxes(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# Title\nSome text.\n")
        checked, total = count_md_checkboxes(str(f))
        assert checked == 0
        assert total == 0


class TestIsTemplateOnly:
    def test_template_file(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# Engagement Scope\n\n## Purpose\nDefine the business area.\n")
        template = "# Engagement Scope\n\n## Purpose\nDefine the business area.\n"
        assert is_template_only(str(f), template) is True

    def test_modified_file(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# Engagement Scope\n\n## Purpose\nDefine the business area.\n\nOur domain is payments.\n")
        template = "# Engagement Scope\n\n## Purpose\nDefine the business area.\n"
        assert is_template_only(str(f), template) is False
