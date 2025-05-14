"""
Chat persistence model for storing conversation history.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.models.document import Base

class Chat(Base):
    """
    Model for tracking chat conversations.
    """
    __tablename__ = "chats"    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String(64), nullable=True, index=True)  # Optional user identification
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                        onupdate=lambda: datetime.now(timezone.utc))
    meta_data = Column(JSON, nullable=True)  # For additional chat session metadata (renamed from metadata to avoid SQLAlchemy conflict)

    # Relationship with messages
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert chat model to dictionary representation.
        """
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.meta_data,
            "messages": [message.to_dict() for message in self.messages]
        }


class ChatMessage(Base):
    """
    Model for storing individual messages in a chat conversation.
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)    
    message_type = Column(String(20), nullable=False)  # 'request', 'response', 'tool-call', 'tool-return', etc
    content = Column(Text, nullable=False)
    model_name = Column(String(64), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    meta_data = Column(JSON, nullable=True)  # For additional message metadata, like tokens used (renamed from metadata)
    message_idx = Column(Integer, nullable=False)  # Order of messages in the conversation
    
    # Relationship with chat
    chat = relationship("Chat", back_populates="messages")    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message model to dictionary representation.
        """
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "message_type": self.message_type,
            "content": self.content,
            "model_name": self.model_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.meta_data,
            "message_idx": self.message_idx
        }
