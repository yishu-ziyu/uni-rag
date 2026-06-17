import pytest
from pathlib import Path
from uni_rag.config import load_settings
from uni_rag.store.vector import VectorStore


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("UNI_RAG_DATA_DIR", str(tmp_path))
    return VectorStore()


def test_add_and_query(store):
    store.add("src1", "chunk1", [0.1] * 1024, {"source": "a"})
    store.add("src1", "chunk2", [0.2] * 1024, {"source": "a"})
    results = store.query([0.1] * 1024, top_k=2)
    assert len(results) == 2
    assert results[0]["id"] in ("chunk1", "chunk2")


def test_query_with_filter(store):
    store.add("src1", "c1", [0.1] * 1024, {"source": "a"})
    store.add("src1", "c2", [0.2] * 1024, {"source": "b"})
    results = store.query([0.1] * 1024, top_k=10, where={"source": "a"})
    assert all(r["metadata"]["source"] == "a" for r in results)
