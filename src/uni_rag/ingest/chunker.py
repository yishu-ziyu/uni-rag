"""Semantic chunker: split on headers, then by size."""
from __future__ import annotations
from dataclasses import dataclass
import re


@dataclass
class Chunk:
    text: str
    source_id: str
    section_title: str | None
    start_offset: int  # 相对于原始 text
    end_offset: int


_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def _split_by_headers(text: str) -> list[tuple[str | None, str]]:
    """Return [(title, body), ...] 按 markdown header 切分。"""
    matches = list(_HEADER_RE.finditer(text))
    if not matches:
        return [(None, text)]
    sections = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        title = m.group(2).strip()
        body = text[start:end].strip()
        if body:
            sections.append((title, body))
    return sections


def _split_long_body(body: str, max_chars: int) -> list[str]:
    """长段按句子边界切分。"""
    if len(body) <= max_chars:
        return [body]
    sentences = re.split(r"(?<=[.!?。！？])\s+", body)
    chunks = []
    current = []
    cur_len = 0
    for s in sentences:
        if cur_len + len(s) > max_chars and current:
            chunks.append(" ".join(current).strip())
            current = [s]
            cur_len = len(s)
        else:
            current.append(s)
            cur_len += len(s) + 1
    if current:
        chunks.append(" ".join(current).strip())
    return chunks


def chunk_document(
    text: str,
    source_id: str,
    max_chars: int = 1000,
) -> list[Chunk]:
    """按 header 切，再按 max_chars 切长段。"""
    sections = _split_by_headers(text)
    chunks = []
    cursor = 0
    for title, body in sections:
        # 找 body 在原文的位置
        idx = text.find(body, cursor)
        if idx < 0:
            idx = cursor
        cursor = idx + len(body)
        for piece in _split_long_body(body, max_chars):
            piece_start = text.find(piece, idx)
            if piece_start < 0:
                piece_start = idx
            chunks.append(Chunk(
                text=piece,
                source_id=source_id,
                section_title=title,
                start_offset=piece_start,
                end_offset=piece_start + len(piece),
            ))
    return chunks
