import pytest
from pathlib import Path
from uni_rag.ingest.pipeline import IngestPipeline


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    monkeypatch.setenv("UNI_RAG_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    return IngestPipeline()


def test_ingest_pdf_returns_chunk_count(pipeline):
    pdf = Path(__file__).resolve().parents[1] / "fixtures" / "sample.pdf"
    result = pipeline.ingest_file(pdf)
    assert result["chunks"] > 0
    assert result["source_id"]
    assert result["format"] == "pdf"


def test_ingest_marks_persisted(pipeline):
    pdf = Path(__file__).resolve().parents[1] / "fixtures" / "sample.pdf"
    pipeline.ingest_file(pdf)
    # 检索能找回来
    results = pipeline.search("supervised learning", top_k=3)
    assert any("supervised" in r["document"].lower() for r in results)
