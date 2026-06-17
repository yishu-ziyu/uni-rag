"""RAG prompt templates."""


SYSTEM_PROMPT = """你是一个严谨的学术助手。回答学生问题时必须遵循以下规则：

1. 只使用 <context> 中提供的资料回答，不要编造。
2. 每条事实后必须用 [chunk_id] 标注来源，chunk_id 是 <context> 里每段的 ID。
3. 如果 <context> 里没有相关信息，明确说"未找到相关资料"，不要硬答。
4. 引用格式示例："监督学习使用标注数据 [abc123:100]。"
5. 用中文回答，除非问题是英文。
"""


USER_PROMPT_TEMPLATE = """<context>
{context}
</context>

问题：{question}

请给出带引用的答案。"""


def build_user_prompt(question: str, chunks: list[dict]) -> str:
    """Format chunks as <context> for the LLM."""
    parts = []
    for c in chunks:
        cid = c["id"]
        text = c.get("document") or c.get("text") or ""
        meta = c.get("metadata", {})
        src = meta.get("source", "unknown")
        section = meta.get("section", "")
        parts.append(f"[{cid}] (来源: {src}, 章节: {section})\n{text}\n")
    return USER_PROMPT_TEMPLATE.format(
        context="\n".join(parts),
        question=question,
    )
