"""Tests for config loading."""
import pytest
from uni_rag.config import Settings, load_settings


def test_load_settings_reads_minimax():
    settings = load_settings()
    assert settings.anthropic_base_url.startswith("http")
    assert settings.anthropic_api_key != ""
    assert settings.anthropic_model != ""


def test_data_dir_defaults():
    settings = load_settings()
    assert settings.data_dir.exists()


def test_data_dir_override(monkeypatch, tmp_path):
    monkeypatch.setenv("UNI_RAG_DATA_DIR", str(tmp_path))
    from uni_rag import config as config_module
    config_module._settings = None
    settings = config_module.load_settings()
    assert settings.data_dir == tmp_path
    # restore
    config_module._settings = None
