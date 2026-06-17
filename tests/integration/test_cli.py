"""Integration test: Typer CLI."""
import pytest
from pathlib import Path
from typer.testing import CliRunner
from cli.main import app


@pytest.fixture
def runner(tmp_path, monkeypatch):
    monkeypatch.setenv("UNI_RAG_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    return CliRunner()


def test_ingest_command(runner):
    pdf = Path(__file__).resolve().parents[1] / "fixtures" / "sample.pdf"
    result = runner.invoke(app, ["ingest", str(pdf)])
    assert result.exit_code == 0
    assert "chunks" in result.stdout


def test_serve_command_starts(runner):
    # 只测能 import，不真起 server
    from cli.main import serve
    assert callable(serve)
