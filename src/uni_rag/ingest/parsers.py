"""Document parsers for PDF, DOCX, Markdown."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import fitz  # PyMuPDF
import docx
from markdown_it import MarkdownIt


@dataclass
class ParsedDocument:
    """Output of a parser."""
    text: str
    format: str  # 'pdf' | 'docx' | 'md'
    source_path: str
    pages: list[tuple[int, str]] | None = None  # [(page_no, text)] for pdf


def _parse_pdf(path: Path) -> ParsedDocument:
    doc = fitz.open(str(path))
    pages = []
    full = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        pages.append((i + 1, text))
        full.append(text)
    doc.close()
    return ParsedDocument(
        text="\n\n".join(full),
        format="pdf",
        source_path=str(path),
        pages=pages,
    )


def _parse_docx(path: Path) -> ParsedDocument:
    d = docx.Document(str(path))
    paragraphs = [p.text for p in d.paragraphs if p.text.strip()]
    return ParsedDocument(
        text="\n\n".join(paragraphs),
        format="docx",
        source_path=str(path),
    )


def _parse_md(path: Path) -> ParsedDocument:
    md = MarkdownIt()
    text = path.read_text(encoding="utf-8")
    rendered = md.render(text)
    # MarkdownIt 渲染后有 HTML 标签，去掉
    import re
    plain = re.sub(r"<[^>]+>", "", rendered)
    plain = re.sub(r"\n{3,}", "\n\n", plain).strip()
    return ParsedDocument(
        text=plain,
        format="md",
        source_path=str(path),
    )


def parse_document(path: str | Path) -> ParsedDocument:
    """Dispatch to the right parser by file extension."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Not found: {p}")
    ext = p.suffix.lower()
    if ext == ".pdf":
        return _parse_pdf(p)
    if ext == ".docx":
        return _parse_docx(p)
    if ext in (".md", ".markdown"):
        return _parse_md(p)
    raise ValueError(f"Unsupported format: {ext}")
