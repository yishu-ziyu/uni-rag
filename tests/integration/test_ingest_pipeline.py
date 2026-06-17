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


def test_ingest_emits_user_visible_progress(pipeline):
    """长文件入库时应汇报阶段进度，避免用户以为页面卡死。"""
    pdf = Path(__file__).resolve().parents[1] / "fixtures" / "sample.pdf"
    events = []

    result = pipeline.ingest_file(pdf, progress=events.append)

    assert result["chunks"] > 0
    steps = [event["step"] for event in events]
    assert steps == ["saving", "parsing", "chunking", "embedding", "indexing", "done"]
    assert events[0]["percent"] > 0
    assert events[-1]["percent"] == 100
    assert all(event["message"] for event in events)



    pdf = Path(__file__).resolve().parents[1] / "fixtures" / "sample.pdf"
    pipeline.ingest_file(pdf)
    # 检索能找回来
    results = pipeline.search("supervised learning", top_k=3)
    assert any("supervised" in r["document"].lower() for r in results)
