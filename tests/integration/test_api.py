"""Integration test: FastAPI app end-to-end."""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from uni_rag.api.app import create_app


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
