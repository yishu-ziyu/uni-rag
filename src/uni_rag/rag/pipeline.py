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
        self.ingest = IngestPipeline()
        self.retriever = HybridRetriever()
        self.llm = LLMClient()
        self.uploads_dir = load_settings().uploads_dir

    def ingest_file(self, path: Path) -> dict:
        return self.ingest.ingest_file(path)

    def query(
        self,
        question: str,
        session_id: str | None = None,
        top_k: int = 5,
    ) -> dict:
        # 1. 检索
        chunks = self.retriever.retrieve(question, top_k=top_k)
        if not chunks:
            return {
                "answer": "未找到相关资料。请尝试换个问法，或先上传相关文档。",
                "citations": [],
                "chunks_used": [],
            }

        # 2. 构造 prompt
        user_prompt = build_user_prompt(question, chunks)
        self.llm.clear_messages()
        self.llm.add_user_message(user_prompt)
        answer = self.llm.complete(SYSTEM_PROMPT)

        # 3. 解析引用
        citations = self._extract_citations(answer, chunks)

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
