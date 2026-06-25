"""Document parsers for PDF, DOCX, Markdown."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
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
    from uni_rag.config import load_settings
    settings = load_settings()

    if settings.llama_cloud_api_key:
        return _parse_pdf_llama(path, settings.llama_cloud_api_key)
    return _parse_pdf_pymupdf(path)

def _parse_pdf_llama(path: Path, api_key: str) -> ParsedDocument:
    # LlamaParse is async, but we need to run it synchronously in our current pipeline
    import asyncio
    try:
        from llama_cloud import AsyncLlamaCloud
    except ImportError:
        # Fallback to PyMuPDF if the library is not installed
        import warnings
        warnings.warn("llama_cloud package is not installed. Falling back to PyMuPDF. Run `pip install llama-cloud`.")
        return _parse_pdf_pymupdf(path)

    async def _run():
        client = AsyncLlamaCloud(api_key=api_key)

        # 1. Upload the file
        file_obj = await client.files.create(file=str(path), purpose="parse")

        # 2. Trigger parsing (use the "agentic" tier for best multi-modal extraction)
        result = await client.parsing.parse(
            file_id=file_obj.id,
            tier="agentic",
            expand=["markdown_full"],
        )
        return result.markdown_full

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # If we're already in an async context, we shouldn't block.
        # But this function is synchronous, so we're forced to create a new thread or use nest_asyncio.
        # For simplicity, we just run the event loop in a new thread if needed, or use a new loop.
        import threading

        result_container = {}
        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            result_container['markdown'] = new_loop.run_until_complete(_run())
            new_loop.close()

        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()
        markdown = result_container['markdown']
    else:
        markdown = loop.run_until_complete(_run())

    return ParsedDocument(
        text=markdown,
        format="pdf",
        source_path=str(path),
    )

def _parse_pdf_pymupdf(path: Path) -> ParsedDocument:
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

    parts: list[str] = []

    # 1. 段落（按 body 顺序）
    for p in d.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        text = _wrap_formulas(text)
        parts.append(text)

    # 2. 表格（按 body 顺序；用 d.element.body 顺序，简化：放在段落后）
    for table in d.tables:
        rows = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            rows.append(" | ".join(cells))
        if rows:
            parts.append("\n".join(rows))

    return ParsedDocument(
        text="\n\n".join(parts),
        format="docx",
        source_path=str(path),
    )


_FORMULA_BLOCK_RE = re.compile(r"\$\$([^$]+)\$\$", re.DOTALL)


def _wrap_formulas(text: str) -> str:
    """把 $$...$$ 块公式包到 ``` 围栏里；$...$ 行内公式保留。"""
    def block_sub(m: re.Match) -> str:
        return f"```\n{m.group(1).strip()}\n```"
    return _FORMULA_BLOCK_RE.sub(block_sub, text)


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
