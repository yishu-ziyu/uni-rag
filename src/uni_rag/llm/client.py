"""LLM client wrapping Anthropic SDK for MiniMax M3."""
from __future__ import annotations
from anthropic import Anthropic
from uni_rag.config import load_settings


class LLMClient:
    def __init__(self):
        s = load_settings()
        self.base_url = s.anthropic_base_url
        self.api_key = s.anthropic_api_key
        self.model = s.anthropic_model
        self._client = Anthropic(base_url=self.base_url, api_key=self.api_key)
        self._messages: list[dict] = []

    @property
    def messages(self) -> list[dict]:
        return list(self._messages)

    def add_user_message(self, content: str) -> None:
        self._messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        self._messages.append({"role": "assistant", "content": content})

    def clear_messages(self) -> None:
        self._messages.clear()

    def complete(self, system: str, max_tokens: int = 1024) -> str:
        """Non-streaming completion. Returns assistant text."""
        resp = self._client.messages.create(
            model=self.model,
            system=system,
            messages=self._messages,
            max_tokens=max_tokens,
        )
        text = ""
        for block in resp.content:
            if hasattr(block, "text"):
                text += block.text
        return text
