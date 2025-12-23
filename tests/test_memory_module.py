"""Comprehensive tests for Memory Module."""

import pytest
from pathlib import Path
import tempfile
import shutil
from app.memory import ConversationMemory, Message, Conversation


class TestConversationMemory:
    """Test ConversationMemory class."""
    
    def setup_method(self):
        """Set up fresh memory instance for each test."""
        self.memory = ConversationMemory(max_messages_per_conversation=100)
    
    def test_add_single_message(self):
        """Test adding single message."""
        self.memory.add_message("conv_123", "user", "What is a dividend?")
        messages = self.memory.get_messages("conv_123")
        
        assert len(messages) == 1
        assert messages[0].role == "user"
        assert messages[0].content == "What is a dividend?"
    
    def test_add_multiple_messages(self):
        """Test adding multiple messages in sequence."""
        conv_id = "conv_multi"
        self.memory.add_message(conv_id, "user", "Hello")
        self.memory.add_message(conv_id, "assistant", "Hi there!")
        self.memory.add_message(conv_id, "user", "How are you?")
        
        messages = self.memory.get_messages(conv_id)
        assert len(messages) == 3
    
    def test_get_existing_conversation(self):
        """Test getting existing conversation."""
        conv_id = "conv_existing"
        self.memory.add_message(conv_id, "user", "Test message")
        
        conv = self.memory.get_conversation(conv_id)
        assert conv is not None
        assert conv.conversation_id == conv_id
        assert len(conv.messages) == 1
    
    def test_get_nonexistent_conversation(self):
        """Test getting non-existent conversation."""
        conv = self.memory.get_conversation("nonexistent_id")
        assert conv is None
    
    def test_get_messages_with_limit(self):
        """Test getting limited number of messages."""
        conv_id = "conv_limit"
        for i in range(10):
            self.memory.add_message(conv_id, "user", f"Message {i}")
        
        messages = self.memory.get_messages(conv_id, limit=5)
        assert len(messages) == 5
        assert messages[-1].content == "Message 9"  # Most recent
    
    def test_get_context(self):
        """Test formatted context retrieval."""
        conv_id = "conv_context"
        self.memory.add_message(conv_id, "user", "Question 1")
        self.memory.add_message(conv_id, "assistant", "Answer 1")
        
        context = self.memory.get_context(conv_id)
        assert "User: Question 1" in context
        assert "Assistant: Answer 1" in context
    
    def test_clear_conversation(self):
        """Test clearing conversation messages."""
        conv_id = "conv_clear"
        self.memory.add_message(conv_id, "user", "Message 1")
        self.memory.add_message(conv_id, "user", "Message 2")
        
        self.memory.clear_conversation(conv_id)
        messages = self.memory.get_messages(conv_id)
        assert len(messages) == 0
    
    def test_delete_conversation(self):
        """Test deleting entire conversation."""
        conv_id = "conv_delete"
        self.memory.add_message(conv_id, "user", "Test")
        
        self.memory.delete_conversation(conv_id)
        conv = self.memory.get_conversation(conv_id)
        assert conv is None
    
    def test_list_conversations(self):
        """Test listing all conversations."""
        self.memory.add_message("conv_1", "user", "Test 1")
        self.memory.add_message("conv_2", "user", "Test 2")
        
        conv_ids = self.memory.list_conversations()
        assert "conv_1" in conv_ids
        assert "conv_2" in conv_ids
    
    def test_message_metadata(self):
        """Test storing intent and risk metadata."""
        conv_id = "conv_meta"
        self.memory.add_message(
            conv_id, "user", "Buy AAPL",
            intent="trade_execution",
            risk="high"
        )
        
        messages = self.memory.get_messages(conv_id)
        assert messages[0].intent == "trade_execution"
        assert messages[0].risk == "high"
    
    def test_max_messages_pruning(self):
        """Test that old messages are pruned when limit exceeded."""
        memory = ConversationMemory(max_messages_per_conversation=5)
        conv_id = "conv_prune"
        
        for i in range(10):
            memory.add_message(conv_id, "user", f"Message {i}")
        
        messages = memory.get_messages(conv_id)
        assert len(messages) == 5
        assert messages[0].content == "Message 5"  # Oldest kept
        assert messages[-1].content == "Message 9"  # Most recent


class TestConversationPersistence:
    """Test file-based persistence."""
    
    def setup_method(self):
        """Create temp directory for persistence tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.memory = ConversationMemory(persist_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up temp directory."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_persist_conversation(self):
        """Test conversation is persisted to file."""
        conv_id = "conv_persist"
        self.memory.add_message(conv_id, "user", "Test message")
        
        conv_file = Path(self.temp_dir) / f"{conv_id}.json"
        assert conv_file.exists()
    
    def test_load_persisted_conversation(self):
        """Test loading conversation from file on init."""
        conv_id = "conv_load"
        self.memory.add_message(conv_id, "user", "Test")
        
        # Create new memory instance with same persist dir
        new_memory = ConversationMemory(persist_dir=self.temp_dir)
        conv = new_memory.get_conversation(conv_id)
        
        assert conv is not None
        assert len(conv.messages) == 1
