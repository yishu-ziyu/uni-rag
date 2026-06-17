"""Hybrid retriever: vector + BM25 + rerank."""
from __future__ import annotations
from uni_rag.ingest.embedder import get_embedder
from uni_rag.store.vector import VectorStore
from uni_rag.store.bm25 import BM25Index
from uni_rag.retrieve.reranker import Reranker
from uni_rag.config import load_settings


class HybridRetriever:
    def __init__(self):
        self.embedder = get_embedder()
        self.vector = VectorStore()
        self.bm25 = BM25Index.load(load_settings().bm25_dir)
        self.reranker = Reranker()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        source_filter: str | None = None,
    ) -> list[dict]:
        where = {"source": source_filter} if source_filter else None
        # 1. 向量召回
        vec = self.embedder.embed([query])[0]
        vec_results = self.vector.query(vec, top_k=top_k * 3, where=where)
        # 2. BM25 召回
        bm25_results = self.bm25.query(query, top_k=top_k * 3)
        if source_filter:
            bm25_results = [r for r in bm25_results if r["metadata"].get("source") == source_filter]
        # 3. 合并去重
        merged = {}
        for r in vec_results:
            merged[r["id"]] = r
        for r in bm25_results:
            if r["id"] not in merged:
                merged[r["id"]] = r
        # 4. Rerank
        docs = list(merged.values())
        return self.reranker.rerank(query, docs, top_k=top_k)
