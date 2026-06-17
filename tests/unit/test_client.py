"""Tests for the Anthropic SDK → MiniMax M3 LLM client."""
import pytest
from uni_rag.llm.client import LLMClient


def test_client_builds():
    c = LLMClient()
    assert c.model
    assert c.api_key
    assert c.base_url


def test_messages_property():
    c = LLMClient()
    c.add_user_message("hi")
    c.add_assistant_message("hello")
    msgs = c.messages
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"


def test_clear_messages_empties_buffer():
    c = LLMClient()
    c.add_user_message("hi")
    c.add_assistant_message("hello")
    assert len(c.messages) == 2
    c.clear_messages()
    assert c.messages == []
