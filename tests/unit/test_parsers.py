from pathlib import Path
from uni_rag.ingest.parsers import parse_document, ParsedDocument

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_parse_markdown():
    doc = parse_document(FIXTURES / "sample.md")
    assert isinstance(doc, ParsedDocument)
    assert "Introduction" in doc.text
    assert "Supervised" in doc.text
    assert doc.format == "md"


def test_parse_pdf():
    doc = parse_document(FIXTURES / "sample.pdf")
    assert "Supervised" in doc.text
    assert "Unsupervised" in doc.text
    assert doc.format == "pdf"


def test_parse_unsupported_raises(tmp_path):
    f = tmp_path / "weird.xyz"
    f.write_text("nope")
    import pytest
    with pytest.raises(ValueError, match="Unsupported format"):
        parse_document(f)
