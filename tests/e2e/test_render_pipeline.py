import os
import sys



class TestRenderPipeline:
    def test_renders_single_file(self, mock_workspace, mock_plantuml, tmp_path):
        from skhema.render import render_file
        diagrams_dir = os.path.join(str(mock_workspace), "diagrams")
        rendered_dir = str(tmp_path / "rendered")
        source = os.path.join(diagrams_dir, "c4", "sample.puml")
        result = render_file(source_path=source, diagrams_dir=diagrams_dir,
                            rendered_dir=rendered_dir, root=str(mock_workspace),
                            fmt="svg", dry_run=False)
        assert result is True
        assert os.path.exists(os.path.join(rendered_dir, "c4", "sample.svg"))

    def test_renders_all_files(self, mock_workspace, mock_plantuml, tmp_path):
        from skhema.render import find_all_diagrams, render_file
        diagrams_dir = os.path.join(str(mock_workspace), "diagrams")
        rendered_dir = str(tmp_path / "rendered")
        files = find_all_diagrams(diagrams_dir)
        assert len(files) >= 2
        for f in files:
            render_file(f, diagrams_dir, rendered_dir, str(mock_workspace), "svg", False)
        assert os.path.exists(os.path.join(rendered_dir, "c4", "sample.svg"))
        assert os.path.exists(os.path.join(rendered_dir, "sequence", "flow.svg"))

    def test_malformed_puml_surfaces_error(self):
        from skhema.render import render_plantuml
        from unittest.mock import patch, MagicMock
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = b"Syntax Error at line 2"
        with patch("skhema.render.subprocess.run", return_value=mock_result):
            try:
                render_plantuml("@startuml\nbad\n@enduml")
                assert False
            except RuntimeError as e:
                assert "Syntax Error" in str(e)
