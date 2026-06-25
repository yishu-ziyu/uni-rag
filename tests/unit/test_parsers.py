from pathlib import Path
import pytest
from uni_rag.ingest.parsers import parse_document, ParsedDocument

def test_parse_pdf_uses_llama_parse_if_available(monkeypatch):
    """Test that we dispatch to LlamaParse when LLAMA_CLOUD_API_KEY is present."""
    class MockSettings:
        llama_cloud_api_key = "test_key"
    def mock_load_settings():
        return MockSettings()
    import uni_rag.config
    monkeypatch.setattr(uni_rag.config, "load_settings", mock_load_settings)
    
    calls = []
    def mock_parse_pdf_llama(path, api_key):
        calls.append((path, api_key))
        return ParsedDocument(text="llama text", format="pdf", source_path=str(path))
    monkeypatch.setattr("uni_rag.ingest.parsers._parse_pdf_llama", mock_parse_pdf_llama)
    
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        res = parse_document(f.name)
        assert res.text == "llama text"
        assert len(calls) == 1
        assert calls[0][1] == "test_key"

def test_parse_pdf_uses_pymupdf_if_no_key(monkeypatch):
    """Test that we dispatch to PyMuPDF when LLAMA_CLOUD_API_KEY is None."""
    class MockSettings:
        llama_cloud_api_key = None
    def mock_load_settings():
        return MockSettings()
    import uni_rag.config
    monkeypatch.setattr(uni_rag.config, "load_settings", mock_load_settings)
    
    calls = []
    def mock_parse_pdf_pymupdf(path):
        calls.append(path)
        return ParsedDocument(text="pymupdf text", format="pdf", source_path=str(path))
    monkeypatch.setattr("uni_rag.ingest.parsers._parse_pdf_pymupdf", mock_parse_pdf_pymupdf)
    
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        res = parse_document(f.name)
        assert res.text == "pymupdf text"
        assert len(calls) == 1
