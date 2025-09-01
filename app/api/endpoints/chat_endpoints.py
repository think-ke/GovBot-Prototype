"""
Chat endpoints for the GovStack API.
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import uuid4
from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelMessagesTypeAdapter

from app.db.database import get_db
from app.utils.chat_persistence import ChatPersistenceService
from app.core.orchestrator import generate_agent, Output, Source, Usage, UsageDetails
from app.core.llamaindex_orchestrator import run_llamaindex_agent
from app.core.compatibility_orchestrator import convert_pydantic_ai_messages_to_llamaindex
from app.core.event_orchestrator import generate_agent_with_events, EventTrackingContext
from app.utils.security import validate_api_key, require_read_permission, require_write_permission, require_delete_permission, APIKeyInfo

# Configure logging
import logging
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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    message_count: int = 0
    num_messages: int  # Total number of messages
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


@router.post("/", response_model=ChatResponse)
async def process_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_write_permission)
) -> ChatResponse:
    """
    Process a chat message and return the AI assistant's response using LlamaIndex FunctionAgent.
    """
    try:
        logger.info(f"Processing chat request for session: {request.session_id}")
        
        # Create or retrieve session ID
        session_id = request.session_id or str(uuid4())
        
        # Handle chat persistence
        if request.session_id:
            # Check if session exists
            existing_chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
            if not existing_chat:
                # Create new session with provided ID
                await ChatPersistenceService.create_chat_session_with_id(db, session_id, request.user_id)
        else:
            # Create completely new session
            session_id = await ChatPersistenceService.create_chat_session(db, request.user_id)
        
        # Load chat history for context
        chat_history = await ChatPersistenceService.load_history(db, session_id)
        
        # Generate agent using the new LlamaIndex implementation
        agent = generate_agent()
        
        # Process the message with the agent
        # The agent.run method returns a CompatibilityResponse with .output attribute
        response = await agent.run(
            user_msg=request.message,
            message_history=chat_history,
            session_id=session_id
        )
        
        logger.info(f"Agent response for session {session_id}: {response.output.answer}")


        # Extract the structured output
        agent_output = response.output
        
        # Save the user message and assistant response
        await ChatPersistenceService.save_message(
            db=db,
            session_id=session_id,
            message_type="user",
            message_object={"content": request.message, "metadata": request.metadata or {}}
        )
        
        await ChatPersistenceService.save_message(
            db=db,
            session_id=session_id,
            message_type="assistant", 
            message_object={
                "content": agent_output.answer,
                "sources": [source.dict() for source in agent_output.sources],
                "confidence": agent_output.confidence,
                "retriever_type": agent_output.retriever_type,
                "recommended_follow_up_questions": [q.dict() for q in agent_output.recommended_follow_up_questions]
            },
            history=response.all_messages()  # Save full conversation history
        )
        
        # Create the response
        chat_response = ChatResponse(
            session_id=session_id,
            answer=agent_output.answer,
            sources=agent_output.sources,
            confidence=agent_output.confidence,
            retriever_type=agent_output.retriever_type,
            usage=agent_output.usage,
            recommended_follow_up_questions=agent_output.recommended_follow_up_questions,
            trace_id=None  # Can be enhanced with tracing later
        )
        
        logger.info(f"Successfully processed chat for session: {session_id}")
        return chat_response
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing chat message: {str(e)}"
        )


@router.post("/{agency}", response_model=ChatResponse)
async def process_chat_by_agency(
    agency: str = Path(..., description="The agency key to scope tools (e.g., kfc, kfcb, brs, odpc)"),
    request: ChatRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_write_permission)
) -> ChatResponse:
    """
    Process a chat message but scope the available tools to a specific agency.
    JSON input is identical to the default chat endpoint.
    """
    try:
        logger.info(f"Processing agency-scoped chat request for agency: {agency}, session: {request.session_id}")

        # Create or retrieve session ID
        session_id = request.session_id or str(uuid4())

        # Handle chat persistence
        if request.session_id:
            existing_chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
            if not existing_chat:
                await ChatPersistenceService.create_chat_session_with_id(db, session_id, request.user_id)
        else:
            session_id = await ChatPersistenceService.create_chat_session(db, request.user_id)

        # Load chat history for context (Pydantic-AI format) and convert to LlamaIndex ChatMessage
        history_pydantic = await ChatPersistenceService.load_history(db, session_id)
        llama_history = convert_pydantic_ai_messages_to_llamaindex(history_pydantic) if history_pydantic else None

        # Run the LlamaIndex agent directly with agency filter
        li_response: Output = await run_llamaindex_agent(
            message=request.message,
            chat_history=llama_history,
            session_id=session_id,
            agencies=agency
        )

        # Persist user and assistant messages
        await ChatPersistenceService.save_message(
            db=db,
            session_id=session_id,
            message_type="user",
            message_object={"content": request.message, "metadata": request.metadata or {}}
        )

        await ChatPersistenceService.save_message(
            db=db,
            session_id=session_id,
            message_type="assistant",
            message_object={
                "content": li_response.answer,
                "sources": [s.dict() for s in li_response.sources],
                "confidence": li_response.confidence,
                "retriever_type": li_response.retriever_type,
                "recommended_follow_up_questions": [q.dict() for q in li_response.recommended_follow_up_questions],
            },
            # Save a minimal history compatible with our loader
            history=to_jsonable_python([{"role": "assistant", "content": li_response.answer}])
        )

        # Build API response
        return ChatResponse(
            session_id=session_id,
            answer=li_response.answer,
            sources=li_response.sources,
            confidence=li_response.confidence,
            retriever_type=li_response.retriever_type,
            usage=li_response.usage,
            recommended_follow_up_questions=li_response.recommended_follow_up_questions,
            trace_id=None,
        )

    except Exception as e:
        logger.error(f"Error processing agency-scoped chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")


@router.get("/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str = Path(..., description="The ID of the chat session to retrieve"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
) -> ChatHistoryResponse:
    """
    Retrieve chat history for a specific session.
    """
    try:
        logger.info(f"Retrieving chat history for session: {session_id}")
        
        # Get chat and messages
        chat_data = await ChatPersistenceService.get_chat_with_messages(db, session_id)
        
        if not chat_data:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return ChatHistoryResponse(
            session_id=session_id,
            messages=chat_data.get("messages", []),
            user_id=chat_data.get("user_id"),
            created_at=chat_data.get("created_at") or datetime.now(),
            updated_at=chat_data.get("updated_at") or datetime.now(),
            message_count=len(chat_data.get("messages", [])),
            num_messages=len(chat_data.get("messages", []))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving chat history")


@router.delete("/{session_id}")
async def delete_chat(
    session_id: str = Path(..., description="The ID of the chat session to delete"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_delete_permission)
) -> Dict[str, str]:
    """
    Delete a chat session and all associated messages.
    """
    try:
        logger.info(f"Deleting chat session: {session_id}")
        
        success = await ChatPersistenceService.delete_chat_session(db, session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return {"message": f"Chat session {session_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat: {e}")
        raise HTTPException(status_code=500, detail="Error deleting chat session")
