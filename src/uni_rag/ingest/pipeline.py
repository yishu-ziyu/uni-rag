"""Ingest pipeline: parse → chunk → embed → store. Supports per-KB isolation."""
from __future__ import annotations
import hashlib
from pathlib import Path
from uni_rag.ingest.parsers import parse_document
from uni_rag.ingest.chunker import chunk_document
from uni_rag.ingest.embedder import get_embedder
from uni_rag.store.vector import VectorStore
from uni_rag.store.bm25 import BM25Index
from uni_rag.config import load_settings


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

    def ingest_file(self, path: Path, original_name: str | None = None) -> dict:
        path = Path(path)
        save_name = original_name or path.name
        dest = self.uploads_dir / save_name
        dest.write_bytes(path.read_bytes())

        doc = parse_document(dest)
        source_id = self._source_id(dest)

        chunks = chunk_document(doc.text, source_id=source_id)
        if not chunks:
            return {"source_id": source_id, "chunks": 0, "format": doc.format}

        texts = [c.text for c in chunks]
        vecs = self.embedder.embed(texts)

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

        return {"source_id": source_id, "chunks": len(chunks), "format": doc.format}

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Test seam: vector-only search within this KB."""
        vec = self.embedder.embed([query])[0]
        return self.vector.query(vec, top_k=top_k)