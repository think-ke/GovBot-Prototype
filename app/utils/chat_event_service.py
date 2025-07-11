"""
Chat event service for managing real-time event tracking.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat_event import ChatEvent

logger = logging.getLogger(__name__)

# Event types and user-friendly messages mapping
EVENT_MESSAGES = {
    # Core chat processing
    "message_received": {
        "started": "📩 Processing your message...",
        "completed": "✅ Message received and validated"
    },
    
    # Agent processing phases
    "agent_thinking": {
        "started": "🤔 AI is analyzing your question...",
        "progress": "🧠 Understanding context and requirements...",
        "completed": "✅ Analysis complete"
    },
    
    # Tool execution
    "tool_search_documents": {
        "started": "📄 Searching relevant documents...",
        "progress": "🔍 Found {count} potential matches...",
        "completed": "✅ Document search complete"
    },
    
    "tool_search_webpages": {
        "started": "🌐 Searching web content...",
        "progress": "🔍 Analyzing {count} web pages...",
        "completed": "✅ Web search complete"
    },
    
    "tool_collection_stats": {
        "started": "📊 Gathering collection statistics...",
        "completed": "✅ Statistics retrieved"
    },
    
    "tool_extract_text": {
        "started": "📝 Extracting relevant text content...",
        "progress": "🔍 Processing {count} sources...",
        "completed": "✅ Text extraction complete"
    },
    
    # Response generation
    "response_generation": {
        "started": "✍️ Generating response...",
        "progress": "📝 Crafting answer with sources...",
        "completed": "✅ Response ready"
    },
    
    # Database operations
    "saving_message": {
        "started": "💾 Saving conversation...",
        "completed": "✅ Conversation saved"
    },
    
    "loading_history": {
        "started": "📚 Loading conversation history...",
        "completed": "✅ History loaded"
    },
    
    # Error states
    "error": {
        "failed": "❌ {error_message}"
    }
}


class ChatEventService:
    """Service for managing chat events and real-time tracking."""
    
    @staticmethod
    async def create_event(
        db: AsyncSession,
        session_id: str,
        event_type: str,
        event_status: str,
        message_id: Optional[str] = None,
        event_data: Optional[Dict] = None,
        processing_time_ms: Optional[int] = None,
        custom_message: Optional[str] = None
    ) -> Optional[ChatEvent]:
        """
        Create and store a new chat event.
        
        Args:
            db: Database session
            session_id: The chat session ID
            event_type: Type of event (see EVENT_MESSAGES keys)
            event_status: Status of the event ('started', 'progress', 'completed', 'failed')
            message_id: Optional message ID this event relates to
            event_data: Optional additional event data
            processing_time_ms: Optional processing time in milliseconds
            custom_message: Optional custom user message (overrides default)
            
        Returns:
            Created ChatEvent instance or None if failed
        """
        try:
            # Generate user-friendly message
            user_message = custom_message
            if not user_message:
                user_message = ChatEventService._generate_user_message(
                    event_type, event_status, event_data
                )
            
            # Create event
            event = ChatEvent(
                session_id=session_id,
                message_id=message_id,
                event_type=event_type,
                event_status=event_status,
                event_data=event_data,
                user_message=user_message,
                processing_time_ms=processing_time_ms
            )
            
            db.add(event)
            await db.commit()
            await db.refresh(event)
            
            logger.debug(f"Created event: {event_type}:{event_status} for session {session_id}")
            return event
            
        except Exception as e:
            logger.error(f"Error creating chat event: {str(e)}")
            await db.rollback()
            return None
    
    @staticmethod
    async def get_session_events(
        db: AsyncSession,
        session_id: str,
        since_timestamp: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ChatEvent]:
        """
        Get events for a session, optionally since a timestamp.
        
        Args:
            db: Database session
            session_id: The chat session ID
            since_timestamp: Optional timestamp to filter events after
            limit: Maximum number of events to return
            
        Returns:
            List of ChatEvent instances
        """
        try:
            query = select(ChatEvent).where(ChatEvent.session_id == session_id)
            
            if since_timestamp:
                query = query.where(ChatEvent.timestamp > since_timestamp)
            
            query = query.order_by(ChatEvent.timestamp.desc()).limit(limit)
            
            result = await db.execute(query)
            events = result.scalars().all()
            
            # Return in chronological order (oldest first)
            return list(reversed(events))
            
        except Exception as e:
            logger.error(f"Error getting session events: {str(e)}")
            return []
    
    @staticmethod
    async def get_latest_events(
        db: AsyncSession,
        session_id: str,
        count: int = 10
    ) -> List[ChatEvent]:
        """
        Get the latest events for a session.
        
        Args:
            db: Database session
            session_id: The chat session ID
            count: Number of latest events to return
            
        Returns:
            List of latest ChatEvent instances
        """
        try:
            query = select(ChatEvent).where(
                ChatEvent.session_id == session_id
            ).order_by(ChatEvent.timestamp.desc()).limit(count)
            
            result = await db.execute(query)
            events = result.scalars().all()
            
            return list(reversed(events))  # Return in chronological order
            
        except Exception as e:
            logger.error(f"Error getting latest events: {str(e)}")
            return []
    
    @staticmethod
    async def cleanup_old_events(
        db: AsyncSession,
        hours_old: int = 24
    ) -> int:
        """
        Clean up events older than specified hours.
        
        Args:
            db: Database session
            hours_old: Age threshold in hours
            
        Returns:
            Number of deleted events
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_old)
            
            query = delete(ChatEvent).where(ChatEvent.timestamp < cutoff_time)
            result = await db.execute(query)
            await db.commit()
            
            deleted_count = result.rowcount
            logger.info(f"Cleaned up {deleted_count} old chat events")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old events: {str(e)}")
            await db.rollback()
            return 0
    
    @staticmethod
    def _generate_user_message(
        event_type: str,
        event_status: str,
        event_data: Optional[Dict] = None
    ) -> str:
        """
        Generate user-friendly message for an event.
        
        Args:
            event_type: Type of event
            event_status: Status of the event
            event_data: Optional event data for formatting
            
        Returns:
            User-friendly message string
        """
        try:
            # Get message template
            event_messages = EVENT_MESSAGES.get(event_type, {})
            message_template = event_messages.get(event_status, f"{event_type}:{event_status}")
            
            # Format with event data if available
            if event_data and isinstance(message_template, str):
                try:
                    return message_template.format(**event_data)
                except (KeyError, ValueError):
                    # If formatting fails, return template as-is
                    return message_template
            
            return message_template
            
        except Exception as e:
            logger.error(f"Error generating user message: {str(e)}")
            return f"{event_type}:{event_status}"
    
    @staticmethod
    async def mark_event_completed(
        db: AsyncSession,
        session_id: str,
        event_type: str,
        message_id: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
        event_data: Optional[Dict] = None
    ) -> Optional[ChatEvent]:
        """
        Mark an event as completed by creating a completion event.
        
        Args:
            db: Database session
            session_id: The chat session ID
            event_type: Type of event to mark as completed
            message_id: Optional message ID
            processing_time_ms: Optional processing time
            event_data: Optional event data
            
        Returns:
            Created completion event or None
        """
        return await ChatEventService.create_event(
            db=db,
            session_id=session_id,
            event_type=event_type,
            event_status="completed",
            message_id=message_id,
            processing_time_ms=processing_time_ms,
            event_data=event_data
        )
    
    @staticmethod
    async def mark_event_failed(
        db: AsyncSession,
        session_id: str,
        event_type: str,
        error_message: str,
        message_id: Optional[str] = None
    ) -> Optional[ChatEvent]:
        """
        Mark an event as failed with error details.
        
        Args:
            db: Database session
            session_id: The chat session ID
            event_type: Type of event that failed
            error_message: Error message to display to user
            message_id: Optional message ID
            
        Returns:
            Created error event or None
        """
        return await ChatEventService.create_event(
            db=db,
            session_id=session_id,
            event_type=event_type,
            event_status="failed",
            message_id=message_id,
            event_data={"error_message": error_message},
            custom_message=f"❌ {error_message}"
        )
