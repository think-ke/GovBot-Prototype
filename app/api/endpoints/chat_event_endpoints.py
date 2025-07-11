"""
Chat event tracking API endpoints for real-time monitoring.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json

from app.db.database import get_db
from app.utils.security import require_read_permission, APIKeyInfo
from app.utils.chat_event_service import ChatEventService
from app.db.models.chat_event import ChatEvent
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Create router for event endpoints
router = APIRouter()

class ChatEventResponse(BaseModel):
    """Response model for chat events."""
    id: int
    session_id: str
    message_id: Optional[str] = None
    event_type: str
    event_status: str
    event_data: Optional[Dict[str, Any]] = None
    user_message: Optional[str] = None
    timestamp: str
    processing_time_ms: Optional[int] = None

class ChatEventsResponse(BaseModel):
    """Response model for multiple chat events."""
    session_id: str
    events: List[ChatEventResponse]
    total_count: int
    has_more: bool = False

# Connection manager for WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections for real-time event streaming."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a WebSocket connection and add it to the session."""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"WebSocket connected for session {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def send_event(self, session_id: str, event_data: dict):
        """Send event data to all connected clients for a session."""
        if session_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[session_id]:
                try:
                    await websocket.send_text(json.dumps(event_data))
                except Exception as e:
                    logger.error(f"Error sending event to WebSocket: {e}")
                    disconnected.append(websocket)
            
            # Remove disconnected WebSockets
            for ws in disconnected:
                self.disconnect(ws, session_id)

# Global connection manager instance
manager = ConnectionManager()

@router.get("/events/{session_id}", response_model=ChatEventsResponse)
async def get_chat_events(
    session_id: str,
    since: Optional[datetime] = Query(None, description="Get events since this timestamp"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of events to return"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    Get chat events for a session with optional filtering.
    Supports polling-based real-time updates.
    
    Args:
        session_id: The chat session ID
        since: Optional timestamp to get events after
        limit: Maximum number of events to return
        db: Database session
        
    Returns:
        List of chat events for the session
    """
    try:
        events = await ChatEventService.get_session_events(
            db=db,
            session_id=session_id,
            since_timestamp=since,
            limit=limit
        )
        
        # Convert to response format
        event_responses = []
        for event in events:
            event_dict = event.to_dict()
            event_responses.append(
                ChatEventResponse(
                    id=event_dict["id"],
                    session_id=event_dict["session_id"],
                    message_id=event_dict["message_id"],
                    event_type=event_dict["event_type"],
                    event_status=event_dict["event_status"],
                    event_data=event_dict["event_data"],
                    user_message=event_dict["user_message"],
                    timestamp=event_dict["timestamp"],
                    processing_time_ms=event_dict.get("processing_time_ms")
                )
            )
        
        return ChatEventsResponse(
            session_id=session_id,
            events=event_responses,
            total_count=len(event_responses),
            has_more=len(events) == limit  # Indicate if there might be more events
        )
        
    except Exception as e:
        logger.error(f"Error getting chat events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving events: {str(e)}")

@router.get("/events/{session_id}/latest", response_model=ChatEventsResponse)
async def get_latest_chat_events(
    session_id: str,
    count: int = Query(10, ge=1, le=50, description="Number of latest events to return"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    Get the latest chat events for a session.
    
    Args:
        session_id: The chat session ID
        count: Number of latest events to return
        db: Database session
        
    Returns:
        Latest chat events for the session
    """
    try:
        events = await ChatEventService.get_latest_events(
            db=db,
            session_id=session_id,
            count=count
        )
        
        # Convert to response format
        event_responses = []
        for event in events:
            event_dict = event.to_dict()
            event_responses.append(
                ChatEventResponse(
                    id=event_dict["id"],
                    session_id=event_dict["session_id"],
                    message_id=event_dict["message_id"],
                    event_type=event_dict["event_type"],
                    event_status=event_dict["event_status"],
                    event_data=event_dict["event_data"],
                    user_message=event_dict["user_message"],
                    timestamp=event_dict["timestamp"],
                    processing_time_ms=event_dict.get("processing_time_ms")
                )
            )
        
        return ChatEventsResponse(
            session_id=session_id,
            events=event_responses,
            total_count=len(event_responses)
        )
        
    except Exception as e:
        logger.error(f"Error getting latest chat events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving latest events: {str(e)}")

@router.websocket("/ws/events/{session_id}")
async def websocket_chat_events(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time chat event streaming.
    
    Clients can connect to this endpoint to receive real-time updates
    about chat processing events for a specific session.
    
    Args:
        websocket: WebSocket connection
        session_id: The chat session ID to monitor
    """
    await manager.connect(websocket, session_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "🔗 Connected to real-time event stream"
        }))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any client messages (like ping/pong)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle ping/pong for keepalive
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except asyncio.TimeoutError:
                # Send periodic keepalive
                await websocket.send_text(json.dumps({
                    "type": "keepalive",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }))
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket, session_id)

# Utility function to broadcast events to WebSocket clients
async def broadcast_event(session_id: str, event: ChatEvent):
    """
    Broadcast a chat event to all connected WebSocket clients for a session.
    
    Args:
        session_id: The chat session ID
        event: The ChatEvent to broadcast
    """
    try:
        event_data = {
            "type": "event",
            "event": {
                "id": event.id,
                "session_id": event.session_id,
                "message_id": event.message_id,
                "event_type": event.event_type,
                "event_status": event.event_status,
                "event_data": event.event_data,
                "user_message": event.user_message,
                "timestamp": event.timestamp.isoformat(),
                "processing_time_ms": event.processing_time_ms
            }
        }
        
        await manager.send_event(session_id, event_data)
        
    except Exception as e:
        logger.error(f"Error broadcasting event: {e}")

# Enhanced ChatEventService with WebSocket broadcasting
class ChatEventServiceWithBroadcast(ChatEventService):
    """Extended event service that broadcasts events via WebSocket."""
    
    @staticmethod
    async def create_event_with_broadcast(
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
        Create an event and broadcast it to WebSocket clients.
        
        Args:
            db: Database session
            session_id: The chat session ID
            event_type: Type of event
            event_status: Status of the event
            message_id: Optional message ID
            event_data: Optional event data
            processing_time_ms: Optional processing time
            custom_message: Optional custom message
            
        Returns:
            Created ChatEvent instance or None
        """
        # Create the event
        event = await ChatEventService.create_event(
            db=db,
            session_id=session_id,
            event_type=event_type,
            event_status=event_status,
            message_id=message_id,
            event_data=event_data,
            processing_time_ms=processing_time_ms,
            custom_message=custom_message
        )
        
        # Broadcast to WebSocket clients
        if event:
            await broadcast_event(session_id, event)
        
        return event
