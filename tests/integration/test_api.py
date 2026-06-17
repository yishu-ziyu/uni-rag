"""Integration test: FastAPI app end-to-end."""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from uni_rag.api.app import create_app


def _weasyprint_renders() -> bool:
    try:
        from weasyprint import HTML
        HTML(string="<html><body>ok</body></html>").write_pdf()
        return True
    except Exception:
        return False


_pdf_required = pytest.mark.skipif(
    not _weasyprint_renders(),
    reason="weasyprint native deps not loadable on this host",
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("UNI_RAG_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    app = create_app()
    return TestClient(app)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_upload_and_query(client, tmp_path, monkeypatch):
    def fake_complete(self, system, max_tokens=1024):
        return "answer with [src]"
    monkeypatch.setattr("uni_rag.llm.client.LLMClient.complete", fake_complete)

    pdf = Path(__file__).resolve().parents[1] / "fixtures" / "sample.pdf"
    with open(pdf, "rb") as f:
        r = client.post("/api/ingest", files={"file": ("sample.pdf", f, "application/pdf")})
    assert r.status_code == 200
    assert r.json()["chunks"] > 0

    r = client.post("/api/query", json={"question": "what is supervised learning?"})
    assert r.status_code == 200
    assert "answer" in r.json()


def test_get_document_chunks(client, tmp_path, monkeypatch):
    """GET /api/documents/{filename}/chunks returns the file's chunks."""
    def fake_complete(self, system, max_tokens=1024):
        return "ok"
    monkeypatch.setattr("uni_rag.llm.client.LLMClient.complete", fake_complete)

    pdf = Path(__file__).resolve().parents[1] / "fixtures" / "sample.pdf"
    with open(pdf, "rb") as f:
        r = client.post("/api/ingest", files={"file": ("sample.pdf", f, "application/pdf")})
    assert r.status_code == 200

    r = client.get("/api/documents/sample.pdf/chunks")
    assert r.status_code == 200
    data = r.json()
    assert "chunks" in data
    assert len(data["chunks"]) > 0
    first = data["chunks"][0]
    assert {"id", "text", "span"} <= set(first.keys())


def test_export_message_markdown(client, tmp_path, monkeypatch):
    """GET .../export?format=md 返回 markdown 文件下载。"""
    def fake_complete(self, system, max_tokens=1024):
        return "answer with [src]"
    monkeypatch.setattr("uni_rag.llm.client.LLMClient.complete", fake_complete)

    pdf = Path(__file__).resolve().parents[1] / "fixtures" / "sample.pdf"
    with open(pdf, "rb") as f:
        r = client.post("/api/ingest", files={"file": ("sample.pdf", f, "application/pdf")})
    assert r.status_code == 200

    # 发一个问题
    r = client.post("/api/query", json={"question": "what is supervised learning?"})
    assert r.status_code == 200

    # 从 SessionStore 拿到 session_id 和 message seq
    from uni_rag.config import load_settings
    from uni_rag.session.store import SessionStore
    sess = SessionStore(load_settings().sessions_db_path)
    # 找任意一个非空 session
    import sqlite3
    with sqlite3.connect(load_settings().sessions_db_path) as conn:
        rows = conn.execute("SELECT DISTINCT session_id FROM messages LIMIT 1").fetchall()
    assert rows
    sid = rows[0][0]
    # 第一个 assistant message 是 seq=2（user 是 seq=1）
    r = client.get(f"/api/sessions/{sid}/messages/2/export?format=md")
    assert r.status_code == 200
    assert "text/markdown" in r.headers["content-type"]
    body = r.text
    assert "# 问答记录" in body
    assert "## 问题" in body


def test_export_message_pdf(client, tmp_path, monkeypatch):
    """GET .../export?format=pdf 返回 application/pdf bytes。"""
    def fake_complete(self, system, max_tokens=1024):
        return "answer with [src]"
    monkeypatch.setattr("uni_rag.llm.client.LLMClient.complete", fake_complete)

    pdf = Path(__file__).resolve().parents[1] / "fixtures" / "sample.pdf"
    with open(pdf, "rb") as f:
        client.post("/api/ingest", files={"file": ("sample.pdf", f, "application/pdf")})
    client.post("/api/query", json={"question": "q"})

    from uni_rag.config import load_settings
    import sqlite3
    with sqlite3.connect(load_settings().sessions_db_path) as conn:
        rows = conn.execute("SELECT DISTINCT session_id FROM messages LIMIT 1").fetchall()
    sid = rows[0][0]
    r = client.get(f"/api/sessions/{sid}/messages/2/export?format=pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF-")


@_pdf_required
def test_export_message_pdf(client, tmp_path, monkeypatch):
    """GET .../export?format=pdf 返回 application/pdf bytes。"""
    def fake_complete(self, system, max_tokens=1024):
        return "answer with [src]"
    monkeypatch.setattr("uni_rag.llm.client.LLMClient.complete", fake_complete)

    pdf = Path(__file__).resolve().parents[1] / "fixtures" / "sample.pdf"
    with open(pdf, "rb") as f:
        client.post("/api/ingest", files={"file": ("sample.pdf", f, "application/pdf")})
    client.post("/api/query", json={"question": "q"})

    from uni_rag.config import load_settings
    import sqlite3
    with sqlite3.connect(load_settings().sessions_db_path) as conn:
        rows = conn.execute("SELECT DISTINCT session_id FROM messages LIMIT 1").fetchall()
    sid = rows[0][0]
    r = client.get(f"/api/sessions/{sid}/messages/2/export?format=pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF-")


def test_export_message_invalid_format(client, tmp_path):
    from uni_rag.config import load_settings
    from uni_rag.session.store import SessionStore
    sid = SessionStore(load_settings().sessions_db_path).create()
    SessionStore(load_settings().sessions_db_path).append(sid, "user", "q")
    SessionStore(load_settings().sessions_db_path).append(sid, "assistant", "a")
    r = client.get(f"/api/sessions/{sid}/messages/1/export?format=docx")
    assert r.status_code == 400
