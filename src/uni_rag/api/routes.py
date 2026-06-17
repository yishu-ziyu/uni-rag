"""API route handlers."""
from __future__ import annotations
from pathlib import Path
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from uni_rag.rag.pipeline import RAGPipeline
from uni_rag.session.store import SessionStore
from uni_rag.config import load_settings
from uni_rag.api.schemas import QueryRequest, QueryResponse, IngestResponse


router = APIRouter(prefix="/api")
_pipeline: RAGPipeline | None = None


def get_pipeline() -> RAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No filename")
    # 存临时文件 → pipeline 读取
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        result = get_pipeline().ingest_file(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)
    return IngestResponse(
        source_id=result["source_id"],
        chunks=result["chunks"],
        format=result["format"],
        filename=file.filename,
    )


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    sid = req.session_id
    if not sid:
        # 自动开新 session
        sid = SessionStore(load_settings().sessions_db_path).create()
    result = get_pipeline().query(req.question, session_id=sid, top_k=req.top_k)
    return QueryResponse(
        answer=result["answer"],
        citations=result["citations"],
        session_id=sid,
    )
