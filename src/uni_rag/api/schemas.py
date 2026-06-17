"""Pydantic schemas for API."""
from __future__ import annotations
from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    session_id: str | None = None
    top_k: int = 5


class Citation(BaseModel):
    chunk_id: str
    source: str
    section: str
    text: str
    span: tuple[int, int] | None = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    session_id: str | None = None


class IngestResponse(BaseModel):
    source_id: str
    chunks: int
    format: str
    filename: str


class IngestJobStartResponse(BaseModel):
    job_id: str
    status_url: str


class IngestJobStatusResponse(BaseModel):
    job_id: str
    status: str
    step: str
    percent: int
    message: str
    filename: str
    result: IngestResponse | None = None
    error: str | None = None


class DocumentInfo(BaseModel):
    filename: str
    chunks: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]


class ChunkInfo(BaseModel):
    """A single chunk of a document, for the side-panel viewer."""
    id: str
    text: str
    span: tuple[int, int] | None = None
    section: str = ""


class DocumentChunksResponse(BaseModel):
    """All chunks of a single document, ordered by offset."""
    filename: str
    chunks: list[ChunkInfo]


class ExportFormat(str):
    MD = "md"
    PDF = "pdf"


class KbCreateRequest(BaseModel):
    name: str
    description: str = ""
    id: str | None = None  # 可选指定 ID


class KbInfo(BaseModel):
    id: str
    name: str
    description: str
    created_at: str


class KbListResponse(BaseModel):
    kbs: list[KbInfo]


class SessionKbBindRequest(BaseModel):
    kb_ids: list[str]


class SessionKbListResponse(BaseModel):
    session_id: str
    kbs: list[KbInfo]


class DeleteResponse(BaseModel):
    deleted: bool
