"""
Webpage storage model for database records tracking crawled web pages.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.db.models.document import Base

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
    # Audit trail fields
    created_by = Column(String(100), nullable=True, index=True)  # User ID who initiated the crawl
    updated_by = Column(String(100), nullable=True, index=True)  # User ID who last updated the webpage
    api_key_name = Column(String(100), nullable=True, index=True)  # API key name used for crawl
    
    # Links relationship
    outgoing_links = relationship("WebpageLink", foreign_keys="WebpageLink.source_id", back_populates="source")
    incoming_links = relationship("WebpageLink", foreign_keys="WebpageLink.target_id", back_populates="target")    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert webpage model to dictionary representation.
        """
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "content_hash": self.content_hash,
            "last_crawled": self.last_crawled.isoformat() if self.last_crawled else None,
            "first_crawled": self.first_crawled.isoformat() if self.first_crawled else None,            
            "crawl_depth": self.crawl_depth,
            "status_code": self.status_code,
            "error": self.error,
            "meta_data": self.meta_data,            "is_seed": self.is_seed,
            "content_type": self.content_type,
            "collection_id": self.collection_id,
            "is_indexed": self.is_indexed,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "api_key_name": self.api_key_name,
        }


class WebpageLink(Base):
    """
    Model for tracking links between webpages.
    """
    __tablename__ = "webpage_links"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("webpages.id"), nullable=False)    
    target_id = Column(Integer, ForeignKey("webpages.id"), nullable=False)
    text = Column(String(512), nullable=True)  # Anchor text
    rel = Column(String(100), nullable=True)  # Link rel attribute
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    source = relationship("Webpage", foreign_keys=[source_id], back_populates="outgoing_links")
    target = relationship("Webpage", foreign_keys=[target_id], back_populates="incoming_links")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert link model to dictionary representation.
        """
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "text": self.text,
            "rel": self.rel,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
