"""Ingest pipeline: parse → chunk → embed → store. Supports per-KB isolation."""
from __future__ import annotations
import hashlib
from pathlib import Path
from collections.abc import Callable
from uni_rag.ingest.parsers import parse_document
from uni_rag.ingest.chunker import chunk_document
from uni_rag.ingest.embedder import get_embedder
from uni_rag.ingest.url_parser import parse_url_result
from uni_rag.ingest import link_extractors
from uni_rag.store.vector import VectorStore
from uni_rag.store.bm25 import BM25Index
from uni_rag.config import load_settings


def _safe_upload_name(name: str) -> str:
    """Return a filename-only upload name, stripping client-supplied paths."""
    safe = Path(name.replace("\\", "/")).name
    if safe in ("", ".", ".."):
        raise ValueError("invalid upload filename")
    return safe


class IngestPipeline:
    """kb_id=None = legacy single-KB mode (v0.2 default collection 'chunks', single BM25 dir)."""

    def __init__(self, kb_id: str | None = None):
        self.embedder = get_embedder()
        self.kb_id = kb_id
        if kb_id is None:
            # Legacy: v0.2 兼容模式
            self.vector = VectorStore()
            self.bm25 = BM25Index(load_settings().bm25_dir)
            self.uploads_dir = load_settings().uploads_dir
        else:
            # Per-KB mode
            data_dir = load_settings().data_dir
            kb_base = data_dir / "kbs" / kb_id
            chroma_dir = kb_base / "chroma"
            bm25_dir = kb_base / "bm25"
            uploads_dir = kb_base / "uploads"
            chroma_dir.mkdir(parents=True, exist_ok=True)
            bm25_dir.mkdir(parents=True, exist_ok=True)
            uploads_dir.mkdir(parents=True, exist_ok=True)
            self.vector = VectorStore(data_dir=chroma_dir, collection_name=f"kb_{kb_id}")
            self.bm25 = BM25Index(bm25_dir)
            self.uploads_dir = uploads_dir

    def _source_id(self, path: Path) -> str:
        h = hashlib.sha256()
        h.update(str(path.resolve()).encode())
        h.update(path.read_bytes()[:1024 * 1024])  # 前 1MB
        return h.hexdigest()[:16]

    def ingest_file(
        self,
        path: Path,
        original_name: str | None = None,
        progress: Callable[[dict], None] | None = None,
    ) -> dict:
        def emit(step: str, percent: int, message: str, **extra) -> None:
            if progress:
                progress({"step": step, "percent": percent, "message": message, **extra})

        path = Path(path)
        save_name = _safe_upload_name(original_name or path.name)
        emit("saving", 5, "正在保存上传文件")
        dest = self.uploads_dir / save_name
        dest.write_bytes(path.read_bytes())

        emit("parsing", 20, "正在解析文档内容")
        doc = parse_document(dest)
        source_id = self._source_id(dest)

        emit("chunking", 40, "正在按章节和段落切分")
        chunks = chunk_document(doc.text, source_id=source_id)
        if not chunks:
            emit("done", 100, "未解析出可用文本", chunks=0, source_id=source_id)
            return {"source_id": source_id, "chunks": 0, "format": doc.format}

        texts = [c.text for c in chunks]
        emit("embedding", 60, f"正在生成 {len(chunks)} 个文本块的向量", chunks=len(chunks))
        vecs = self.embedder.embed(texts)

        emit("indexing", 82, "正在写入向量索引和关键词索引", chunks=len(chunks))
        for c, v in zip(chunks, vecs):
            self.vector.add(
                source_id=source_id,
                chunk_id=f"{source_id}:{c.start_offset}",
                embedding=v,
                metadata={
                    "source": save_name,
                    "format": doc.format,
                    "section": c.section_title or "",
                    "start": c.start_offset,
                    "end": c.end_offset,
                },
                document=c.text,
            )

        for c in chunks:
            self.bm25.add(
                chunk_id=f"{source_id}:{c.start_offset}",
                text=c.text,
                metadata={"source": save_name, "section": c.section_title or ""},
            )
        self.bm25.save()
        emit("done", 100, "入库完成", chunks=len(chunks), source_id=source_id)

        return {"source_id": source_id, "chunks": len(chunks), "format": doc.format}

    def ingest_url(
        self,
        url: str,
        original_name: str | None = None,
        progress: Callable[[dict], None] | None = None,
    ) -> dict:
        """从链接提取内容并入库。复用现有 chunk/embed/index 流程。"""

        def emit(step: str, percent: int, message: str, **extra) -> None:
            if progress:
                progress({"step": step, "percent": percent, "message": message, **extra})

        emit("extracting", 5, "正在识别链接并提取内容")
        extraction = link_extractors.extract(url)

        emit("parsing", 25, "正在解析提取的内容")
        doc = parse_url_result(extraction)
        source_id = self._source_id_from_url(url, doc.text)

        emit("chunking", 40, "正在按章节和段落切分")
        chunks = chunk_document(doc.text, source_id=source_id)
        if not chunks:
            emit("done", 100, "未解析出可用文本", chunks=0, source_id=source_id)
            return {"source_id": source_id, "chunks": 0, "format": doc.format}

        texts = [c.text for c in chunks]
        emit("embedding", 60, f"正在生成 {len(chunks)} 个文本块的向量", chunks=len(chunks))
        vecs = self.embedder.embed(texts)

        save_name = original_name or extraction.title or url
        emit("indexing", 82, "正在写入向量索引和关键词索引", chunks=len(chunks))
        for c, v in zip(chunks, vecs):
            self.vector.add(
                source_id=source_id,
                chunk_id=f"{source_id}:{c.start_offset}",
                embedding=v,
                metadata={
                    "source": save_name,
                    "format": doc.format,
                    "platform": extraction.platform,
                    "source_url": extraction.source_url,
                    "content_type": extraction.content_type,
                    "section": c.section_title or "",
                    "start": c.start_offset,
                    "end": c.end_offset,
                },
                document=c.text,
            )

        for c in chunks:
            self.bm25.add(
                chunk_id=f"{source_id}:{c.start_offset}",
                text=c.text,
                metadata={
                    "source": save_name,
                    "section": c.section_title or "",
                    "platform": extraction.platform,
                    "source_url": extraction.source_url,
                },
            )
        self.bm25.save()
        emit("done", 100, "入库完成", chunks=len(chunks), source_id=source_id)

        return {"source_id": source_id, "chunks": len(chunks), "format": doc.format,
                "filename": save_name}

    @staticmethod
    def _source_id_from_url(url: str, text: str) -> str:
        h = hashlib.sha256()
        h.update(url.encode())
        h.update(text[:1024 * 1024].encode())
        return h.hexdigest()[:16]

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Test seam: vector-only search within this KB."""
        vec = self.embedder.embed([query])[0]
        return self.vector.query(vec, top_k=top_k)