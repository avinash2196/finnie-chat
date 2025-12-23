"""Extra tests for ConversationMemory clear/delete with persistence."""

import os
import json
import tempfile
from app.memory import ConversationMemory, get_memory


def test_clear_and_delete_conversation_with_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = ConversationMemory(max_messages_per_conversation=10, persist_dir=tmpdir)
        cid = "conv-xyz"
        mem.add_message(cid, role="user", content="hello")
        # File should exist
        path = os.path.join(tmpdir, f"{cid}.json")
        assert os.path.exists(path)
        # Clear conversation removes messages and deletes file
        mem.clear_conversation(cid)
        assert os.path.exists(path) is False
        # Add again to recreate file
        mem.add_message(cid, role="user", content="hi")
        assert os.path.exists(path)
        # Delete conversation removes it and deletes file
        mem.delete_conversation(cid)
        assert os.path.exists(path) is False
        # Listing should not include cid
        assert cid not in mem.list_conversations()


def test_load_persisted_conversation_on_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        cid = "conv-load"
        # Write a minimal conversation file
        data = {
            "conversation_id": cid,
            "messages": [
                {"role": "user", "content": "hello", "timestamp": "t0"},
                {"role": "assistant", "content": "world", "timestamp": "t1"}
            ],
            "created_at": "t0",
            "updated_at": "t1"
        }
        with open(os.path.join(tmpdir, f"{cid}.json"), "w") as f:
            json.dump(data, f)
        # Init should load the file
        mem = ConversationMemory(max_messages_per_conversation=10, persist_dir=tmpdir)
        msgs = mem.get_messages(cid)
        assert len(msgs) == 2
        assert msgs[0].content == "hello"


def test_get_memory_global_instance():
    # Ensure global memory can be constructed
    m = get_memory()
    assert isinstance(m, ConversationMemory)
