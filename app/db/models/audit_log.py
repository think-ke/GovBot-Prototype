"""
Audit log model for tracking user actions across the system.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AuditLog(Base):
    """
    Model for tracking all user actions across the system.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)  # API key name or user identifier
    action = Column(String(100), nullable=False, index=True)  # Action performed (e.g., 'create', 'update', 'delete', 'upload', 'crawl')
    resource_type = Column(String(50), nullable=False, index=True)  # Type of resource (e.g., 'document', 'webpage', 'collection')
    resource_id = Column(String(100), nullable=True, index=True)  # ID of the affected resource
    details = Column(JSON, nullable=True)  # Additional details about the action
    ip_address = Column(String(45), nullable=True)  # IP address of the user (IPv4 or IPv6)
    user_agent = Column(Text, nullable=True)  # User agent string
    api_key_name = Column(String(100), nullable=False, index=True)  # Name of the API key used
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Add composite indexes for common queries
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_action_resource', 'action', 'resource_type'),
        Index('idx_resource_lookup', 'resource_type', 'resource_id'),
        Index('idx_api_key_timestamp', 'api_key_name', 'timestamp'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert audit log model to dictionary representation.
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "api_key_name": self.api_key_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
