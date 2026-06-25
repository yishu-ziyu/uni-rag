"""API route handlers."""
from __future__ import annotations
from pathlib import Path
import tempfile
import threading
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from uni_rag.rag.pipeline import RAGPipeline
from uni_rag.session.store import SessionStore
from uni_rag.store.vector import VectorStore
from uni_rag.store.kb import KBStore
from uni_rag.config import load_settings
from uni_rag.api.schemas import (
    QueryRequest, QueryResponse, IngestResponse,
    IngestJobStartResponse, IngestJobStatusResponse,
    DocumentInfo, DocumentListResponse,
    ChunkInfo, DocumentChunksResponse,
    KbCreateRequest, KbInfo, KbListResponse,
    SessionKbBindRequest, SessionKbListResponse, DeleteResponse,
    SuggestQuestionsRequest, SuggestQuestionsResponse,
)
from uni_rag.export.md_exporter import render_markdown
from uni_rag.ingest.link_extractors import LinkExtractionError


router = APIRouter(prefix="/api")
_pipeline: RAGPipeline | None = None
_ingest_jobs: dict[str, dict] = {}
_ingest_jobs_lock = threading.Lock()


def get_pipeline() -> RAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline


def _set_ingest_job(key: str, **updates) -> None:
    with _ingest_jobs_lock:
        current = _ingest_jobs.get(key, {})
        _ingest_jobs[key] = {**current, **updates}


def _get_ingest_job(job_id: str) -> dict | None:
    with _ingest_jobs_lock:
        job = _ingest_jobs.get(job_id)
        return dict(job) if job else None


def _run_ingest_job(
    job_id: str,
    tmp_path: Path,
    filename: str,
    kb_id: str | None,
) -> None:
    def on_progress(event: dict) -> None:
        _set_ingest_job(
            job_id,
            status="running",
            step=event.get("step", "running"),
            percent=int(event.get("percent", 0)),
            message=str(event.get("message", "正在处理")),
        )

    try:
        _set_ingest_job(
            job_id,
            status="running",
            step="loading_model",
            percent=8,
            message="正在加载本地向量模型，首次使用可能需要更久。",
        )
        pipeline = get_pipeline() if kb_id is None else _pipeline_for_kb(kb_id)
        result = pipeline.ingest_file(tmp_path, original_name=filename, progress=on_progress)
        response = IngestResponse(
            source_id=result["source_id"],
            chunks=result["chunks"],
            format=result["format"],
            filename=filename,
        )
        _set_ingest_job(
            job_id,
            status="completed",
            step="done",
            percent=100,
            message="入库完成，可以开始提问。",
            result=response.model_dump(),
        )
    except Exception as e:
        _set_ingest_job(
            job_id,
            status="failed",
            step="failed",
            percent=100,
            message="入库失败，请换一个文件再试。",
            error=str(e),
        )
    finally:
        tmp_path.unlink(missing_ok=True)


def _run_url_ingest_job(
    job_id: str,
    url: str,
    kb_id: str | None,
) -> None:
    def on_progress(event: dict) -> None:
        _set_ingest_job(
            job_id,
            status="running",
            step=event.get("step", "running"),
            percent=int(event.get("percent", 0)),
            message=str(event.get("message", "正在处理")),
        )

    try:
        _set_ingest_job(
            job_id,
            status="running",
            step="extracting",
            percent=5,
            message="正在识别链接并提取内容",
        )
        pipeline = get_pipeline() if kb_id is None else _pipeline_for_kb(kb_id)
        result = pipeline.ingest_url(url, progress=on_progress)
        response = IngestResponse(
            source_id=result["source_id"],
            chunks=result["chunks"],
            format=result["format"],
            filename=result.get("filename", url),
        )
        _set_ingest_job(
            job_id,
            status="completed",
            step="done",
            percent=100,
            message="入库完成，可以开始提问。",
            result=response.model_dump(),
        )
    except LinkExtractionError as e:
        _set_ingest_job(
            job_id,
            status="failed",
            step="failed",
            percent=100,
            message=e.hint,
            error=str(e),
        )
    except Exception as e:
        _set_ingest_job(
            job_id,
            status="failed",
            step="failed",
            percent=100,
            message="入库失败，请检查链接是否有效后重试。",
            error=str(e),
        )


def _start_url_ingest_job(url: str, kb_id: str | None = None) -> IngestJobStartResponse:
    job_id = uuid.uuid4().hex
    _set_ingest_job(
        job_id,
        job_id=job_id,
        status="queued",
        step="queued",
        percent=1,
        message="已收到链接，准备开始提取。",
        filename=url,
        result=None,
        error=None,
    )
    worker = threading.Thread(
        target=_run_url_ingest_job,
        args=(job_id, url, kb_id),
        daemon=True,
    )
    worker.start()
    return IngestJobStartResponse(job_id=job_id, status_url=f"/api/ingest/jobs/{job_id}")


def _start_ingest_job(file: UploadFile, kb_id: str | None = None) -> IngestJobStartResponse:
    if not file.filename:
        raise HTTPException(400, "No filename")
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = file.file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    job_id = uuid.uuid4().hex
    _set_ingest_job(
        job_id,
        job_id=job_id,
        status="queued",
        step="queued",
        percent=1,
        message="已收到文件，准备开始解析。",
        filename=file.filename,
        result=None,
        error=None,
    )
    worker = threading.Thread(
        target=_run_ingest_job,
        args=(job_id, tmp_path, file.filename, kb_id),
        daemon=True,
    )
    worker.start()
    return IngestJobStartResponse(job_id=job_id, status_url=f"/api/ingest/jobs/{job_id}")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/ingest/jobs", response_model=IngestJobStartResponse)
def start_ingest_job(file: UploadFile = File(...)):
    return _start_ingest_job(file)


@router.get("/ingest/jobs/{job_id}", response_model=IngestJobStatusResponse)
def get_ingest_job(job_id: str):
    job = _get_ingest_job(job_id)
    if job is None:
        raise HTTPException(404, f"Ingest job not found: {job_id}")
    return IngestJobStatusResponse(**job)


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


class LinkIngestRequest(BaseModel):
    url: str
    kb_id: str | None = None


@router.post("/ingest/url", response_model=IngestJobStartResponse)
def ingest_url(req: LinkIngestRequest):
    if not req.url or not req.url.strip():
        raise HTTPException(400, "URL 不能为空")
    url = req.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(400, "请输入以 http:// 或 https:// 开头的有效链接")
    return _start_url_ingest_job(url, kb_id=req.kb_id)


def _query_pipeline(pipeline: RAGPipeline, question: str, session_id: str, top_k: int, api_key: str | None = None, style: str = "academic") -> dict:
    try:
        return pipeline.query(question, session_id=session_id, top_k=top_k, api_key=api_key, style=style)
    except Exception as e:
        raise HTTPException(
            502,
            "MiniMax 回答生成失败。请检查 API key / 网络连接，或稍后重试。",
        ) from e


@router.post("/query", response_model=QueryResponse)
def query(request: Request, req: QueryRequest):
    sid = req.session_id
    if not sid:
        # 自动开新 session
        sid = SessionStore(load_settings().sessions_db_path).create()
    api_key = req.api_key or request.headers.get("X-API-Key")
    result = _query_pipeline(get_pipeline(), req.question, sid, req.top_k, api_key=api_key, style=req.style)
    return QueryResponse(
        answer=result["answer"],
        citations=result["citations"],
        session_id=sid,
    )


@router.post("/suggest-questions", response_model=SuggestQuestionsResponse)
def suggest_questions(request: Request, req: SuggestQuestionsRequest):
    """根据文档内容生成 3 个建议问题。"""
    s = load_settings()
    api_key = req.api_key or request.headers.get("X-API-Key") or s.anthropic_api_key
    base_url = s.anthropic_base_url
    model = s.anthropic_model

    if not api_key or api_key == "REPLACE_WITH_YOUR_REAL_KEY":
        raise HTTPException(400, "请先在设置中配置 API Key")

    preview = req.text[:3000]  # 限制长度
    prompt = f"""根据以下文档内容，生成 3 个可以帮助学习者深入理解材料的问题。
要求：问题具体、有启发性、覆盖不同理解层次（1 个基础概念题 + 1 个分析题 + 1 个应用/延伸题）。
只返回问题列表，每行一个，不要编号，不要其他说明。

文档内容：
{preview}"""

    try:
        from anthropic import Anthropic
        client = Anthropic(base_url=base_url, api_key=api_key)
        resp = client.messages.create(
            model=model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        text = ""
        for block in resp.content:
            if hasattr(block, "text"):
                text += block.text
        questions = [q.strip() for q in text.strip().split("\n") if q.strip()][:3]
        if not questions:
            questions = [
                "这份材料的核心观点是什么？",
                "有哪些关键概念需要掌握？",
                "能举几个例子说明吗？",
            ]
        return SuggestQuestionsResponse(questions=questions)
    except Exception as e:
        raise HTTPException(502, f"生成建议问题失败: {e}") from e


@router.get("/documents", response_model=DocumentListResponse)
def list_documents():
    """List documents already ingested into the default KB."""
    return DocumentListResponse(documents=_list_documents_for_kb("default"))


@router.get("/files", response_model=DocumentListResponse)
def list_files(kb_id: str | None = None):
    """List uploaded files for a given kb_id, defaults to 'default'."""
    target_kb = kb_id if kb_id else "default"
    if target_kb != "default" and _kb_store().get(target_kb) is None:
        raise HTTPException(404, f"KB not found: {target_kb}")
    return DocumentListResponse(documents=_list_documents_for_kb(target_kb))


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


# --- Knowledge base API ---

def _kb_store() -> KBStore:
    return KBStore(load_settings().kb_db_path)


def _to_kb_info(record: dict) -> KbInfo:
    return KbInfo(
        id=record["id"],
        name=record["name"],
        description=record["description"],
        created_at=record["created_at"],
    )


def _pipeline_for_kb(kb_id: str) -> RAGPipeline:
    """Map the default KB to legacy v0.2 storage; other KBs use scoped storage."""
    return RAGPipeline(kb_id=None if kb_id == "default" else kb_id)


def _vector_for_kb(kb_id: str) -> VectorStore:
    if kb_id == "default":
        return VectorStore()
    kb_base = load_settings().data_dir / "kbs" / kb_id
    return VectorStore(data_dir=kb_base / "chroma", collection_name=f"kb_{kb_id}")


def _uploads_dir_for_kb(kb_id: str) -> Path:
    if kb_id == "default":
        return load_settings().uploads_dir
    return load_settings().data_dir / "kbs" / kb_id / "uploads"


def _list_documents_for_kb(kb_id: str) -> list[DocumentInfo]:
    uploads_dir = _uploads_dir_for_kb(kb_id)
    if not uploads_dir.exists():
        return []

    counts: dict[str, int] = {}
    vector = _vector_for_kb(kb_id)
    try:
        res = vector.collection.get(include=["metadatas"])
    except Exception:
        res = {"metadatas": []}
    for meta in res.get("metadatas") or []:
        source = str(meta.get("source", "")) if meta else ""
        if source:
            counts[source] = counts.get(source, 0) + 1

    documents: list[DocumentInfo] = []
    for path in sorted(p for p in uploads_dir.iterdir() if p.is_file() and not p.name.startswith(".")):
        documents.append(DocumentInfo(filename=path.name, chunks=counts.get(path.name, 0)))
    return documents


@router.post("/kbs", response_model=KbInfo)
def create_kb(req: KbCreateRequest):
    try:
        record = _kb_store().create(req.name, req.description, kb_id=req.id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _to_kb_info(record)


@router.get("/kbs", response_model=KbListResponse)
def list_kbs():
    store = _kb_store()
    store.ensure_default()
    return KbListResponse(kbs=[_to_kb_info(kb) for kb in store.list()])


@router.get("/kbs/{kb_id}", response_model=KbInfo)
def get_kb(kb_id: str):
    record = _kb_store().get(kb_id)
    if record is None:
        raise HTTPException(404, f"KB not found: {kb_id}")
    return _to_kb_info(record)


@router.delete("/kbs/{kb_id}", response_model=DeleteResponse)
def delete_kb(kb_id: str):
    deleted = _kb_store().delete(kb_id)
    if not deleted:
        raise HTTPException(404, f"KB not found: {kb_id}")
    return DeleteResponse(deleted=True)


@router.post("/kbs/{kb_id}/ingest/jobs", response_model=IngestJobStartResponse)
def start_kb_ingest_job(kb_id: str, file: UploadFile = File(...)):
    if _kb_store().get(kb_id) is None:
        raise HTTPException(404, f"KB not found: {kb_id}")
    return _start_ingest_job(file, kb_id=kb_id)


@router.post("/kbs/{kb_id}/ingest", response_model=IngestResponse)
async def ingest_into_kb(kb_id: str, file: UploadFile = File(...)):
    if _kb_store().get(kb_id) is None:
        raise HTTPException(404, f"KB not found: {kb_id}")
    if not file.filename:
        raise HTTPException(400, "No filename")

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        result = _pipeline_for_kb(kb_id).ingest_file(tmp_path, original_name=file.filename)
    finally:
        tmp_path.unlink(missing_ok=True)
    return IngestResponse(
        source_id=result["source_id"],
        chunks=result["chunks"],
        format=result["format"],
        filename=file.filename,
    )


@router.get("/kbs/{kb_id}/documents", response_model=DocumentListResponse)
def list_kb_documents(kb_id: str):
    """List documents already ingested into a KB."""
    if _kb_store().get(kb_id) is None:
        raise HTTPException(404, f"KB not found: {kb_id}")
    return DocumentListResponse(documents=_list_documents_for_kb(kb_id))


@router.get("/kbs/{kb_id}/documents/{filename}/chunks", response_model=DocumentChunksResponse)
def get_kb_document_chunks(kb_id: str, filename: str):
    """Return chunks for a document inside a KB, for the citation side panel."""
    if _kb_store().get(kb_id) is None:
        raise HTTPException(404, f"KB not found: {kb_id}")

    target = _uploads_dir_for_kb(kb_id) / filename
    if not target.exists():
        raise HTTPException(404, f"Document not found: {filename}")

    vector = _vector_for_kb(kb_id)
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


@router.post("/kbs/{kb_id}/query", response_model=QueryResponse)
def query_kb(request: Request, kb_id: str, req: QueryRequest):
    """Ask a question against one KB; keeps v0.2 /api/query unchanged."""
    if _kb_store().get(kb_id) is None:
        raise HTTPException(404, f"KB not found: {kb_id}")
    sid = req.session_id
    if not sid:
        sid = SessionStore(load_settings().sessions_db_path).create()
    _kb_store().bind_session(sid, [kb_id])
    api_key = req.api_key or request.headers.get("X-API-Key")
    result = _query_pipeline(_pipeline_for_kb(kb_id), req.question, sid, req.top_k, api_key=api_key, style=req.style)
    return QueryResponse(
        answer=result["answer"],
        citations=result["citations"],
        session_id=sid,
    )


@router.post("/sessions/{session_id}/kbs", response_model=SessionKbListResponse)
def bind_session_kbs(session_id: str, req: SessionKbBindRequest):
    store = _kb_store()
    try:
        store.bind_session(session_id, req.kb_ids)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return SessionKbListResponse(
        session_id=session_id,
        kbs=[_to_kb_info(kb) for kb in store.get_session_kbs(session_id)],
    )


@router.get("/sessions/{session_id}/kbs", response_model=SessionKbListResponse)
def get_session_kbs(session_id: str):
    store = _kb_store()
    return SessionKbListResponse(
        session_id=session_id,
        kbs=[_to_kb_info(kb) for kb in store.get_session_kbs(session_id)],
    )


def _build_export_payload(
    question: str,
    answer: str,
    kb_id: str | None = None,
) -> dict:
    """Build a {question, answer, citations} payload for the export modules.

    Re-runs retrieval on the same question to re-derive citations consistently.
    If the original retrieval would fail (e.g. cleared vector store), citations is [].
    """
    payload: dict = {"question": question, "answer": answer, "citations": []}
    try:
        pipeline = _pipeline_for_kb(kb_id) if kb_id else get_pipeline()
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

    bound_kbs = KBStore(settings.kb_db_path).get_session_kbs(session_id)
    kb_id = bound_kbs[0]["id"] if bound_kbs else None
    payload = _build_export_payload(question, answer, kb_id=kb_id)

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
