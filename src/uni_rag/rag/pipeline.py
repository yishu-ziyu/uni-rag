"""RAG pipeline: query → retrieve → LLM → citations. Supports per-KB isolation."""
from __future__ import annotations
import re
from pathlib import Path
from uni_rag.ingest.pipeline import IngestPipeline
from uni_rag.retrieve.retriever import HybridRetriever
from uni_rag.llm.client import LLMClient
from uni_rag.llm.prompts import get_system_prompt, build_user_prompt, get_mode_system_prompt
from uni_rag.cite.locator import locate_citation
from uni_rag.cite.verifier import CitationVerifier
from uni_rag.config import load_settings


_CITE_RE = re.compile(r"\[([a-zA-Z0-9_]+:\d+)\]")


class RAGPipeline:
    """kb_id=None = legacy v0.2 mode (single global KB)."""

    def __init__(self, kb_id: str | None = None):
        from uni_rag.session.store import SessionStore
        self.kb_id = kb_id
        self.ingest = IngestPipeline(kb_id=kb_id)
        self.retriever = HybridRetriever(kb_id=kb_id)
        self.llm = LLMClient()
        # uploads_dir 用于回查原文做 span 定位
        self.uploads_dir = (
            self.ingest.uploads_dir  # IngestPipeline 已经按 kb_id 算好
        )
        self.session_store = SessionStore(load_settings().sessions_db_path)

    def ingest_file(self, path: Path, original_name: str | None = None, progress=None) -> dict:
        return self.ingest.ingest_file(path, original_name=original_name, progress=progress)

    def ingest_url(self, url: str, original_name: str | None = None, progress=None) -> dict:
        return self.ingest.ingest_url(url, original_name=original_name, progress=progress)

    def query(
        self,
        question: str,
        session_id: str | None = None,
        top_k: int = 5,
        style: str = "academic",
        api_key: str | None = None,
        provider: str = "minimax",
        mode: str = "chat",
    ) -> dict:
        if api_key:
            llm = self.llm.with_api_key(api_key)
        elif provider and provider != "minimax":
            llm = self.llm.with_provider(provider)
        else:
            llm = self.llm

        # 1. 检索（KB-scoped）
        chunks = self.retriever.retrieve(question, top_k=top_k)

        # 2. 加载历史
        history = []
        if session_id:
            settings = load_settings()
            cap = settings.max_session_messages
            history = self.session_store.get_recent(session_id, max(cap - 1, 0))

        # 3. 构造 prompt
        llm.clear_messages()
        for m in history:
            if m["role"] == "user":
                llm.add_user_message(m["content"])
            elif m["role"] == "assistant":
                llm.add_assistant_message(m["content"])

        system_prompt = get_mode_system_prompt(mode, style)

        if chunks:
            user_prompt = build_user_prompt(question, chunks)
        else:
            user_prompt = question
        llm.add_user_message(user_prompt)
        answer = llm.complete(system_prompt)

        citations = self._extract_citations(answer, chunks) if mode == "chat" else []

        if session_id:
            self.session_store.append(session_id, "user", question)
            self.session_store.append(session_id, "assistant", answer)

        return {
            "answer": answer,
            "citations": citations,
            "chunks_used": chunks,
        }

    def _extract_citations(self, answer: str, chunks: list[dict]) -> list[dict]:
        chunk_map = {c["id"]: c for c in chunks}
        seen = set()
        out = []
        settings = load_settings()
        threshold = settings.cite_similarity_threshold
        verifier = CitationVerifier(threshold=threshold)
        last_end = 0
        for m in _CITE_RE.finditer(answer):
            cid = m.group(1)
            if cid in seen:
                last_end = m.end()
                continue
            seen.add(cid)
            chunk = chunk_map.get(cid)
            if chunk is not None:
                meta = chunk.get("metadata", {})
                src = meta.get("source", "")
                section = meta.get("section", "")
                page = meta.get("page", 0)
                cited_text = chunk.get("document") or ""
                src_path = self.uploads_dir / src
                span = None
                if src_path.exists():
                    full = src_path.read_text(errors="ignore")
                    _, span = locate_citation(full, cited_text)
            else:
                meta = {}
                src = ""
                section = ""
                page = 0
                cited_text = ""
                span = None
            claimed_text = answer[last_end:m.start()].strip()

            # NOTE: For UX reasons, we allow citation verification to be skipped or
            # we just mark it softly without blocking the main thread. Here we run it inline
            # but it is very fast (local BGE-M3 model). If it becomes a bottleneck,
            # we can make this async or run it in a background thread and push updates via WebSocket.
            similarity = verifier.verify(claimed_text, cited_text) if (claimed_text and cited_text) else 0.0

            out.append({
                "chunk_id": cid,
                "source": src,
                "section": section,
                "page": page,
                "text": cited_text,
                "span": span,
                "verified": similarity >= threshold,
                "similarity": round(similarity, 4),
            })
            last_end = m.end()
        return out