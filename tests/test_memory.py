"""
Tests for conversation memory system.
"""

import pytest
from app.memory import ConversationMemory, Message, Conversation, get_memory
from datetime import datetime
import tempfile
from pathlib import Path


class TestMessage:
    """Test Message dataclass."""

    def test_message_creation(self):
        msg = Message(
            role="user",
            content="Hello",
            timestamp=datetime.utcnow().isoformat(),
            intent="ASK_CONCEPT"
        )
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.intent == "ASK_CONCEPT"

    def test_message_to_dict(self):
        msg = Message(
            role="assistant",
            content="Hi there",
            timestamp="2025-01-01T00:00:00",
            risk="LOW"
        )
        d = msg.to_dict()
        assert d["role"] == "assistant"
        assert d["risk"] == "LOW"


class TestConversationMemory:
    """Test ConversationMemory class."""

    @pytest.fixture
    def memory(self):
        """Create in-memory conversation store (no persistence)."""
        return ConversationMemory(max_messages_per_conversation=10)

    def test_add_message(self, memory):
        """Test adding a message to conversation."""
        conv_id = "test-conv-1"
        memory.add_message(conv_id, "user", "What is a bond?", intent="ASK_CONCEPT")
        
        conv = memory.get_conversation(conv_id)
        assert conv is not None
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "What is a bond?"

    def test_get_messages(self, memory):
        """Test retrieving messages from conversation."""
        conv_id = "test-conv-2"
        memory.add_message(conv_id, "user", "Message 1")
        memory.add_message(conv_id, "assistant", "Response 1")
        memory.add_message(conv_id, "user", "Message 2")
        
        messages = memory.get_messages(conv_id)
        assert len(messages) == 3
        assert messages[0].content == "Message 1"
        assert messages[1].role == "assistant"

    def test_get_messages_with_limit(self, memory):
        """Test retrieving limited messages (most recent)."""
        conv_id = "test-conv-3"
        for i in range(5):
            memory.add_message(conv_id, "user", f"Message {i}")
        
        recent = memory.get_messages(conv_id, limit=2)
        assert len(recent) == 2
        assert recent[0].content == "Message 3"
        assert recent[1].content == "Message 4"

    def test_get_context(self, memory):
        """Test getting formatted context for LLM."""
        conv_id = "test-conv-4"
        memory.add_message(conv_id, "user", "What is inflation?", intent="ASK_CONCEPT")
        memory.add_message(conv_id, "assistant", "Inflation is a rise in prices.")
        
        context = memory.get_context(conv_id)
        assert "What is inflation?" in context
        assert "Inflation is a rise in prices." in context
        assert "User:" in context
        assert "Assistant:" in context

    def test_pruning_max_messages(self, memory):
        """Test that old messages are pruned when limit exceeded."""
        # memory has max_messages_per_conversation=10
        conv_id = "test-conv-5"
        
        # Add 15 messages
        for i in range(15):
            memory.add_message(conv_id, "user", f"Message {i}")
        
        conv = memory.get_conversation(conv_id)
        assert len(conv.messages) == 10  # Pruned to 10 (keep most recent)
        # Most recent message should be Message 14
        assert conv.messages[-1].content == "Message 14"
        # Oldest should be Message 5 (dropped 0-4)
        assert conv.messages[0].content == "Message 5"

    def test_clear_conversation(self, memory):
        """Test clearing all messages from conversation."""
        conv_id = "test-conv-6"
        memory.add_message(conv_id, "user", "Message 1")
        memory.add_message(conv_id, "assistant", "Response 1")
        
        assert len(memory.get_messages(conv_id)) == 2
        
        memory.clear_conversation(conv_id)
        assert len(memory.get_messages(conv_id)) == 0

    def test_delete_conversation(self, memory):
        """Test deleting entire conversation."""
        conv_id = "test-conv-7"
        memory.add_message(conv_id, "user", "Message")
        
        assert conv_id in memory.list_conversations()
        
        memory.delete_conversation(conv_id)
        assert conv_id not in memory.list_conversations()
        assert memory.get_conversation(conv_id) is None

    def test_list_conversations(self, memory):
        """Test listing all conversation IDs."""
        memory.add_message("conv-a", "user", "Hello")
        memory.add_message("conv-b", "user", "Hi")
        memory.add_message("conv-c", "user", "Hey")
        
        convs = memory.list_conversations()
        assert len(convs) == 3
        assert "conv-a" in convs
        assert "conv-b" in convs
        assert "conv-c" in convs

    def test_persistence(self):
        """Test file-based persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create memory with persistence
            memory1 = ConversationMemory(persist_dir=tmpdir)
            memory1.add_message("persist-conv", "user", "Test message", intent="ASK_CONCEPT")
            memory1.add_message("persist-conv", "assistant", "Test response")
            
            # Create new memory instance from same directory
            memory2 = ConversationMemory(persist_dir=tmpdir)
            
            # Should load the persisted conversation
            conv = memory2.get_conversation("persist-conv")
            assert conv is not None
            assert len(conv.messages) == 2
            assert conv.messages[0].content == "Test message"
            assert conv.messages[0].intent == "ASK_CONCEPT"

    def test_get_memory_singleton(self):
        """Test global memory singleton."""
        mem1 = get_memory()
        mem2 = get_memory()
        assert mem1 is mem2  # Same instance


class TestGlobalMemory:
    """Test global memory instance behavior."""

    def test_global_memory_persists_across_calls(self):
        """Test that global memory maintains state."""
        memory = get_memory()
        # Clear any existing test data to avoid interference from prior runs
        if "global-test" in memory.list_conversations():
            memory.delete_conversation("global-test")
        
        memory.add_message("global-test", "user", "Persistent message")
        
        # Get memory again and verify message is there
        memory2 = get_memory()
        messages = memory2.get_messages("global-test")
        assert len(messages) == 1
        assert messages[0].content == "Persistent message"
