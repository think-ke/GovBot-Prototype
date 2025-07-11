"""
Enhanced orchestrator with event tracking integration.
"""

from app.utils.prompts import SYSTEM_PROMPT
from app.core.rag.tool_loader import tools, collection_dict
from llama_index.core import Settings
from pydantic_ai import Agent
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Union
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_core import to_jsonable_python
from app.core.orchestrator import Output
import yaml
import os
from contextvars import ContextVar
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

# Context variables for event tracking
session_id_context: ContextVar[Optional[str]] = ContextVar('session_id', default=None)
message_id_context: ContextVar[Optional[str]] = ContextVar('message_id', default=None)
db_context: ContextVar[Optional[AsyncSession]] = ContextVar('db', default=None)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.getenv("RUNPOD_API_KEY"),
    base_url=os.getenv("RUNPOD_API_BASE_URL"),
    model=os.getenv("RUNPOD_MODEL_NAME", "gpt-4o"),
)

Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small", embed_batch_size=100
)

class EventTrackingContext:
    """Context manager for tracking events during agent execution."""
    
    def __init__(self, db: AsyncSession, session_id: str, message_id: str):
        self.db = db
        self.session_id = session_id
        self.message_id = message_id
    
    def __enter__(self):
        """Set context variables for event tracking."""
        session_id_context.set(self.session_id)
        message_id_context.set(self.message_id)
        db_context.set(self.db)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clear context variables."""
        session_id_context.set(None)
        message_id_context.set(None)
        db_context.set(None)

async def emit_tool_event(event_type: str, event_status: str, event_data: Optional[Dict] = None):
    """
    Emit a tool-related event if context is available.
    
    Args:
        event_type: Type of tool event
        event_status: Status of the event
        event_data: Optional event data
    """
    try:
        from app.utils.chat_event_service import ChatEventService
        
        session_id = session_id_context.get()
        message_id = message_id_context.get()
        db = db_context.get()
        
        if session_id and db:
            await ChatEventService.create_event(
                db=db,
                session_id=session_id,
                event_type=event_type,
                event_status=event_status,
                message_id=message_id,
                event_data=event_data
            )
    except Exception as e:
        logger.error(f"Error emitting tool event: {e}")

# Enhanced tool functions with event tracking
async def query_kfc_with_events(query: str):
    """Query KFC collection with event tracking."""
    await emit_tool_event("tool_search_documents", "started", {"collection": "kfc"})
    
    try:
        from app.core.rag.tool_loader import query_kfc
        results = await query_kfc(query)
        
        await emit_tool_event(
            "tool_search_documents", 
            "completed", 
            {"collection": "kfc", "count": len(results)}
        )
        
        return results
    except Exception as e:
        await emit_tool_event(
            "tool_search_documents", 
            "failed",
            {"collection": "kfc", "error": str(e)}
        )
        raise

async def query_kfcb_with_events(query: str):
    """Query KFCB collection with event tracking."""
    await emit_tool_event("tool_search_documents", "started", {"collection": "kfcb"})
    
    try:
        from app.core.rag.tool_loader import query_kfcb
        results = await query_kfcb(query)
        
        await emit_tool_event(
            "tool_search_documents", 
            "completed", 
            {"collection": "kfcb", "count": len(results)}
        )
        
        return results
    except Exception as e:
        await emit_tool_event(
            "tool_search_documents", 
            "failed",
            {"collection": "kfcb", "error": str(e)}
        )
        raise

async def query_brs_with_events(query: str):
    """Query BRS collection with event tracking."""
    await emit_tool_event("tool_search_documents", "started", {"collection": "brs"})
    
    try:
        from app.core.rag.tool_loader import query_brs
        results = await query_brs(query)
        
        await emit_tool_event(
            "tool_search_documents", 
            "completed", 
            {"collection": "brs", "count": len(results)}
        )
        
        return results
    except Exception as e:
        await emit_tool_event(
            "tool_search_documents", 
            "failed",
            {"collection": "brs", "error": str(e)}
        )
        raise

async def query_odpc_with_events(query: str):
    """Query ODPC collection with event tracking."""
    await emit_tool_event("tool_search_documents", "started", {"collection": "odpc"})
    
    try:
        from app.core.rag.tool_loader import query_odpc
        results = await query_odpc(query)
        
        await emit_tool_event(
            "tool_search_documents", 
            "completed", 
            {"collection": "odpc", "count": len(results)}
        )
        
        return results
    except Exception as e:
        await emit_tool_event(
            "tool_search_documents", 
            "failed",
            {"collection": "odpc", "error": str(e)}
        )
        raise

# Enhanced tools with event tracking
enhanced_tools = [
    query_kfc_with_events,
    query_kfcb_with_events, 
    query_brs_with_events,
    query_odpc_with_events
]

def generate_agent_with_events() -> Agent[None, Output]:
    """
    Generate an agent for the OpenAI model with event tracking support.
    
    Returns:
        Initialized agent with enhanced tools
    """
    collection_yml = yaml.dump(collection_dict, default_flow_style=False)
    
    # Initialize the agent with the system prompt and enhanced tools
    agent = Agent(
        model='openai:gpt-4o',
        system_prompt=SYSTEM_PROMPT.format(collections=collection_yml),
        tools=enhanced_tools,
        output_type=Output
    )
    
    return agent

# Fallback to original agent if events are not needed
def generate_agent() -> Agent[None, Output]:
    """
    Generate an agent for the OpenAI model with the original tools.
    
    Returns:
        Initialized agent
    """
    collection_yml = yaml.dump(collection_dict, default_flow_style=False)
    
    # Initialize the agent with the system prompt and original tools
    agent = Agent(
        model='openai:gpt-4o',
        system_prompt=SYSTEM_PROMPT.format(collections=collection_yml),
        tools=tools,
        output_type=Output
    )
    
    return agent
