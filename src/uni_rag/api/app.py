"""FastAPI app factory."""
from __future__ import annotations
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from uni_rag.api.routes import router
from uni_rag.config import load_settings
from uni_rag.logging_setup import setup_logging
from uni_rag.store.kb import KBStore


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="uni-rag", version="0.1.0")
    KBStore(load_settings().kb_db_path).ensure_default()
    app.include_router(router)

    # 静态前端
    web_dir = Path(__file__).resolve().parents[1] / "web"
    if web_dir.exists():
        app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

        @app.get("/")
        def index():
            return FileResponse(str(web_dir / "index.html"))

    return app
