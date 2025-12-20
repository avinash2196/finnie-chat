"""
Conversation memory system for maintaining chat history and context.
Supports in-memory storage with optional file-based persistence.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Single message in conversation history."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    intent: Optional[str] = None
    risk: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Conversation:
    """Single conversation session."""
    conversation_id: str
    messages: List[Message]
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class ConversationMemory:
    """
    In-memory conversation memory with optional file persistence.
    
    Stores complete chat history for each conversation session.
    Supports:
    - Per-conversation message history
    - Metadata (intent, risk) per message
    - Optional file-based persistence
    - Memory limits and pruning
    """

    def __init__(self, max_messages_per_conversation: int = 100, persist_dir: Optional[str] = None):
        """
        Initialize conversation memory.
        
        Args:
            max_messages_per_conversation: Max messages to keep per conversation (older messages dropped)
            persist_dir: Directory for file persistence (optional)
        """
        self._conversations: Dict[str, Conversation] = {}
        self._max_messages = max_messages_per_conversation
        self._persist_dir = Path(persist_dir) if persist_dir else None
        
        if self._persist_dir:
            self._persist_dir.mkdir(parents=True, exist_ok=True)
            self._load_persisted_conversations()

    def add_message(self, conversation_id: str, role: str, content: str, 
                   intent: Optional[str] = None, risk: Optional[str] = None) -> None:
        """
        Add a message to conversation history.
        
        Args:
            conversation_id: Unique identifier for conversation
            role: "user" or "assistant"
            content: Message text
            intent: (optional) Detected intent
            risk: (optional) Risk classification
        """
        # Create conversation if doesn't exist
        if conversation_id not in self._conversations:
            now = datetime.utcnow().isoformat()
            self._conversations[conversation_id] = Conversation(
                conversation_id=conversation_id,
                messages=[],
                created_at=now,
                updated_at=now
            )

        conv = self._conversations[conversation_id]
        
        # Add message
        msg = Message(
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            intent=intent,
            risk=risk
        )
        conv.messages.append(msg)
        conv.updated_at = datetime.utcnow().isoformat()
        
        # Prune if over limit (keep most recent)
        if len(conv.messages) > self._max_messages:
            conv.messages = conv.messages[-self._max_messages:]
            logger.info(f"Pruned conversation {conversation_id} to {self._max_messages} messages")
        
        # Persist if enabled
        if self._persist_dir:
            self._save_conversation(conversation_id)

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve conversation by ID."""
        return self._conversations.get(conversation_id)

    def get_messages(self, conversation_id: str, limit: Optional[int] = None) -> List[Message]:
        """
        Get messages from conversation.
        
        Args:
            conversation_id: Conversation ID
            limit: Max messages to return (most recent first)
            
        Returns:
            List of Message objects
        """
        conv = self._conversations.get(conversation_id)
        if not conv:
            return []
        
        messages = conv.messages
        if limit:
            messages = messages[-limit:]
        return messages

    def get_context(self, conversation_id: str, limit: int = 10) -> str:
        """
        Get recent messages formatted as context for LLM.
        
        Args:
            conversation_id: Conversation ID
            limit: Number of recent messages to include
            
        Returns:
            Formatted conversation context as string
        """
        messages = self.get_messages(conversation_id, limit=limit)
        if not messages:
            return ""
        
        context_lines = []
        for msg in messages:
            role = "User" if msg.role == "user" else "Assistant"
            context_lines.append(f"{role}: {msg.content}")
        
        return "\n".join(context_lines)

    def clear_conversation(self, conversation_id: str) -> None:
        """Clear all messages from a conversation."""
        if conversation_id in self._conversations:
            self._conversations[conversation_id].messages = []
            self._conversations[conversation_id].updated_at = datetime.utcnow().isoformat()
            
            if self._persist_dir:
                # Delete persisted file
                conv_file = self._persist_dir / f"{conversation_id}.json"
                if conv_file.exists():
                    conv_file.unlink()
            logger.info(f"Cleared conversation {conversation_id}")

    def delete_conversation(self, conversation_id: str) -> None:
        """Delete entire conversation."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            
            if self._persist_dir:
                conv_file = self._persist_dir / f"{conversation_id}.json"
                if conv_file.exists():
                    conv_file.unlink()
            logger.info(f"Deleted conversation {conversation_id}")

    def list_conversations(self) -> List[str]:
        """Get list of all conversation IDs."""
        return list(self._conversations.keys())

    def _save_conversation(self, conversation_id: str) -> None:
        """Save conversation to file (if persistence enabled)."""
        if not self._persist_dir:
            return
        
        conv = self._conversations.get(conversation_id)
        if not conv:
            return
        
        conv_file = self._persist_dir / f"{conversation_id}.json"
        try:
            with open(conv_file, "w") as f:
                json.dump(conv.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save conversation {conversation_id}: {e}")

    def _load_persisted_conversations(self) -> None:
        """Load conversations from disk (if persistence enabled)."""
        if not self._persist_dir:
            return
        
        for conv_file in self._persist_dir.glob("*.json"):
            try:
                with open(conv_file) as f:
                    data = json.load(f)
                
                messages = [
                    Message(
                        role=m["role"],
                        content=m["content"],
                        timestamp=m["timestamp"],
                        intent=m.get("intent"),
                        risk=m.get("risk")
                    )
                    for m in data.get("messages", [])
                ]
                
                conv = Conversation(
                    conversation_id=data["conversation_id"],
                    messages=messages,
                    created_at=data["created_at"],
                    updated_at=data["updated_at"]
                )
                
                self._conversations[conv.conversation_id] = conv
                logger.info(f"Loaded conversation {conv.conversation_id} from disk")
                
            except Exception as e:
                logger.error(f"Failed to load conversation from {conv_file}: {e}")


# Global memory instance
_memory: Optional[ConversationMemory] = None


def get_memory() -> ConversationMemory:
    """Get or create the global conversation memory instance."""
    global _memory
    if _memory is None:
        # Enable persistence in 'chroma/' directory (where embeddings are stored)
        _memory = ConversationMemory(
            max_messages_per_conversation=100,
            persist_dir="chroma/conversations"
        )
    return _memory
