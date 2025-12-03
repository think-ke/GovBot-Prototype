"""
Main orchestrator module - now using LlamaIndex FunctionAgent as the primary implementation.
This module provides the new LlamaIndex implementation and maintains backward compatibility.
"""

import yaml
import os
import logging
import asyncio
from typing import List, Optional, Any, Dict, Union

# Initialize logger first
logger = logging.getLogger(__name__)

# Import the new LlamaIndex implementation with aliases to avoid conflicts
from app.core.llamaindex_orchestrator import (
    run_llamaindex_agent,
    generate_llamaindex_agent,
    Output as LlamaIndexOutput,
    Source as LlamaIndexSource,
    Usage as LlamaIndexUsage,
    UsageDetails as LlamaIndexUsageDetails,
    FollowUpQuestion as LlamaIndexFollowUpQuestion
)

# Import compatibility layer
from app.core.compatibility_orchestrator import CompatibilityAgent

# Legacy imports for backward compatibility
from app.utils.prompts import SYSTEM_PROMPT
from app.core.rag.tool_loader import tools, collection_dict
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()

# Re-export the LlamaIndex models as the main models
Output = LlamaIndexOutput
Source = LlamaIndexSource
Usage = LlamaIndexUsage
UsageDetails = LlamaIndexUsageDetails
FollowUpQuestion = LlamaIndexFollowUpQuestion


# Main agent generation functions using the new LlamaIndex implementation
def generate_agent(tools=None) -> CompatibilityAgent:
    """
    Generate an agent using the new LlamaIndex backend with compatibility wrapper.
    
    Args:
        tools: Legacy parameter (ignored, tools are loaded internally)
        
    Returns:
        CompatibilityAgent that uses LlamaIndex FunctionAgent
    """
    logger.info("Creating agent with LlamaIndex FunctionAgent backend")
    return CompatibilityAgent()


def generate_agent_with_events(tools=None) -> CompatibilityAgent:
    """
    Generate an agent with event tracking using LlamaIndex backend.
    
    Args:
        tools: Legacy parameter (ignored, tools are loaded internally)
        
    Returns:
        CompatibilityAgent that uses LlamaIndex FunctionAgent
    """
    logger.info("Creating agent with event tracking and LlamaIndex FunctionAgent backend")
    return CompatibilityAgent()


def generate_li_agent(tools=None, collection_dict: Optional[Dict[str, Any]] = None):
    """
    Generate a LlamaIndex FunctionAgent directly.
    
    Args:
        tools: Legacy parameter (ignored)
        collection_dict: Collection metadata
        
    Returns:
        LlamaIndex FunctionAgent instance
    """
    logger.info("Creating LlamaIndex FunctionAgent directly")
    return generate_llamaindex_agent()


# Expose the new LlamaIndex functions for direct use
run_agent = run_llamaindex_agent
create_agent = generate_llamaindex_agent


if __name__ == "__main__":
    # Example usage of the new LlamaIndex-based system
    async def main():
        """Test the new LlamaIndex agent implementation."""
        
        # Test with compatibility wrapper
        agent = generate_agent()
        response = await agent.run(
            "What services does the Kenya Film Commission provide?",
            session_id="test-session"
        )
        
        print("Compatibility Response:", response.output.answer)
        print("Sources:", len(response.output.sources))
        print("Confidence:", response.output.confidence)
        
        # Test direct LlamaIndex usage
        direct_response = await run_llamaindex_agent(
            "What are the requirements for business registration in Kenya?",
            session_id="test-direct"
        )
        
        print("\nDirect LlamaIndex Response:", direct_response.answer)
        print("Retriever Type:", direct_response.retriever_type)
        print("Follow-up Questions:", [q.question for q in direct_response.recommended_follow_up_questions])
    
    # Run the test
    asyncio.run(main())
