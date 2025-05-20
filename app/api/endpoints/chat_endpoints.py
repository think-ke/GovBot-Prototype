"""
Chat endpoints for the GovStack API.
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import logging
import uuid
from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelMessagesTypeAdapter

from app.db.database import get_db
from app.utils.chat_persistence import ChatPersistenceService
from app.core.orchestrator import generate_agent, Output

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request and response
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Session ID can be provided by frontend
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[Dict[str, str]] = []
    confidence: float
    retriever_type: str
    trace_id: Optional[str] = None  # Optional trace ID for monitoring

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    num_messages: int  # Total number of messages


@router.post("/", response_model=ChatResponse)
async def process_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Process a chat message, creating a new session if needed or continuing an existing one.
    
    Args:
        request: The chat request containing the message, session_id (if continuing), and user data
        db: Database session
        
    Returns:
        Chat response containing the session ID and agent output
    """
    trace_id = str(uuid.uuid4())  # Generate a unique trace ID for logging
    session_id = request.session_id
    
    # New conversation (no session_id provided) or continuing conversation
    is_new_session = not session_id
    
    if is_new_session:
        logger.info(f"[{trace_id}] Creating new chat session for user: {request.user_id}")
        # Create a new chat session
        session_id = await ChatPersistenceService.create_chat_session(db, request.user_id)
    else:
        logger.info(f"[{trace_id}] Using existing session ID: {session_id}")
        # Check if the chat session exists
        chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
        if not chat:
            logger.warning(f"[{trace_id}] Chat session {session_id} not found, creating new session")
            await ChatPersistenceService.create_chat_session_with_id(db, session_id, request.user_id)
    
    try:
        start_time = datetime.now()
        
        # Create agent and load message history if available
        agent = generate_agent()
        message_history = await ChatPersistenceService.load_history(db, session_id)
        
        # Save the user message first
        user_message_obj = {"query": request.message}
        await ChatPersistenceService.save_message(
            db, 
            session_id, 
            "user", 
            user_message_obj
        )
        
        # Process the message with history if available
        if message_history:
            logger.info(f"[{trace_id}] Processing message with history for session: {session_id}")
            result = agent.run_sync(request.message, message_history=message_history)
        else:
            logger.info(f"[{trace_id}] Processing message without history for session: {session_id}")
            result = agent.run_sync(request.message)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"[{trace_id}] Processed message in {processing_time:.2f} seconds")
        
        # Create assistant message object
        assistant_message_obj = {
            "session_id": session_id,
            "answer": result.output.answer,
            "sources": result.output.sources,
            "confidence": result.output.confidence,
            "retriever_type": result.output.retriever_type,
            "trace_id": trace_id
        }
        
        # Save the assistant message with history
        history = result.all_messages()
        history_as_python = to_jsonable_python(history)
        success = await ChatPersistenceService.save_message(
            db, 
            session_id, 
            "assistant", 
            assistant_message_obj,
            history=history_as_python
        )
            
        if not success:
            logger.error(f"[{trace_id}] Failed to save chat messages for session: {session_id}")
            raise HTTPException(status_code=500, detail="Failed to save chat messages")
        
        # Return the response
        return ChatResponse(
            session_id=session_id,
            answer=result.output.answer,
            sources=result.output.sources,
            confidence=result.output.confidence,
            retriever_type=result.output.retriever_type,
            trace_id=trace_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{trace_id}] Error processing chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str = Path(..., description="The ID of the chat session to retrieve"),
    db: AsyncSession = Depends(get_db)
) -> ChatHistoryResponse:
    """
    Retrieve the history of a chat session.
    
    Args:
        session_id: The ID of the chat session to retrieve
        db: Database session
        
    Returns:
        Chat history response containing all messages in the session
    """
    trace_id = str(uuid.uuid4())
    logger.info(f"[{trace_id}] Retrieving chat history for session: {session_id}")
    
    try:
        # Get the chat session
        chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
        if not chat:
            logger.warning(f"[{trace_id}] Chat session {session_id} not found")
            raise HTTPException(status_code=404, detail=f"Chat session {session_id} not found")
        
        # Get all messages for this chat
        messages = []
        for msg in chat.messages:
            messages.append({
                "id": msg.id,
                "message_id": msg.message_id,
                "message_type": msg.message_type,
                "message_object": msg.message_object,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
            })
        
        # Return the chat history
        return ChatHistoryResponse(
            session_id=session_id,
            messages=messages,
            user_id=chat.user_id,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            message_count=len(messages),
            num_messages=len(messages)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{trace_id}] Error retrieving chat history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{session_id}")
async def delete_chat(
    session_id: str = Path(..., description="The ID of the chat session to delete"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete a chat session and all its messages.
    
    Args:
        session_id: The ID of the chat session to delete
        db: Database session
        
    Returns:
        Confirmation message
    """
    try:
        # Delete the chat session
        success = await ChatPersistenceService.delete_chat_session(db, session_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Chat session {session_id} not found")
        
        return {"message": f"Chat session {session_id} deleted successfully"}
    
    except Exception as e:
        logger.error(f"Error deleting chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
