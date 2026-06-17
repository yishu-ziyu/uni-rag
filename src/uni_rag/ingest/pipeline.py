"""Ingest pipeline: parse → chunk → embed → store."""
from __future__ import annotations
import hashlib
from pathlib import Path
from dataclasses import asdict
from uni_rag.ingest.parsers import parse_document
from uni_rag.ingest.chunker import chunk_document
from uni_rag.ingest.embedder import get_embedder
from uni_rag.store.vector import VectorStore
from uni_rag.store.bm25 import BM25Index
from uni_rag.config import load_settings


class IngestPipeline:
    def __init__(self):
        self.embedder = get_embedder()
        self.vector = VectorStore()
        self.bm25 = BM25Index(load_settings().bm25_dir)
        self._bm25_dir = load_settings().bm25_dir

    def _source_id(self, path: Path) -> str:
        h = hashlib.sha256()
        h.update(str(path.resolve()).encode())
        h.update(path.read_bytes()[:1024 * 1024])  # 前 1MB
        return h.hexdigest()[:16]

    def ingest_file(self, path: Path) -> dict:
        path = Path(path)
        # 1. 复制到 uploads
        dest = load_settings().uploads_dir / path.name
        dest.write_bytes(path.read_bytes())

        # 2. 解析
        doc = parse_document(dest)
        source_id = self._source_id(dest)

        # 3. 分块
        chunks = chunk_document(doc.text, source_id=source_id)
        if not chunks:
            return {"source_id": source_id, "chunks": 0, "format": doc.format}

        # 4. embed
        texts = [c.text for c in chunks]
        vecs = self.embedder.embed(texts)

        # 5. 存 Chroma
        for c, v in zip(chunks, vecs):
            self.vector.add(
                source_id=source_id,
                chunk_id=f"{source_id}:{c.start_offset}",
                embedding=v,
                metadata={
                    "source": path.name,
                    "format": doc.format,
                    "section": c.section_title or "",
                    "start": c.start_offset,
                    "end": c.end_offset,
                },
                document=c.text,
            )

        # 6. 存 BM25
        for c in chunks:
            self.bm25.add(
                chunk_id=f"{source_id}:{c.start_offset}",
                text=c.text,
                metadata={"source": path.name, "section": c.section_title or ""},
            )
        self.bm25.save()

        return {"source_id": source_id, "chunks": len(chunks), "format": doc.format}

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Test seam: vector-only search."""
        vec = self.embedder.embed([query])[0]
        return self.vector.query(vec, top_k=top_k)
