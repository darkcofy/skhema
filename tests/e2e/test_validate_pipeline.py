import os



class TestValidatePipeline:
    def test_clean_workspace_passes(self, mock_workspace):
        from skhema.validate import check_inline_definitions
        source = open(os.path.join(str(mock_workspace), "diagrams", "c4", "sample.puml")).read()
        errors = check_inline_definitions(source, "sample.puml")
        assert isinstance(errors, list)
