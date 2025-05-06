"""
Document storage model for database records tracking files in MinIO.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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
    upload_date = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    metadata = Column(JSON, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert document model to dictionary representation.
        """
        return {
            "id": self.id,
            "filename": self.filename,
            "object_name": self.object_name,
            "content_type": self.content_type,
            "size": self.size,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "description": self.description,
            "is_public": self.is_public,
            "metadata": self.metadata,
        }