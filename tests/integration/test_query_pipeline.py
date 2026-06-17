"""Integration test: end-to-end query with mocked LLM."""
import pytest
from pathlib import Path
from uni_rag.rag.pipeline import RAGPipeline


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    monkeypatch.setenv("UNI_RAG_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    p = RAGPipeline()
    pdf = Path(__file__).resolve().parents[1] / "fixtures" / "sample.pdf"
    p.ingest_file(pdf)
    return p


def test_query_returns_answer_and_citations(pipeline, monkeypatch):
    """Mock the LLM call to avoid network in unit test."""
    def fake_complete(self, system, max_tokens=1024):
        return "Supervised learning uses labeled data. [src1:100] [src1:200]"
    monkeypatch.setattr("uni_rag.llm.client.LLMClient.complete", fake_complete)

    result = pipeline.query("What is supervised learning?")
    assert "answer" in result
    assert "citations" in result
    assert len(result["citations"]) > 0
