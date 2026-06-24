"""Tests for RAGPipeline adaptive style system (query with style param)."""
import pytest
from unittest.mock import patch, MagicMock

from uni_rag.rag.pipeline import RAGPipeline


def _build_pipeline_with_mocked_deps():
    """Helper: construct RAGPipeline with all heavy deps mocked."""
    with patch("uni_rag.rag.pipeline.IngestPipeline"), \
         patch("uni_rag.rag.pipeline.HybridRetriever"), \
         patch("uni_rag.rag.pipeline.LLMClient"), \
         patch("uni_rag.session.store.SessionStore"), \
         patch("uni_rag.config.load_settings"):
        p = RAGPipeline(kb_id="test_kb")
    return p


def test_query_default_style_is_academic():
    """Backward compat: query() without style param should call get_system_prompt('academic')."""
    p = _build_pipeline_with_mocked_deps()
    p.retriever.retrieve.return_value = []
    p.llm.complete.return_value = "mock answer"

    with patch("uni_rag.rag.pipeline.get_system_prompt", return_value="学术系统提示") as mock_prompt:
        p.query("测试问题")

    # Currently query() uses SYSTEM_PROMPT directly, not get_system_prompt.
    # This assertion will FAIL (mock never called) until the feature is implemented.
    mock_prompt.assert_called_once_with("academic")


def test_query_with_style_casual():
    """query(style="casual") should accept a style param and forward it to get_system_prompt."""
    p = _build_pipeline_with_mocked_deps()
    p.retriever.retrieve.return_value = []
    p.llm.complete.return_value = "mock answer"

    casual_prompt = "你是一个友好的日常助手..."
    with patch(
        "uni_rag.rag.pipeline.get_system_prompt", return_value=casual_prompt
    ) as mock_prompt:
        # Currently query() has no `style` param — TypeError expected until implemented.
        p.query("测试问题", style="casual")

    mock_prompt.assert_called_once_with("casual")
    call_args = p.llm.complete.call_args
    assert call_args[0][0] == casual_prompt
