"""Configuration loading from environment variables."""
from __future__ import annotations
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # MiniMax / Anthropic 兼容
    anthropic_base_url: str = "https://api.minimaxi.com/anthropic"
    anthropic_api_key: str
    anthropic_model: str = "MiniMax-M3"

    # 数据目录
    uni_rag_data_dir: str = "./data"

    # Session 长度上限（防止长对话打爆 LLM context）
    uni_rag_max_session_messages: int = 20

    @property
    def max_session_messages(self) -> int:
        """Alias for uni_rag_max_session_messages (used by RAG pipeline)."""
        return self.uni_rag_max_session_messages

    @property
    def data_dir(self) -> Path:
        p = Path(self.uni_rag_data_dir).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def uploads_dir(self) -> Path:
        p = self.data_dir / "uploads"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def chroma_dir(self) -> Path:
        p = self.data_dir / "chroma"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def bm25_dir(self) -> Path:
        p = self.data_dir / "bm25"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def sessions_db_path(self) -> Path:
        return self.data_dir / "sessions.db"

    @property
    def kb_db_path(self) -> Path:
        return self.data_dir / "kbs.db"

    @property
    def kb_dir(self) -> Path:
        """Base dir for per-KB subdirectories (chroma/, bm25/, uploads/)."""
        p = self.data_dir / "kbs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    # Citation verification
    cite_similarity_threshold: float = 0.45

    # LlamaCloud (LlamaParse) configuration
    llama_cloud_api_key: str | None = None


_settings: Settings | None = None


def load_settings() -> Settings:
    """Load settings (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
