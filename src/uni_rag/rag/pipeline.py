"""RAG pipeline: query → retrieve → LLM → citations."""
from __future__ import annotations
import re
from pathlib import Path
from uni_rag.ingest.pipeline import IngestPipeline
from uni_rag.retrieve.retriever import HybridRetriever
from uni_rag.llm.client import LLMClient
from uni_rag.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from uni_rag.cite.locator import locate_citation
from uni_rag.config import load_settings


_CITE_RE = re.compile(r"\[([a-zA-Z0-9_]+:\d+)\]")


class RAGPipeline:
    def __init__(self):
        from uni_rag.session.store import SessionStore
        self.ingest = IngestPipeline()
        self.retriever = HybridRetriever()
        self.llm = LLMClient()
        self.uploads_dir = load_settings().uploads_dir
        self.session_store = SessionStore(load_settings().sessions_db_path)

    def ingest_file(self, path: Path, original_name: str | None = None) -> dict:
        return self.ingest.ingest_file(path, original_name=original_name)

    def query(
        self,
        question: str,
        session_id: str | None = None,
        top_k: int = 5,
    ) -> dict:
        # 1. 检索
        chunks = self.retriever.retrieve(question, top_k=top_k)

        # 2. 加载历史（仅最近 N 条，防止长对话打爆 LLM context）
        history = []
        if session_id:
            settings = load_settings()
            # 预留 1 个 slot 给本轮 user prompt，所以历史最多取 cap-1
            cap = settings.max_session_messages
            history = self.session_store.get_recent(session_id, max(cap - 1, 0))

        # 3. 构造 prompt（注入历史 + 当前问题）
        self.llm.clear_messages()
        for m in history:
            if m["role"] == "user":
                self.llm.add_user_message(m["content"])
            elif m["role"] == "assistant":
                self.llm.add_assistant_message(m["content"])

        if not chunks:
            answer = "未找到相关资料。请尝试换个问法，或先上传相关文档。"
        else:
            user_prompt = build_user_prompt(question, chunks)
            self.llm.add_user_message(user_prompt)
            answer = self.llm.complete(SYSTEM_PROMPT)

        # 4. 解析引用
        citations = self._extract_citations(answer, chunks)

        # 5. 落历史
        if session_id:
            self.session_store.append(session_id, "user", question)
            self.session_store.append(session_id, "assistant", answer)

        return {
            "answer": answer,
            "citations": citations,
            "chunks_used": chunks,
        }

    def _extract_citations(self, answer: str, chunks: list[dict]) -> list[dict]:
        """Parse [chunk_id] markers and link to source documents."""
        chunk_map = {c["id"]: c for c in chunks}
        seen = set()
        out = []
        for m in _CITE_RE.finditer(answer):
            cid = m.group(1)
            if cid in seen:
                continue
            seen.add(cid)
            chunk = chunk_map.get(cid)
            if chunk is not None:
                meta = chunk.get("metadata", {})
                src = meta.get("source", "")
                section = meta.get("section", "")
                cited_text = chunk.get("document") or ""
                # 找原始文件，定位 span
                src_path = self.uploads_dir / src
                span = None
                if src_path.exists():
                    full = src_path.read_text(errors="ignore")
                    _, span = locate_citation(full, cited_text)
            else:
                # 引用了不在当前召回里的 chunk（LLM 幻觉或外部 id），仍记录
                meta = {}
                src = ""
                section = ""
                cited_text = ""
                span = None
            out.append({
                "chunk_id": cid,
                "source": src,
                "section": section,
                "text": cited_text,
                "span": span,
            })
        return out
