"""
Chat endpoints for the GovStack API.
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import logging
import json
import uuid
import traceback
from pydantic_ai.messages import ModelMessage

from app.api.fast_api_app import get_db
from app.utils.chat_persistence import ChatPersistenceService
from app.core.orchestrator import generate_agent, Output

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request and response
class ChatRequest(BaseModel):
    message: str
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
async def create_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Create a new chat session and process the initial message.
    
    Args:
        request: The chat request containing the message and optional user data
        db: Database session
        
    Returns:
        Chat response containing the session ID and agent output
    """
    trace_id = str(uuid.uuid4())  # Generate a unique trace ID for logging
    logger.info(f"[{trace_id}] Creating new chat session for user: {request.user_id}")
    
    try:
        # Create a new chat session
        session_id = await ChatPersistenceService.create_chat_session(db, request.user_id)
        
        # Generate agent and process the message
        agent = generate_agent()
        start_time = datetime.now()
        result = agent.run_sync(request.message)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"[{trace_id}] Processed message in {processing_time:.2f} seconds")
        
        # Save the messages to the database
        success = await ChatPersistenceService.save_messages(db, session_id, result.all_messages())
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
    
    except Exception as e:
        logger.error(f"[{trace_id}] Error creating chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{session_id}", response_model=ChatResponse)
async def continue_chat(
    session_id: str = Path(..., description="The ID of the chat session to continue"),
    request: ChatRequest = Body(...),
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Continue an existing chat session with a new message.
    
    Args:
        session_id: The ID of the chat session to continue
        request: The chat request containing the message
        db: Database session
        
    Returns:
        Chat response containing the agent output
    """
    trace_id = str(uuid.uuid4())  # Generate a unique trace ID for logging
    logger.info(f"[{trace_id}] Continuing chat session: {session_id}")
    
    try:
        # Check if the chat session exists
        chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
        if not chat:
            logger.warning(f"[{trace_id}] Chat session {session_id} not found")
            raise HTTPException(status_code=404, detail=f"Chat session {session_id} not found")
        
        # Load the previous messages
        message_history = await ChatPersistenceService.load_messages(db, session_id)
        
        start_time = datetime.now()
        
        if not message_history:
            # If no messages found, start a new conversation
            logger.info(f"[{trace_id}] No previous messages found for session {session_id}, starting fresh")
            agent = generate_agent()
        else:
            # Continue the conversation with previous context
            logger.info(f"[{trace_id}] Loaded {len(message_history)} previous messages")
            
            # Truncate history if it's getting too long (to avoid token limits)
            if len(message_history) > 20:
                logger.info(f"[{trace_id}] Truncating message history from {len(message_history)} to 20 messages")
                from app.core.orchestrator import truncate_message_history
                message_history = truncate_message_history(message_history, 20)
            
            agent = generate_agent(message_history=message_history)
        
        # Process the message
        result = agent.run_sync(request.message)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"[{trace_id}] Processed message in {processing_time:.2f} seconds")
        
        # Save the new messages to the database
        # We only save the new messages to avoid duplicating existing ones
        success = await ChatPersistenceService.save_messages(db, session_id, result.new_messages())
        if not success:
            logger.error(f"[{trace_id}] Failed to save new messages for session: {session_id}")
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
        logger.error(f"[{trace_id}] Error continuing chat: {str(e)}", exc_info=True)
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
            # Ensure content is valid JSON
            try:
                content = json.loads(msg.content)
            except json.JSONDecodeError:
                content = {"text": msg.content}
            
            # Format timestamp as ISO string if it exists
            timestamp = msg.timestamp.isoformat() if msg.timestamp else None
            
            messages.append({
                "id": msg.id,
                "message_type": msg.message_type,
                "content": content,
                "timestamp": timestamp,
                "metadata": msg.metadata,
                "message_idx": msg.message_idx
            })
        
        # Return the chat history
        return ChatHistoryResponse(
            session_id=session_id,
            messages=messages,
            user_id=chat.user_id,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
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
