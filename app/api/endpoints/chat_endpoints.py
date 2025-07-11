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
from app.core.orchestrator import generate_agent, Output, Source, Usage, UsageDetails
from app.core.event_orchestrator import generate_agent_with_events, EventTrackingContext
from app.utils.security import validate_api_key, require_read_permission, require_write_permission, require_delete_permission, APIKeyInfo

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request and response
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Session ID can be provided by frontend
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What services does the government provide for business registration?",
                "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "user_id": "user123",
                "metadata": {"platform": "web", "language": "en"}
            }
        }

class ChatResponse(Output):
    """
    Chat response model that extends the Output model with chat-specific fields.
    """
    session_id: str = Field(
        description="Unique identifier for the chat session"
    )
    
    trace_id: Optional[str] = Field(
        default=None,
        description="Optional trace ID for monitoring and debugging"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "answer": "To register a business in Kenya, you need to follow these steps...",
                "sources": [
                    {
                        "title": "Business Registration Guidelines", 
                        "url": "https://example.gov/business-reg",
                        "snippet": "The Business Registration Service (BRS) is a state corporation that registers businesses in Kenya."
                    }
                ],
                "confidence": 0.92,
                "retriever_type": "brs",
                "trace_id": "7fa85f64-5717-4562-b3fc-2c963f66afa7",
                "usage": {
                    "requests": 1,
                    "request_tokens": 891,
                    "response_tokens": 433,
                    "total_tokens": 1324,
                    "details": {
                        "accepted_prediction_tokens": 0,
                        "audio_tokens": 0,
                        "reasoning_tokens": 0,
                        "rejected_prediction_tokens": 0,
                        "cached_tokens": 0
                    }
                },
                "recommended_follow_up_questions": [
                    {
                        "question": "What are the funding opportunities available for filmmakers in Kenya?",
                        "relevance_score": 0.85
                    },
                    {
                        "question": "How does the Kenya Film Commission support local filmmakers?",
                        "relevance_score": 0.90
                    }
                ]
            }
        }

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    num_messages: int  # Total number of messages
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "messages": [
                    {
                        "id": 1,
                        "message_id": "msg1",
                        "message_type": "user",
                        "message_object": {"query": "What services does the government provide for business registration?"},
                        "timestamp": "2023-10-20T14:30:15.123456"
                    },
                    {
                        "id": 2,
                        "message_id": "msg2",
                        "message_type": "assistant",
                        "message_object": {
                            "answer": "To register a business in Kenya, you need to follow these steps...",
                            "sources": [{"title": "Business Registration Guidelines", "url": "https://example.gov/business-reg"}],
                            "confidence": 0.92,
                            "retriever_type": "brs",  # Changed from "hybrid" to a valid collection ID
                            "usage": {
                                "requests": 1,
                                "request_tokens": 891,
                                "response_tokens": 433,
                                "total_tokens": 1324,
                                "details": {
                                    "accepted_prediction_tokens": 0,
                                    "audio_tokens": 0,
                                    "reasoning_tokens": 0,
                                    "rejected_prediction_tokens": 0,
                                    "cached_tokens": 0
                                }
                            }
                        },
                        "timestamp": "2023-10-20T14:30:18.654321"
                    }
                ],
                "user_id": "user123",
                "created_at": "2023-10-20T14:30:15.123456",
                "updated_at": "2023-10-20T14:30:18.654321",
                "message_count": 2,
                "num_messages": 2
            }
        }


@router.post("/", response_model=ChatResponse)
async def process_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_write_permission)
) -> ChatResponse:
    """
    Process a chat message, creating a new session if needed or continuing an existing one.
    Requires write permission.
    
    Args:
        request: The chat request containing the message, session_id (if continuing), and user data
        db: Database session
        
    Returns:
        Chat response containing the session ID and agent output
    """
    from app.utils.chat_event_service import ChatEventService
    
    trace_id = str(uuid.uuid4())  # Generate a unique trace ID for logging
    session_id = request.session_id
    message_id = str(uuid.uuid4())  # Generate unique message ID for event tracking
    
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
        # Event: Message received
        await ChatEventService.create_event(
            db, session_id, "message_received", "started", message_id
        )
        
        start_time = datetime.now()
        
        # Event: Loading history (if not new session)
        if not is_new_session:
            await ChatEventService.create_event(
                db, session_id, "loading_history", "started", message_id
            )
        
        # Create agent and load message history if available
        # Use event-aware agent with tracking context
        with EventTrackingContext(db, session_id, message_id):
            agent = generate_agent_with_events()
            message_history = await ChatPersistenceService.load_history(db, session_id)
        
        if not is_new_session:
            await ChatEventService.create_event(
                db, session_id, "loading_history", "completed", message_id
            )
        
        # Event: Message validated and ready for processing
        await ChatEventService.create_event(
            db, session_id, "message_received", "completed", message_id
        )
        
        # Save the user message first
        user_message_obj = {"query": request.message}
        await ChatPersistenceService.save_message(
            db, 
            session_id, 
            "user", 
            user_message_obj
        )
        
        # Event: Agent thinking
        await ChatEventService.create_event(
            db, session_id, "agent_thinking", "started", message_id
        )
        
        # Process the message with history if available
        # Run agent within event tracking context
        with EventTrackingContext(db, session_id, message_id):
            if message_history:
                logger.info(f"[{trace_id}] Processing message with history for session: {session_id}")
                result = await agent.run(request.message, message_history=message_history)
            else:
                logger.info(f"[{trace_id}] Processing message without history for session: {session_id}")
                result = await agent.run(request.message)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        processing_time_ms = int(processing_time * 1000)
        logger.info(f"[{trace_id}] Processed message in {processing_time:.2f} seconds")
        
        # Event: Agent thinking completed
        await ChatEventService.create_event(
            db, session_id, "agent_thinking", "completed", message_id, 
            processing_time_ms=processing_time_ms
        )
        
        # Event: Response generation
        await ChatEventService.create_event(
            db, session_id, "response_generation", "started", message_id
        )
        
        # Get usage information
        usage_info = convert_usage(result.usage())
        
        # Create assistant message object with empty follow-up questions
        assistant_message_obj = {
            "session_id": session_id,
            "answer": result.output.answer,
            "sources": result.output.sources,
            "confidence": result.output.confidence,
            "retriever_type": result.output.retriever_type,
            "trace_id": trace_id,
            "recommended_follow_up_questions": [],
            "usage": usage_info.dict() if usage_info else None
        }
        
        # Event: Response generation completed
        await ChatEventService.create_event(
            db, session_id, "response_generation", "completed", message_id
        )
        
        # Event: Saving message
        await ChatEventService.create_event(
            db, session_id, "saving_message", "started", message_id
        )
        
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
            await ChatEventService.create_event(
                db, session_id, "error", "failed", message_id,
                event_data={"error_message": "Failed to save chat messages"}
            )
            raise HTTPException(status_code=500, detail="Failed to save chat messages")
        
        # Event: Message saved successfully
        await ChatEventService.create_event(
            db, session_id, "saving_message", "completed", message_id
        )
        
        # Return the response with empty follow-up questions
        response = ChatResponse(
            session_id=session_id,
            answer=result.output.answer,
            sources=result.output.sources,
            confidence=result.output.confidence,
            retriever_type=result.output.retriever_type,
            trace_id=trace_id,
            recommended_follow_up_questions=[],
            usage=usage_info
        )
        
        return response
    
    except HTTPException:
        # Log error event for HTTP exceptions
        await ChatEventService.create_event(
            db, session_id, "error", "failed", message_id,
            event_data={"error_message": "HTTP error occurred during processing"}
        )
        raise
    except Exception as e:
        # Log error event for general exceptions
        await ChatEventService.create_event(
            db, session_id, "error", "failed", message_id,
            event_data={"error_message": f"Internal server error: {str(e)}"}
        )
        logger.error(f"[{trace_id}] Error processing chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str = Path(..., description="The ID of the chat session to retrieve"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
) -> ChatHistoryResponse:
    """
    Retrieve the history of a chat session.
    Requires read permission.
    
    Args:
        session_id: The ID of the chat session to retrieve
        db: Database session
        
    Returns:
        Chat history response containing all messages in the session
    """
    trace_id = str(uuid.uuid4())
    logger.info(f"[{trace_id}] Retrieving chat history for session: {session_id}")
    
    try:
        # Get the chat session with properly loaded messages
        chat_with_messages = await ChatPersistenceService.get_chat_with_messages(db, session_id)
        if not chat_with_messages:
            logger.warning(f"[{trace_id}] Chat session {session_id} not found")
            raise HTTPException(status_code=404, detail=f"Chat session {session_id} not found")
        
        chat = chat_with_messages["chat"]
        messages = chat_with_messages["messages"]
        
        # Format messages for response
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "id": msg.id,
                "message_id": msg.message_id,
                "message_type": msg.message_type,
                "message_object": msg.message_object,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
            })
        
        # Return the chat history
        return ChatHistoryResponse(
            session_id=session_id,
            messages=formatted_messages,
            user_id=chat.user_id,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            message_count=len(formatted_messages),
            num_messages=len(formatted_messages)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{trace_id}] Error retrieving chat history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{session_id}")
async def delete_chat(
    session_id: str = Path(..., description="The ID of the chat session to delete"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_delete_permission)
) -> Dict[str, str]:
    """
    Delete a chat session and all its messages.
    Requires delete permission.
    
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

# Helper function to convert pydantic-ai usage to our Usage model
def convert_usage(pydantic_ai_usage) -> Optional[Usage]:
    """Convert pydantic-ai usage object to our Usage model."""
    if not pydantic_ai_usage:
        return None
    
    usage_dict = pydantic_ai_usage.__dict__
    
    return Usage(
        requests=usage_dict.get('requests', 0),
        request_tokens=usage_dict.get('request_tokens', 0),
        response_tokens=usage_dict.get('response_tokens', 0),
        total_tokens=usage_dict.get('total_tokens', 0),
        details=UsageDetails(
            accepted_prediction_tokens=usage_dict.get('details', {}).get('accepted_prediction_tokens', 0),
            audio_tokens=usage_dict.get('details', {}).get('audio_tokens', 0),
            reasoning_tokens=usage_dict.get('details', {}).get('reasoning_tokens', 0),
            rejected_prediction_tokens=usage_dict.get('details', {}).get('rejected_prediction_tokens', 0),
            cached_tokens=usage_dict.get('details', {}).get('cached_tokens', 0)
        )
    )
