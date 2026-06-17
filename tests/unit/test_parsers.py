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


def test_parse_docx_with_table():
    """DOCX 解析必须把 2x2 表格变成 markdown | 分隔的多行。"""
    doc = parse_document(FIXTURES / "sample_with_table_formula.docx")
    assert "Aspect" in doc.text
    assert "Description" in doc.text
    # markdown 风格：包含 | 分隔
    assert " | " in doc.text
    # 至少两行表格
    table_lines = [l for l in doc.text.split("\n") if " | " in l]
    assert len(table_lines) >= 2


def test_parse_docx_with_formula():
    """DOCX 解析必须保留 $...$ 公式（原样保留或包到 code block 都算通过）。"""
    doc = parse_document(FIXTURES / "sample_with_table_formula.docx")
    # 内联公式原文保留
    assert "x^2 + y^2 = z^2" in doc.text
    # 块公式：用 ``` 围起来
    assert "```" in doc.text
    # 且包含积分符号或 LaTeX 关键字
    assert "int_0^1" in doc.text or "int" in doc.text
