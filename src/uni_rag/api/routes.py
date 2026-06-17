"""API route handlers."""
from __future__ import annotations
from pathlib import Path
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from uni_rag.rag.pipeline import RAGPipeline
from uni_rag.session.store import SessionStore
from uni_rag.store.vector import VectorStore
from uni_rag.config import load_settings
from uni_rag.api.schemas import (
    QueryRequest, QueryResponse, IngestResponse,
    ChunkInfo, DocumentChunksResponse,
)
from uni_rag.export.md_exporter import render_markdown


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
        # 用上传时的 filename 命名落盘文件，side-panel 按 filename 查找
        result = get_pipeline().ingest_file(tmp_path, original_name=file.filename)
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


@router.get("/documents/{filename}/chunks", response_model=DocumentChunksResponse)
def get_document_chunks(filename: str):
    """Return all chunks for a given uploaded filename, ordered by offset."""
    settings = load_settings()
    # 验证文件存在
    target = settings.uploads_dir / filename
    if not target.exists():
        raise HTTPException(404, f"Document not found: {filename}")

    # 从 Chroma 拉这个 source 的所有 chunk
    vector = VectorStore()
    res = vector.collection.get(where={"source": filename}, include=["metadatas", "documents"])
    if not res["ids"]:
        return DocumentChunksResponse(filename=filename, chunks=[])

    rows: list[ChunkInfo] = []
    for i, cid in enumerate(res["ids"]):
        meta = res["metadatas"][i] if res["metadatas"] else {}
        doc_text = res["documents"][i] if res["documents"] else ""
        start = int(meta.get("start", 0) or 0)
        end = int(meta.get("end", start + len(doc_text)) or (start + len(doc_text)))
        rows.append(ChunkInfo(
            id=cid,
            text=doc_text,
            span=(start, end),
            section=str(meta.get("section", "")),
        ))
    rows.sort(key=lambda r: r.span[0] if r.span else 0)
    return DocumentChunksResponse(filename=filename, chunks=rows)


def _build_export_payload(
    question: str,
    answer: str,
) -> dict:
    """Build a {question, answer, citations} payload for the export modules.

    Re-runs retrieval on the same question to re-derive citations consistently.
    If the original retrieval would fail (e.g. cleared vector store), citations is [].
    """
    payload: dict = {"question": question, "answer": answer, "citations": []}
    try:
        pipeline = get_pipeline()
        result = pipeline.query(question, session_id=None, top_k=5)
        payload["citations"] = result.get("citations", [])
    except Exception:
        # 导出在主对话失败时仍要可用；citations 留空
        payload["citations"] = []
    return payload


@router.get("/sessions/{session_id}/messages/{message_index}/export")
def export_message(session_id: str, message_index: int, format: str = "md"):
    """Download a single assistant message as Markdown or PDF.

    `format` must be 'md' or 'pdf'. The Nth (1-based) message must be 'assistant';
    we walk back to find the most recent 'user' message to use as the question.
    """
    fmt = (format or "").lower()
    if fmt not in ("md", "pdf"):
        raise HTTPException(400, "format must be 'md' or 'pdf'")

    settings = load_settings()
    from uni_rag.session.store import SessionStore
    store = SessionStore(settings.sessions_db_path)
    msgs = store.get(session_id)
    if not msgs:
        raise HTTPException(404, f"Session not found or empty: {session_id}")
    if message_index < 1 or message_index > len(msgs):
        raise HTTPException(404, f"message_index out of range")

    role, answer = msgs[message_index - 1]["role"], msgs[message_index - 1]["content"]
    if role != "assistant":
        raise HTTPException(400, "Only assistant messages can be exported")

    # 找前一条 user message 作为 question
    question = ""
    for j in range(message_index - 2, -1, -1):
        if msgs[j]["role"] == "user":
            question = msgs[j]["content"]
            break
    if not question:
        question = "（无对应问题）"

    payload = _build_export_payload(question, answer)

    if fmt == "md":
        md_text = render_markdown(payload)
        return Response(
            content=md_text,
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="uni-rag-msg-{message_index}.md"'
            },
        )
    # pdf
    try:
        from uni_rag.export.pdf_exporter import render_pdf
    except Exception as e:
        raise HTTPException(503, f"PDF export unavailable: {e}")
    pdf_bytes = render_pdf(payload)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="uni-rag-msg-{message_index}.pdf"'
        },
    )
