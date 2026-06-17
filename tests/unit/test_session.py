"""Session store: persists multi-turn Q&A for follow-up context."""
import pytest
from uni_rag.session.store import SessionStore


@pytest.fixture
def store(tmp_path):
    db = tmp_path / "sessions.db"
    return SessionStore(db)


def test_create_and_get(store):
    sid = store.create()
    assert store.get(sid) == []


def test_append_messages(store):
    sid = store.create()
    store.append(sid, "user", "hi")
    store.append(sid, "assistant", "hello")
    msgs = store.get(sid)
    assert len(msgs) == 2
    assert msgs[0] == {"role": "user", "content": "hi"}
    assert msgs[1] == {"role": "assistant", "content": "hello"}


def test_clear(store):
    sid = store.create()
    store.append(sid, "user", "x")
    store.clear(sid)
    assert store.get(sid) == []
