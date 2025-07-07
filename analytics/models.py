"""
Database models for analytics service.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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
    
    # Relationship with messages
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")    

class ChatMessage(Base):
    """
    Model for storing individual messages in a chat conversation.
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)    
    message_id = Column(String(64), nullable=False, index=True)  # Unique message ID
    message_type = Column(String(20), nullable=False)  # 'user' or 'assistant'
    message_object = Column(JSON, nullable=False)  # Message content as JSON dictionary
    history = Column(JSON, nullable=True)  # Raw message history from the agent (only for assistant messages)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationship with chat
    chat = relationship("Chat", back_populates="messages")    

class Document(Base):
    """
    Model for tracking documents stored in MinIO.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    object_name = Column(String(255), unique=True, nullable=False)
    content_type = Column(String(100), nullable=False)      
    size = Column(Integer, nullable=False)
    upload_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    meta_data = Column(JSON, nullable=True)  # Renamed from 'metadata' which is reserved
    collection_id = Column(String(64), nullable=True, index=True)  # Identifier for collections

class Webpage(Base):
    """
    Model for tracking crawled webpages.
    """
    __tablename__ = "webpages"    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), unique=True, nullable=False, index=True)
    title = Column(String(512), nullable=True)
    content_hash = Column(String(64), nullable=True)  # For detecting changes
    content_markdown = Column(Text, nullable=True)    
    last_crawled = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    first_crawled = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    crawl_depth = Column(Integer, default=0)
    status_code = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True)  # Renamed from 'metadata' which is reserved    
    is_seed = Column(Boolean, default=False)
    content_type = Column(String(100), nullable=True)
    collection_id = Column(String(64), nullable=True, index=True)  # Identifier for crawl jobs/collections
    is_indexed = Column(Boolean, default=False, nullable=False)  # Track whether the webpage has been indexed
    indexed_at = Column(DateTime(timezone=True), nullable=True)  # When the webpage was indexed
