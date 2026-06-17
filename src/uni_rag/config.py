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


_settings: Settings | None = None


def load_settings() -> Settings:
    """Load settings (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
