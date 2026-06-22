"""E2E tests for frontend UX quick wins."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from uni_rag.api.app import create_app
from uni_rag.ingest.pipeline import IngestPipeline
from uni_rag.ingest.chunker import Chunk
from cli.main import app


# ── Fixtures ──────────────────────────────────────

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("UNI_RAG_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    from uni_rag import config as config_module
    config_module._settings = None
    from uni_rag.api import routes as routes_module
    routes_module._pipeline = None
    app_instance = create_app()
    return TestClient(app_instance)


# ── T2: Citation chips with location info ────────

class TestCitationLocationInfo:
    """Citation chips show page/section info."""

    def test_page_in_citation_response(self, tmp_path):
        """Query response includes page field in citations."""
        from uni_rag.rag.pipeline import RAGPipeline

        fake_chunks = [
            {
                "id": "abc:0",
                "document": "Hello world.",
                "metadata": {"source": "test.pdf", "section": "", "page": 3},
            }
        ]

        pipeline = RAGPipeline.__new__(RAGPipeline)
        pipeline.uploads_dir = tmp_path
        pipeline.retriever = MagicMock()
        pipeline.retriever.retrieve.return_value = fake_chunks
        pipeline.session_store = MagicMock()
        pipeline.session_store.get_recent.return_value = []
        pipeline.llm = MagicMock()
        pipeline.llm.complete.return_value = 'Answer [abc:0].'
        pipeline.llm.clear_messages = MagicMock()
        pipeline.llm.add_user_message = MagicMock()
        pipeline.llm.add_assistant_message = MagicMock()

        result = pipeline.query("test question")
        assert result["citations"][0]["page"] == 3
        assert result["citations"][0]["section"] == ""

    def test_section_in_citation_response(self, tmp_path):
        """Query response includes section field in citations."""
        from uni_rag.rag.pipeline import RAGPipeline

        fake_chunks = [
            {
                "id": "xyz:0",
                "document": "Some text.",
                "metadata": {"source": "notes.md", "section": "Introduction", "page": 0},
            }
        ]

        pipeline = RAGPipeline.__new__(RAGPipeline)
        pipeline.uploads_dir = tmp_path
        pipeline.retriever = MagicMock()
        pipeline.retriever.retrieve.return_value = fake_chunks
        pipeline.session_store = MagicMock()
        pipeline.session_store.get_recent.return_value = []
        pipeline.llm = MagicMock()
        pipeline.llm.complete.return_value = 'Answer [xyz:0].'
        pipeline.llm.clear_messages = MagicMock()
        pipeline.llm.add_user_message = MagicMock()
        pipeline.llm.add_assistant_message = MagicMock()

        result = pipeline.query("test")
        assert result["citations"][0]["section"] == "Introduction"


# ── T1: Suggested questions ──────────────────────

class TestSuggestedQuestions:
    """Suggested questions appear after upload."""

    def test_show_suggested_questions_function_exists(self):
        """app.js contains showSuggestedQuestions function."""
        js = Path("src/uni_rag/web/app.js").read_text()
        assert "function showSuggestedQuestions" in js

    def test_suggested_questions_rendered_in_chat(self, client):
        """showSuggestedQuestions creates chip buttons in chat."""
        from uni_rag.api.app import create_app
        from starlette.testclient import TestClient as TC

        app_instance = create_app()
        c = TC(app_instance)

        # Call showSuggestedQuestions via the app's static JS
        # We verify by checking the JS source contains the right elements
        js = Path("src/uni_rag/web/app.js").read_text()
        assert "suggested-questions" in js
        assert "suggest-chip" in js
        assert "试试问这些问题" in js

    def test_suggested_questions_click_submits(self, client):
        """Clicking a suggested question triggers form submit."""
        js = Path("src/uni_rag/web/app.js").read_text()
        assert "form.dispatchEvent(new Event('submit'))" in js


# ── Frontend element checks ──────────────────────

class TestFrontendElements:
    """Frontend has the new UX elements."""

    def test_settings_modal_in_html(self):
        """index.html contains settings modal."""
        html = Path("src/uni_rag/web/index.html").read_text()
        assert 'id="settings-btn"' in html
        assert 'id="settings-modal"' in html
        assert 'id="setting-api-key"' in html

    def test_citation_chip_shows_page_format(self):
        """Citation chip renders page info when section is empty."""
        js = Path("src/uni_rag/web/app.js").read_text()
        assert "c.page" in js
        assert "第" in js  # Chinese page format like "第3页"

    def test_citation_chip_shows_section_format(self):
        """Citation chip renders section when available."""
        js = Path("src/uni_rag/web/app.js").read_text()
        assert "c.section" in js

    def test_suggest_questions_endpoint(self, client):
        """POST /api/suggest-questions returns 3 questions."""
        fake_response = MagicMock()
        fake_response.content = [MagicMock(text="问题1\n问题2\n问题3")]

        with patch('anthropic.Anthropic') as MockAnthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = fake_response
            MockAnthropic.return_value = mock_client

            r = client.post("/api/suggest-questions", json={
                "text": "这是一篇关于机器学习的基础教程，介绍了监督学习、无监督学习和强化学习的核心概念。"
            })
            assert r.status_code == 200
            data = r.json()
            assert "questions" in data
            assert len(data["questions"]) == 3
