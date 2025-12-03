"""
Collection model to persist assistant/agency collections in the database.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import Column, String, DateTime, Text, Index

# Reuse the shared Base from the document model to keep a single metadata group
from app.db.models.document import Base


class Collection(Base):
	"""
	Collections represent logical groupings of documents/webpages that power
	retrieval for a specific assistant/agency.
	"""

	__tablename__ = "collections"

	# Use string IDs so we can map to existing external identifiers if needed
	id = Column(String(64), primary_key=True, index=True)
	name = Column(String(255), unique=True, nullable=False, index=True)
	description = Column(Text, nullable=True)
	collection_type = Column(String(32), nullable=False, default="mixed")  # 'documents' | 'webpages' | 'mixed'
	api_key_name = Column(String(100), nullable=True, index=True)  # Optional owner/scope
	created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
	updated_at = Column(
		DateTime(timezone=True),
		default=lambda: datetime.now(timezone.utc),
		onupdate=lambda: datetime.now(timezone.utc),
		nullable=False,
	)

	__table_args__ = (
		Index("idx_collections_owner_name", "api_key_name", "name"),
	)

	def to_dict(self) -> Dict[str, Any]:
		created_at = getattr(self, "created_at", None)
		updated_at = getattr(self, "updated_at", None)
		return {
			"id": self.id,
			"name": self.name,
			"description": self.description,
			"collection_type": self.collection_type,
			"api_key_name": self.api_key_name,
			"created_at": created_at.isoformat() if created_at else None,
			"updated_at": updated_at.isoformat() if updated_at else None,
		}

