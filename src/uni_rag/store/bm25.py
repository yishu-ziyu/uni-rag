"""BM25 keyword index, persisted to disk."""
from __future__ import annotations
import json
import pickle
from pathlib import Path
from rank_bm25 import BM25Okapi
import jieba  # 中文分词


class BM25Index:
    """BM25 index with jieba Chinese tokenization."""

    def __init__(self, index_dir: Path):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.docs: list[tuple[str, str, dict]] = []  # (id, text, meta)
        self._index: BM25Okapi | None = None

    def add(self, chunk_id: str, text: str, metadata: dict) -> None:
        self.docs.append((chunk_id, text, metadata))
        self._index = None  # 标记为脏

    def _build(self) -> None:
        tokenized = [list(jieba.cut_for_search(t)) for _, t, _ in self.docs]
        self._index = BM25Okapi(tokenized)

    def save(self) -> None:
        self._build()
        with open(self.index_dir / "docs.pkl", "wb") as f:
            pickle.dump(self.docs, f)

    @classmethod
    def load(cls, index_dir: Path) -> "BM25Index":
        idx = cls(index_dir)
        with open(index_dir / "docs.pkl", "rb") as f:
            idx.docs = pickle.load(f)
        idx._build()
        return idx

    def query(self, text: str, top_k: int = 5) -> list[dict]:
        if not self._index or not self.docs:
            return []
        tokens = list(jieba.cut_for_search(text))
        scores = self._index.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: -x[1])[:top_k]
        out = []
        for i, score in ranked:
            if score <= 0:
                continue
            chunk_id, doc_text, meta = self.docs[i]
            out.append({"id": chunk_id, "score": float(score), "metadata": meta, "document": doc_text})
        return out
