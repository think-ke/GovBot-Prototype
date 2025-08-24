"""
Compatibility wrapper for transitioning from Pydantic-AI to LlamaIndex FunctionAgent.
This module provides a bridge to maintain existing API compatibility while using the new LlamaIndex backend.
"""

import logging
from typing import List, Optional, Any, Dict, Union
from llama_index.core.base.llms.types import ChatMessage
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from app.core.llamaindex_orchestrator import (
    run_llamaindex_agent, 
    Output, 
    Source, 
    Usage, 
    UsageDetails, 
    FollowUpQuestion
)

logger = logging.getLogger(__name__)


def convert_pydantic_ai_messages_to_llamaindex(messages: List[ModelMessage]) -> List[ChatMessage]:
    """
    Convert Pydantic-AI ModelMessage objects to LlamaIndex ChatMessage objects.
    
    Args:
        messages: List of Pydantic-AI ModelMessage objects
        
    Returns:
        List of LlamaIndex ChatMessage objects
    """
    llamaindex_messages = []
    
    for msg in messages:
        # Extract role and content from Pydantic-AI message
        if hasattr(msg, 'kind'):
            # Handle different Pydantic-AI message types
            if msg.kind == 'request':
                role = "user"
                # Extract content from parts
                content_parts = []
                for part in msg.parts:
                    part_kind = getattr(part, 'part_kind', None)
                    part_content = getattr(part, 'content', None)
                    
                    if part_kind and part_content and part_kind in ['user-prompt', 'system-prompt', 'retry-prompt']:
                        content_parts.append(str(part_content))
                content = " ".join(content_parts) if content_parts else str(msg)
                
            elif msg.kind == 'response':
                role = "assistant"
                # Extract content from parts
                content_parts = []
                for part in msg.parts:
                    part_kind = getattr(part, 'part_kind', None)
                    part_content = getattr(part, 'content', None)
                    
                    if part_kind and part_content and part_kind in ['text', 'thinking']:
                        content_parts.append(str(part_content))
                content = " ".join(content_parts) if content_parts else str(msg)
            else:
                # Default handling
                role = "user"
                content = str(msg)
        elif isinstance(msg, dict):
            # Handle dict-like messages
            role = msg.get('role', 'user')
            content = str(msg.get('content', ''))
        else:
            # Fallback for unknown message structure
            role = "user"
            content = str(msg)
        
        llamaindex_messages.append(ChatMessage(role=role, content=content))
    
    return llamaindex_messages


def convert_chat_history_to_llamaindex(chat_history: List[Dict[str, Any]]) -> List[ChatMessage]:
    """
    Convert chat history from database format to LlamaIndex ChatMessage objects.
    
    Args:
        chat_history: List of chat messages from database
        
    Returns:
        List of LlamaIndex ChatMessage objects
    """
    llamaindex_messages = []
    
    for msg in chat_history:
        if isinstance(msg, dict):
            role = msg.get('role', 'user')
            content = msg.get('content', '')
        else:
            # Handle other formats
            role = getattr(msg, 'role', 'user')
            content = getattr(msg, 'content', str(msg))
        
        llamaindex_messages.append(ChatMessage(role=role, content=content))
    
    return llamaindex_messages


class CompatibilityAgent:
    """
    Compatibility wrapper that mimics the Pydantic-AI Agent interface while using LlamaIndex backend.
    """
    
    def __init__(self):
        """Initialize the compatibility agent."""
        logger.info("Initializing CompatibilityAgent with LlamaIndex backend")
    
    async def run(
        self, 
        user_msg: str, 
        message_history: Optional[List[ModelMessage]] = None,
        session_id: Optional[str] = None
    ) -> 'CompatibilityResponse':
        """
        Run the agent with a user message and optional message history.
        
        Args:
            user_msg: User message to process
            message_history: Optional Pydantic-AI message history
            session_id: Optional session ID
            
        Returns:
            CompatibilityResponse object that mimics Pydantic-AI response
        """
        logger.info(f"Running compatibility agent for session {session_id}")
        
        # Convert message history if provided
        chat_history = None
        if message_history:
            chat_history = convert_pydantic_ai_messages_to_llamaindex(message_history)
        
        # Run the LlamaIndex agent
        response = await run_llamaindex_agent(
            message=user_msg,
            chat_history=chat_history,
            session_id=session_id
        )
        
        # Wrap in compatibility response
        return CompatibilityResponse(output=response, raw_response=response)
    
    def run_sync(
        self, 
        user_msg: str, 
        message_history: Optional[List[ModelMessage]] = None,
        session_id: Optional[str] = None
    ) -> 'CompatibilityResponse':
        """
        Synchronous version of run method.
        
        Args:
            user_msg: User message to process
            message_history: Optional Pydantic-AI message history
            session_id: Optional session ID
            
        Returns:
            CompatibilityResponse object that mimics Pydantic-AI response
        """
        import asyncio
        return asyncio.run(self.run(user_msg, message_history, session_id))


class CompatibilityResponse:
    """
    Compatibility response object that mimics Pydantic-AI response structure.
    """
    
    def __init__(self, output: Output, raw_response: Any):
        """
        Initialize compatibility response.
        
        Args:
            output: Processed Output object
            raw_response: Raw response from LlamaIndex
        """
        self.output = output
        self._raw_response = raw_response
        self._messages = []  # Placeholder for message history
    
    def data(self) -> Output:
        """Return the output data (for Pydantic-AI compatibility)."""
        return self.output
    
    def all_messages(self) -> List[Dict[str, Any]]:
        """
        Return all messages from the conversation (for Pydantic-AI compatibility).
        
        Returns:
            List of message dictionaries
        """
        # Return a simplified message history
        return [
            {"role": "assistant", "content": self.output.answer}
        ]
    
    def usage(self) -> Usage:
        """Return usage information."""
        return self.output.usage or Usage(
            requests=1, 
            request_tokens=0, 
            response_tokens=0, 
            total_tokens=0
        )
    
    def __str__(self) -> str:
        """String representation of the response."""
        return self.output.answer


# Factory function to create agents (for backward compatibility)
def generate_agent() -> CompatibilityAgent:
    """
    Generate a compatibility agent that uses LlamaIndex backend.
    
    Returns:
        CompatibilityAgent instance
    """
    logger.info("Creating compatibility agent with LlamaIndex backend")
    return CompatibilityAgent()


def generate_agent_with_events() -> CompatibilityAgent:
    """
    Generate a compatibility agent with event tracking support.
    
    Returns:
        CompatibilityAgent instance (events will be handled separately)
    """
    logger.info("Creating compatibility agent with event tracking support")
    # For now, return the same agent - events can be handled in the API layer
    return CompatibilityAgent()


# Export the main classes and functions for backward compatibility
__all__ = [
    'CompatibilityAgent',
    'CompatibilityResponse', 
    'generate_agent',
    'generate_agent_with_events',
    'Output',
    'Source',
    'Usage',
    'UsageDetails',
    'FollowUpQuestion',
    'convert_pydantic_ai_messages_to_llamaindex',
    'convert_chat_history_to_llamaindex'
]
