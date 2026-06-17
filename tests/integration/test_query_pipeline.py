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


def test_query_with_session_uses_history(pipeline, monkeypatch):
    def fake_complete(self, system, max_tokens=1024):
        return "ok"
    monkeypatch.setattr("uni_rag.llm.client.LLMClient.complete", fake_complete)

    sid = "test-session"
    pipeline.query("first question", session_id=sid)
    pipeline.query("follow up", session_id=sid)
    history = pipeline.session_store.get(sid)
    assert len(history) == 4  # 2 user + 2 assistant


def test_long_session_uses_only_recent_history(pipeline, monkeypatch):
    """30+ 轮 session，query() 注入到 LLM 的 history 不应超过 max_session_messages。"""
    captured: list[int] = []

    def fake_complete(self, system, max_tokens=1024):
        # 记录 LLM 当前持有的 message 数（不含 system prompt）
        captured.append(len(self._messages))
        return "ok"

    monkeypatch.setattr("uni_rag.llm.client.LLMClient.complete", fake_complete)

    from uni_rag.config import load_settings
    settings = load_settings()
    original = settings.uni_rag_max_session_messages
    settings.uni_rag_max_session_messages = 6  # 临时调小方便测试

    try:
        sid = "long-session"
        # 30 轮 = 60 条消息
        for i in range(30):
            pipeline.query(f"q{i}", session_id=sid)

        # 每次 query() 注入的 message 数（含本轮 user）必须 <= cap
        assert all(n <= settings.uni_rag_max_session_messages for n in captured), (
            f"some calls exceeded cap: {captured}"
        )
    finally:
        settings.uni_rag_max_session_messages = original
