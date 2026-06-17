"""BGE-M3 embedder wrapper (local, multilingual)."""
from __future__ import annotations
from functools import lru_cache
from sentence_transformers import SentenceTransformer


class Embedder:
    """BGE-M3: multilingual, 1024 dim, 支持中英。"""

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        vecs = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vecs]


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """Singleton accessor."""
    return Embedder()
