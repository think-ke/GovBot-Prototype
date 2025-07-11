"""
Chat event tracking model for real-time event monitoring.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.db.models.document import Base

class ChatEvent(Base):
    """
    Model for tracking real-time chat processing events.
    Provides visibility into backend processing stages for frontend users.
    """
    __tablename__ = "chat_events"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), nullable=False, index=True)  # Links to Chat.session_id
    message_id = Column(String(64), nullable=True, index=True)   # Links to ChatMessage.message_id
    event_type = Column(String(50), nullable=False, index=True)  # Type of event (see EVENT_MESSAGES)
    event_status = Column(String(20), nullable=False)            # 'started', 'progress', 'completed', 'failed'
    event_data = Column(JSON, nullable=True)                     # Additional event-specific data
    user_message = Column(String(500), nullable=True)            # User-friendly message
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Optional: Performance tracking
    processing_time_ms = Column(Integer, nullable=True)
    
    # Create composite indexes for efficient querying
    __table_args__ = (
        Index('idx_session_timestamp', 'session_id', 'timestamp'),
        Index('idx_session_event_type', 'session_id', 'event_type'),
        Index('idx_message_events', 'message_id', 'timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event model to dictionary representation.
        """
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message_id": self.message_id,
            "event_type": self.event_type,
            "event_status": self.event_status,
            "event_data": self.event_data,
            "user_message": self.user_message,
            "timestamp": self.timestamp.isoformat() if self.timestamp is not None else None,
            "processing_time_ms": self.processing_time_ms
        }
