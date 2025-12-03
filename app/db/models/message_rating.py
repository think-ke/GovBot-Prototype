"""
Message rating model for storing user feedback on assistant responses.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Index
from sqlalchemy.orm import relationship

from app.db.models.document import Base

class MessageRating(Base):
    """
    Model for storing user ratings and feedback on assistant messages.
    """
    __tablename__ = "message_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), nullable=False, index=True)  # Links to Chat.session_id
    message_id = Column(String(64), nullable=False, index=True)  # Links to ChatMessage.message_id
    user_id = Column(String(64), nullable=True, index=True)      # Optional user identification
    
    # Rating information
    rating = Column(Integer, nullable=False)                     # Star rating 1-5
    feedback_text = Column(Text, nullable=True)                  # Optional written feedback
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                        onupdate=lambda: datetime.now(timezone.utc))
    rating_metadata = Column(JSON, nullable=True)                   # Additional rating metadata
    
    # Create composite indexes for efficient querying
    __table_args__ = (
        Index('idx_session_message_rating', 'session_id', 'message_id'),
        Index('idx_rating_timestamp', 'rating', 'created_at'),
        Index('idx_user_ratings', 'user_id', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert rating model to dictionary representation.
        """
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message_id": self.message_id,
            "user_id": self.user_id,
            "rating": self.rating,
            "feedback_text": self.feedback_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.rating_metadata
        }
