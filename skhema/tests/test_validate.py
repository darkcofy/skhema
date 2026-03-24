"""Tests for the validation script."""
import pytest
from scripts.validate import (
    check_inline_definitions,
    check_hardcoded_colours,
    check_duplicate_ids,
)


class TestInlineDefinitions:
    def test_clean_view_passes(self):
        source = "!include ../../models/consumers.puml\n$DataAnalyst()\nRel(a, b, 'uses')"
        errors = check_inline_definitions(source, "diagrams/c4/test.puml")
        assert errors == []

    def test_inline_container_fails(self):
        source = 'Container(my_svc, "My Service", "Java", "Does things")'
        errors = check_inline_definitions(source, "diagrams/c4/test.puml")
        assert len(errors) == 1
        assert "Container(" in errors[0]

    def test_procedure_definition_ok(self):
        source = '!procedure $Foo()\n  Container(foo, "Foo", "Tech", "Desc")\n!endprocedure'
        errors = check_inline_definitions(source, "models/test.puml")
        assert errors == []


class TestHardcodedColours:
    def test_no_colours_passes(self):
        source = "$DataAnalyst()\nRel(a, b, 'uses')"
        errors = check_hardcoded_colours(source, "diagrams/c4/test.puml")
        assert errors == []

    def test_hex_colour_fails(self):
        source = 'skinparam backgroundColor #FF0000'
        errors = check_hardcoded_colours(source, "diagrams/c4/test.puml")
        assert len(errors) == 1

    def test_theme_file_exempt(self):
        source = '!$PERSON_BG_COLOR = "#FDE68A"'
        errors = check_hardcoded_colours(source, "lib/theme.puml")
        assert errors == []

    def test_template_file_exempt(self):
        source = 'skinparam backgroundColor #FFFFFF'
        errors = check_hardcoded_colours(source, "templates/sequence.puml")
        assert errors == []

    def test_prompts_file_exempt(self):
        source = 'skinparam backgroundColor #F0F0F0'
        errors = check_hardcoded_colours(source, "prompts/examples/bad-inline-defs.puml")
        assert errors == []


class TestDuplicateIds:
    def test_no_duplicates_passes(self):
        models = {
            "models/a.puml": "Container(foo, 'Foo', 'T', 'D')",
            "models/b.puml": "Container(bar, 'Bar', 'T', 'D')",
        }
        errors = check_duplicate_ids(models)
        assert errors == []

    def test_duplicates_caught(self):
        models = {
            "models/a.puml": "Container(foo, 'Foo', 'T', 'D')",
            "models/b.puml": "Container(foo, 'Foo2', 'T', 'D')",
        }
        errors = check_duplicate_ids(models)
        assert len(errors) == 1
        assert "foo" in errors[0]
