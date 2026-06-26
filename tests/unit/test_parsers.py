from pathlib import Path
import pytest
from uni_rag.ingest.parsers import parse_document, ParsedDocument

def test_parse_pdf_uses_mineru_if_available(monkeypatch):
    """Test that we dispatch to MinerU when token is configured."""
    calls = []
    def mock_is_available():
        return True
    def mock_parse_mineru(path):
        calls.append(path)
        return "mineru text"  # parse_file_via_api returns str
    monkeypatch.setattr("uni_rag.ingest.parsers.is_mineru_available", mock_is_available)
    monkeypatch.setattr("uni_rag.ingest.parsers.parse_file_via_api", mock_parse_mineru)

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        res = parse_document(f.name)
        assert res.text == "mineru text"
        assert len(calls) == 1

def test_parse_pdf_falls_back_to_pymupdf_if_mineru_unavailable(monkeypatch):
    """Test that we fall back to PyMuPDF when MinerU token is missing."""
    calls = []
    def mock_is_available():
        return False
    monkeypatch.setattr("uni_rag.ingest.parsers.is_mineru_available", mock_is_available)

    def mock_parse_pdf_pymupdf(path):
        calls.append(path)
        return ParsedDocument(text="pymupdf text", format="pdf", source_path=str(path))
    monkeypatch.setattr("uni_rag.ingest.parsers._parse_pdf_pymupdf", mock_parse_pdf_pymupdf)

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        res = parse_document(f.name)
        assert res.text == "pymupdf text"
        assert len(calls) == 1

def test_parse_pdf_falls_back_to_pymupdf_on_mineru_failure(monkeypatch):
    """Test that we fall back to PyMuPDF when MinerU raises an error."""
    calls = []
    def mock_is_available():
        return True
    def mock_parse_mineru(path):
        raise RuntimeError("MinerU API error")
    monkeypatch.setattr("uni_rag.ingest.parsers.is_mineru_available", mock_is_available)
    monkeypatch.setattr("uni_rag.ingest.parsers.parse_file_via_api", mock_parse_mineru)

    def mock_parse_pdf_pymupdf(path):
        calls.append(path)
        return ParsedDocument(text="pymupdf fallback text", format="pdf", source_path=str(path))
    monkeypatch.setattr("uni_rag.ingest.parsers._parse_pdf_pymupdf", mock_parse_pdf_pymupdf)

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        res = parse_document(f.name)
        assert res.text == "pymupdf fallback text"
        assert len(calls) == 1
