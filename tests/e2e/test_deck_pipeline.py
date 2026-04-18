import os
import sys
from unittest.mock import patch



class TestDeckPipeline:
    def test_produces_merged_pdf(self, mock_workspace, mock_plantuml, fake_pdf, tmp_path):
        from skhema.deck import build_deck
        output = str(tmp_path / "deck.pdf")
        diagrams_dir = os.path.join(str(mock_workspace), "diagrams")
        with patch("skhema.deck._svg_to_pdf", return_value=fake_pdf):
            build_deck(client_name="Test", diagrams_dir=diagrams_dir,
                      search_paths=[], output_path=output, include_cover=False)
        assert os.path.exists(output)
        from pypdf import PdfReader
        reader = PdfReader(output)
        assert len(reader.pages) >= 2

    def test_pages_flag_emits_individual_files(self, mock_workspace, mock_plantuml, fake_pdf, tmp_path):
        from skhema.deck import build_deck
        output = str(tmp_path / "deck.pdf")
        diagrams_dir = os.path.join(str(mock_workspace), "diagrams")
        with patch("skhema.deck._svg_to_pdf", return_value=fake_pdf):
            build_deck(client_name="Test", diagrams_dir=diagrams_dir,
                      search_paths=[], output_path=output,
                      include_cover=False, emit_pages=True)
        pages_dir = output.replace(".pdf", "_pages")
        assert os.path.isdir(pages_dir)
        assert len(os.listdir(pages_dir)) >= 2
