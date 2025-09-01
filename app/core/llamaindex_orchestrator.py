"""
LlamaIndex FunctionAgent implementation to replace Pydantic-AI.
"""

import os
import yaml
import logging
from typing import List, Optional, Any, Dict, Union
from dotenv import load_dotenv

from llama_index.core import Settings
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool
from llama_index.core.base.llms.types import ChatMessage
from llama_index.llms.openai import OpenAI
from llama_index.llms.groq import Groq
from llama_index.embeddings.openai import OpenAIEmbedding
from pydantic import BaseModel, Field

from app.utils.prompts import SYSTEM_PROMPT
from app.core.rag.tool_loader import collection_dict, get_index_dict

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Settings
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small", embed_batch_size=100
)

# Configure LLM based on environment
if os.getenv("GROQ_MODEL_NAME") is None:
    Settings.llm = OpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    logger.info("Using OpenAI model: gpt-4o-mini")
else:
    groq_model_name = os.getenv('GROQ_MODEL_NAME', 'llama-3.3-70b-versatile')
    Settings.llm = Groq(
        model=groq_model_name, 
        api_key=os.getenv("GROQ_API_KEY")
    )
    logger.info(f"Using Groq model: {groq_model_name}")


class Source(BaseModel):
    """Represents a source of information referenced in the answer."""
    title: str = Field(description="The title of the source document")
    url: str = Field(description="The URL where the source document can be accessed")
    snippet: Optional[str] = Field(
        None, 
        description="A relevant excerpt from the source document that supports the answer",
        max_length=1000
    )


class UsageDetails(BaseModel):
    """Usage details from the model response."""
    accepted_prediction_tokens: int = Field(default=0)
    audio_tokens: int = Field(default=0)
    reasoning_tokens: int = Field(default=0)
    rejected_prediction_tokens: int = Field(default=0)
    cached_tokens: int = Field(default=0)


class Usage(BaseModel):
    """Usage information from the model response."""
    requests: int = Field(description="Number of requests made")
    request_tokens: int = Field(description="Number of tokens in the request")
    response_tokens: int = Field(description="Number of tokens in the response")
    total_tokens: int = Field(description="Total number of tokens used")
    details: UsageDetails = Field(default_factory=UsageDetails)


class FollowUpQuestion(BaseModel):
    """Represents a recommended follow-up question related to the user's query."""
    question: str = Field(description="The recommended follow-up question for the user")
    relevance_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class Output(BaseModel):
    """Structured output format for agent responses with source attribution and metadata."""
    answer: str = Field(description="The comprehensive answer to the user's question")
    sources: List[Source] = Field(default_factory=list)
    confidence: float = Field(description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0)
    retriever_type: str = Field(description="Identifier for the knowledge collection used")
    usage: Optional[Usage] = Field(default=None)
    recommended_follow_up_questions: List[FollowUpQuestion] = Field(default_factory=list)


# Tool functions for LlamaIndex FunctionAgent
async def query_kfc_tool(query: str) -> str:
    """
    Query the Kenya Film Commission collection for information about film industry services and support.
    
    Args:
        query: Search query related to Kenya Film Commission
        
    Returns:
        Formatted response with relevant information and sources
    """
    logger.info(f"Querying Kenya Film Commission with: {query}")
    
    try:
        indexes = get_index_dict()
        index = indexes["kfc"]
        retriever = index.as_retriever(similarity_top_k=3)
        nodes = await retriever.aretrieve(query)
        
        if not nodes:
            return "No relevant information found in the Kenya Film Commission collection."
        
        # Format response with sources
        response_parts = []
        sources = []
        
        for i, node in enumerate(nodes[:3]):  # Limit to top 3 results
            response_parts.append(f"Source {i+1}: {node.text[:500]}...")
            sources.append({
                "title": f"KFC Document {i+1}",
                "content": node.text,
                "score": node.score if hasattr(node, 'score') else 0.0
            })
        
        formatted_response = "\n\n".join(response_parts)
        return f"Kenya Film Commission Information:\n\n{formatted_response}"
        
    except Exception as e:
        logger.error(f"Error querying KFC: {e}")
        return f"Error retrieving information from Kenya Film Commission: {str(e)}"


async def query_kfcb_tool(query: str) -> str:
    """
    Query the Kenya Film Classification Board collection for film regulation and classification information.
    
    Args:
        query: Search query related to Kenya Film Classification Board
        
    Returns:
        Formatted response with relevant information and sources
    """
    logger.info(f"Querying Kenya Film Classification Board with: {query}")
    
    try:
        indexes = get_index_dict()
        index = indexes["kfcb"]
        retriever = index.as_retriever(similarity_top_k=3)
        nodes = await retriever.aretrieve(query)
        
        if not nodes:
            return "No relevant information found in the Kenya Film Classification Board collection."
        
        response_parts = []
        for i, node in enumerate(nodes[:3]):
            response_parts.append(f"Source {i+1}: {node.text[:500]}...")
        
        formatted_response = "\n\n".join(response_parts)
        return f"Kenya Film Classification Board Information:\n\n{formatted_response}"
        
    except Exception as e:
        logger.error(f"Error querying KFCB: {e}")
        return f"Error retrieving information from Kenya Film Classification Board: {str(e)}"


async def query_brs_tool(query: str) -> str:
    """
    Query the Business Registration Service collection for business registration information.
    
    Args:
        query: Search query related to Business Registration Service
        
    Returns:
        Formatted response with relevant information and sources
    """
    logger.info(f"Querying Business Registration Service with: {query}")
    
    try:
        indexes = get_index_dict()
        index = indexes["brs"]
        retriever = index.as_retriever(similarity_top_k=3)
        nodes = await retriever.aretrieve(query)
        
        if not nodes:
            return "No relevant information found in the Business Registration Service collection."
        
        response_parts = []
        for i, node in enumerate(nodes[:3]):
            response_parts.append(f"Source {i+1}: {node.text[:500]}...")
        
        formatted_response = "\n\n".join(response_parts)
        return f"Business Registration Service Information:\n\n{formatted_response}"
        
    except Exception as e:
        logger.error(f"Error querying BRS: {e}")
        return f"Error retrieving information from Business Registration Service: {str(e)}"


async def query_odpc_tool(query: str) -> str:
    """
    Query the Office of the Data Protection Commissioner collection for data protection information.
    
    Args:
        query: Search query related to Office of the Data Protection Commissioner
        
    Returns:
        Formatted response with relevant information and sources
    """
    logger.info(f"Querying Office of the Data Protection Commissioner with: {query}")
    
    try:
        indexes = get_index_dict()
        index = indexes["odpc"]
        retriever = index.as_retriever(similarity_top_k=3)
        nodes = await retriever.aretrieve(query)
        
        if not nodes:
            return "No relevant information found in the Office of the Data Protection Commissioner collection."
        
        response_parts = []
        for i, node in enumerate(nodes[:3]):
            response_parts.append(f"Source {i+1}: {node.text[:500]}...")
        
        formatted_response = "\n\n".join(response_parts)
        return f"Office of the Data Protection Commissioner Information:\n\n{formatted_response}"
        
    except Exception as e:
        logger.error(f"Error querying ODPC: {e}")
        return f"Error retrieving information from Office of the Data Protection Commissioner: {str(e)}"


def create_llamaindex_tools(agencies: Optional[Union[str, List[str]]] = None) -> List[FunctionTool]:
    """
    Create LlamaIndex FunctionTool objects from our async tool functions.
    
    Args:
        agencies: Optional agency filter. Can be:
                 - None: Returns all tools
                 - str: Returns tool for single agency (e.g., "kfc", "kfcb", "brs", "odpc")
                 - List[str]: Returns tools for multiple agencies
    
    Returns:
        List of FunctionTool objects filtered by agencies
    """
    # Define all available tools
    all_tools = {
        "kfc": FunctionTool.from_defaults(
            async_fn=query_kfc_tool,
            name="query_kfc",
            description="Query the Kenya Film Commission collection for information about film industry services, support, licensing, and regulations in Kenya."
        ),
        "kfcb": FunctionTool.from_defaults(
            async_fn=query_kfcb_tool,
            name="query_kfcb", 
            description="Query the Kenya Film Classification Board collection for information about film classification, content regulation, and broadcast compliance in Kenya."
        ),
        "brs": FunctionTool.from_defaults(
            async_fn=query_brs_tool,
            name="query_brs",
            description="Query the Business Registration Service collection for information about business registration, company formation, and related government services in Kenya."
        ),
        "odpc": FunctionTool.from_defaults(
            async_fn=query_odpc_tool,
            name="query_odpc",
            description="Query the Office of the Data Protection Commissioner collection for information about data protection laws, privacy rights, and compliance requirements in Kenya."
        )
    }
    
    # Filter tools based on agencies parameter
    if agencies is None:
        # Return all tools
        selected_tools = list(all_tools.values())
    elif isinstance(agencies, str):
        # Single agency
        agencies_lower = agencies.lower()
        if agencies_lower in all_tools:
            selected_tools = [all_tools[agencies_lower]]
        else:
            logger.warning(f"Unknown agency '{agencies}'. Available agencies: {list(all_tools.keys())}")
            selected_tools = list(all_tools.values())
    elif isinstance(agencies, list):
        # Multiple agencies
        selected_tools = []
        for agency in agencies:
            agency_lower = agency.lower()
            if agency_lower in all_tools:
                selected_tools.append(all_tools[agency_lower])
            else:
                logger.warning(f"Unknown agency '{agency}'. Available agencies: {list(all_tools.keys())}")
        
        # If no valid agencies were found, return all tools
        if not selected_tools:
            logger.warning("No valid agencies found. Returning all tools.")
            selected_tools = list(all_tools.values())
    else:
        logger.warning(f"Invalid agencies parameter type: {type(agencies)}. Returning all tools.")
        selected_tools = list(all_tools.values())
    
    logger.info(f"Created {len(selected_tools)} LlamaIndex FunctionTools for agencies: {agencies}")
    return selected_tools


def generate_llamaindex_agent(agencies: Optional[Union[str, List[str]]] = None) -> FunctionAgent:
    """
    Generate a LlamaIndex FunctionAgent with tools and system prompt.
    
    Args:
        agencies: Optional agency filter for tools. Can be:
                 - None: Uses all available tools
                 - str: Uses tool for single agency (e.g., "kfc", "kfcb", "brs", "odpc")
                 - List[str]: Uses tools for multiple agencies
    
    Returns:
        Initialized FunctionAgent
    """
    logger.info("Starting LlamaIndex FunctionAgent creation process")
    
    # Create tools with optional filtering
    tools = create_llamaindex_tools(agencies)
    
    # Format system prompt with collection information
    formatted_system_prompt = SYSTEM_PROMPT.format(
        collections=yaml.dump(collection_dict) if collection_dict else "No collections available"
    )
    
    # Create the FunctionAgent
    agent = FunctionAgent(
        tools=tools,
        llm=Settings.llm,
        system_prompt=formatted_system_prompt,
        verbose=True
    )
    
    logger.info(f"LlamaIndex FunctionAgent created with {len(tools)} tools available for agencies: {agencies}")
    return agent


class LlamaIndexResponseProcessor:
    """Process LlamaIndex agent responses into our expected Output format."""
    
    @staticmethod
    def process_response(agent_response, retriever_type: str = "unknown") -> Output:
        """
        Convert LlamaIndex agent response to our Output format.
        
        Args:
            agent_response: The response from the LlamaIndex agent
            retriever_type: The type of retriever used
            
        Returns:
            Output object with structured response data
        """
        # Extract the main response text
        response_text = str(agent_response)
        
        # Extract sources from the response if available
        sources = []
        # TODO: Implement source extraction logic based on response content
        
        # Generate follow-up questions based on the response
        follow_up_questions = LlamaIndexResponseProcessor._generate_follow_up_questions(response_text)
        
        # Create usage information (placeholder for now)
        usage = Usage(
            requests=1,
            request_tokens=0,  # LlamaIndex doesn't expose this easily
            response_tokens=0,
            total_tokens=0,
            details=UsageDetails()
        )
        
        return Output(
            answer=response_text,
            sources=sources,
            confidence=0.8,  # Default confidence score
            retriever_type=retriever_type,
            usage=usage,
            recommended_follow_up_questions=follow_up_questions
        )
    
    @staticmethod
    def _generate_follow_up_questions(response_text: str) -> List[FollowUpQuestion]:
        """Generate follow-up questions based on the response content."""
        # Basic follow-up question generation
        # This could be enhanced with LLM-based generation
        follow_up_questions = []
        
        if "Kenya Film Commission" in response_text:
            follow_up_questions.append(
                FollowUpQuestion(
                    question="What are the funding opportunities available for filmmakers in Kenya?",
                    relevance_score=0.85
                )
            )
        
        if "Business Registration Service" in response_text:
            follow_up_questions.append(
                FollowUpQuestion(
                    question="What documents are required for business registration in Kenya?",
                    relevance_score=0.90
                )
            )
        
        if "Data Protection" in response_text:
            follow_up_questions.append(
                FollowUpQuestion(
                    question="What are the penalties for data protection violations in Kenya?",
                    relevance_score=0.88
                )
            )
        
        return follow_up_questions


async def run_llamaindex_agent(
    message: str, 
    chat_history: Optional[List[ChatMessage]] = None,
    session_id: Optional[str] = None,
    agencies: Optional[Union[str, List[str]]] = None
) -> Output:
    """
    Run the LlamaIndex agent with a message and optional chat history.
    
    Args:
        message: User message to process
        chat_history: Optional chat history as LlamaIndex ChatMessage objects
        session_id: Optional session ID for tracking
        agencies: Optional agency filter for tools. Can be:
                 - None: Uses all available tools
                 - str: Uses tool for single agency (e.g., "kfc", "kfcb", "brs", "odpc")
                 - List[str]: Uses tools for multiple agencies
        
    Returns:
        Output object with structured response
    """
    logger.info(f"Running LlamaIndex agent for session {session_id} with agencies: {agencies}")
    
    # Create agent with optional agency filtering
    agent = generate_llamaindex_agent(agencies)
    
    # Determine retriever type based on message content
    retriever_type = "general"
    if any(term in message.lower() for term in ["film", "movie", "cinema"]):
        if "classification" in message.lower() or "regulation" in message.lower():
            retriever_type = "kfcb"
        else:
            retriever_type = "kfc"
    elif any(term in message.lower() for term in ["business", "company", "registration"]):
        retriever_type = "brs"
    elif any(term in message.lower() for term in ["data", "privacy", "protection"]):
        retriever_type = "odpc"
    
    try:
        # Run the agent
        if chat_history:
            # If we have chat history, we need to add the current message
            current_history = chat_history.copy()
            response = await agent.run(message, chat_history=current_history)
        else:
            response = await agent.run(message)

        logger.info(f"LlamaIndex agent response received for session {session_id} : {response}")

        # Process the response into our expected format
        processed_response = LlamaIndexResponseProcessor.process_response(
            response, retriever_type=retriever_type
        )
        
        logger.info(f"Successfully processed LlamaIndex agent response for session {session_id}")
        return processed_response
        
    except Exception as e:
        logger.error(f"Error running LlamaIndex agent: {e}")
        # Return error response in expected format
        return Output(
            answer=f"I apologize, but I encountered an error while processing your request: {str(e)}",
            sources=[],
            confidence=0.0,
            retriever_type=retriever_type,
            usage=Usage(requests=1, request_tokens=0, response_tokens=0, total_tokens=0),
            recommended_follow_up_questions=[]
        )


if __name__ == "__main__":
    import asyncio
    
    async def test_llamaindex_agent():
        """Test the LlamaIndex agent implementation."""
        
        # Test basic functionality with all tools
        print("=== Testing with all tools ===")
        response = await run_llamaindex_agent(
            "What services does the Kenya Film Commission provide?",
            session_id="test-session"
        )
        
        print("Response:", response.answer)
        print("Sources:", len(response.sources))
        print("Confidence:", response.confidence)
        print("Retriever Type:", response.retriever_type)
        print("Follow-up Questions:", [q.question for q in response.recommended_follow_up_questions])
        
        # Test with single agency filter
        print("\n=== Testing with single agency (kfc) ===")
        response_single = await run_llamaindex_agent(
            "What funding is available for filmmakers?",
            session_id="test-session-single",
            agencies="kfc"
        )
        
        print("Response:", response_single.answer)
        
        # Test with multiple agencies filter
        print("\n=== Testing with multiple agencies (brs, odpc) ===")
        response_multiple = await run_llamaindex_agent(
            "What are the data protection requirements for businesses?",
            session_id="test-session-multiple",
            agencies=["brs", "odpc"]
        )
        
        print("Response:", response_multiple.answer)
        
        # Test with invalid agency (should fallback to all tools)
        print("\n=== Testing with invalid agency ===")
        response_invalid = await run_llamaindex_agent(
            "General government information",
            session_id="test-session-invalid",
            agencies="invalid_agency"
        )
        
        print("Response:", response_invalid.answer)
        
        # Test with chat history
        chat_history = [
            ChatMessage(role="user", content="Hello, I'm interested in filmmaking in Kenya."),
            ChatMessage(role="assistant", content="I'd be happy to help you with information about filmmaking in Kenya. What specifically would you like to know?")
        ]
        
        response_with_history = await run_llamaindex_agent(
            "What support does the government provide?",
            chat_history=chat_history,
            session_id="test-session-2"
        )
        
        print("\nResponse with history:", response_with_history.answer)
    
    # Run the test
    asyncio.run(test_llamaindex_agent())
