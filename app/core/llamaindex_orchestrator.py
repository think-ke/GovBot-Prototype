"""
LlamaIndex FunctionAgent implementation to replace Pydantic-AI.
"""

import os
import yaml
import logging
from typing import List, Optional, Any, Dict, Union, Callable
from contextvars import ContextVar
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
from app.utils.fallbacks import get_no_answer_message, get_out_of_scope_message
from app.core.rag.tool_loader import collection_dict, get_index_dict, get_alias_map
from app.utils.chat_event_service import ChatEventService
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Settings
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small", embed_batch_size=100
)

# Context for event tracking (optional; set by run_llamaindex_agent when db/session is provided)
session_id_context: ContextVar[Optional[str]] = ContextVar('session_id', default=None)
db_context: ContextVar[Optional[AsyncSession]] = ContextVar('db', default=None)

async def _emit_event(event_type: str, event_status: str, event_data: Optional[Dict] = None) -> None:
    """Emit a chat event if context is available; noop otherwise."""
    try:
        sid = session_id_context.get()
        db = db_context.get()
        if sid and db:
            await ChatEventService.create_event(
                db=db,
                session_id=sid,
                event_type=event_type,
                event_status=event_status,
                event_data=event_data or {},
            )
    except Exception as e:
        # Do not fail agent flow due to telemetry
        logger.debug(f"Event emit skipped/error: {e}")

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
        await _emit_event("tool_search_documents", "started", {"collection": "kfc"})
        indexes = get_index_dict()
        index = indexes["kfc"]
        retriever = index.as_retriever(similarity_top_k=3)
        nodes = await retriever.aretrieve(query)

        if not nodes:
            await _emit_event("tool_search_documents", "completed", {"collection": "kfc", "count": 0})
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
        await _emit_event("tool_search_documents", "completed", {"collection": "kfc", "count": len(nodes)})
        return f"Kenya Film Commission Information:\n\n{formatted_response}"

    except Exception as e:
        logger.error(f"Error querying KFC: {e}")
        await _emit_event("tool_search_documents", "failed", {"collection": "kfc", "error": str(e)})
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
        await _emit_event("tool_search_documents", "started", {"collection": "kfcb"})
        indexes = get_index_dict()
        index = indexes["kfcb"]
        retriever = index.as_retriever(similarity_top_k=3)
        nodes = await retriever.aretrieve(query)

        if not nodes:
            await _emit_event("tool_search_documents", "completed", {"collection": "kfcb", "count": 0})
            return "No relevant information found in the Kenya Film Classification Board collection."

        response_parts = []
        for i, node in enumerate(nodes[:3]):
            response_parts.append(f"Source {i+1}: {node.text[:500]}...")

        formatted_response = "\n\n".join(response_parts)
        await _emit_event("tool_search_documents", "completed", {"collection": "kfcb", "count": len(nodes)})
        return f"Kenya Film Classification Board Information:\n\n{formatted_response}"

    except Exception as e:
        logger.error(f"Error querying KFCB: {e}")
        await _emit_event("tool_search_documents", "failed", {"collection": "kfcb", "error": str(e)})
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
        await _emit_event("tool_search_documents", "started", {"collection": "brs"})
        indexes = get_index_dict()
        index = indexes["brs"]
        retriever = index.as_retriever(similarity_top_k=3)
        nodes = await retriever.aretrieve(query)

        if not nodes:
            await _emit_event("tool_search_documents", "completed", {"collection": "brs", "count": 0})
            return "No relevant information found in the Business Registration Service collection."

        response_parts = []
        for i, node in enumerate(nodes[:3]):
            response_parts.append(f"Source {i+1}: {node.text[:500]}...")

        formatted_response = "\n\n".join(response_parts)
        await _emit_event("tool_search_documents", "completed", {"collection": "brs", "count": len(nodes)})
        return f"Business Registration Service Information:\n\n{formatted_response}"

    except Exception as e:
        logger.error(f"Error querying BRS: {e}")
        await _emit_event("tool_search_documents", "failed", {"collection": "brs", "error": str(e)})
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
        await _emit_event("tool_search_documents", "started", {"collection": "odpc"})
        indexes = get_index_dict()
        index = indexes["odpc"]
        retriever = index.as_retriever(similarity_top_k=3)
        nodes = await retriever.aretrieve(query)

        if not nodes:
            await _emit_event("tool_search_documents", "completed", {"collection": "odpc", "count": 0})
            return "No relevant information found in the Office of the Data Protection Commissioner collection."

        response_parts = []
        for i, node in enumerate(nodes[:3]):
            response_parts.append(f"Source {i+1}: {node.text[:500]}...")

        formatted_response = "\n\n".join(response_parts)
        await _emit_event("tool_search_documents", "completed", {"collection": "odpc", "count": len(nodes)})
        return f"Office of the Data Protection Commissioner Information:\n\n{formatted_response}"

    except Exception as e:
        logger.error(f"Error querying ODPC: {e}")
        await _emit_event("tool_search_documents", "failed", {"collection": "odpc", "error": str(e)})
        return f"Error retrieving information from Office of the Data Protection Commissioner: {str(e)}"


def create_llamaindex_tools(agencies: Optional[Union[str, List[str]]] = None) -> List[FunctionTool]:
    """
    Create FunctionTool objects dynamically from collections. Supports filtering by:
    - alias (e.g., kfc)
    - canonical collection ID (UUID)
    - collection name (case-insensitive)
    """

    def _slugify(text: str) -> str:
        import re
        s = text.lower()
        s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
        return s or "collection"

    # Ensure metadata is loaded
    meta = collection_dict or {}
    alias_map = get_alias_map()  # alias -> canonical
    # Prefer stable alias names where available for tool naming
    preferred_alias_order = ["kfc", "kfcb", "brs", "odpc"]
    canonical_to_alias: Dict[str, str] = {}
    for alias in preferred_alias_order:
        can = alias_map.get(alias)
        if can:
            canonical_to_alias[str(can)] = alias

    # Build a reverse lookup for names -> canonical id
    name_to_canonical: Dict[str, str] = {}
    for cid, info in meta.items():
        name = info.get("collection_name") or info.get("name") or str(cid)
        name_to_canonical[name.lower()] = str(cid)

    # Build dynamic async functions per collection key
    def _make_query_fn(key: str, display_name: str) -> Callable[[str], Any]:
        async def _fn(query: str) -> str:
            try:
                # Emit started event for dynamic tools
                await _emit_event("tool_search_documents", "started", {"collection": key})
                indexes = get_index_dict()
                index = indexes[key]
                retriever = index.as_retriever(similarity_top_k=3)
                nodes = await retriever.aretrieve(query)
                if not nodes:
                    await _emit_event("tool_search_documents", "completed", {"collection": key, "count": 0})
                    return f"No relevant information found in the {display_name} collection."
                parts = []
                for i, node in enumerate(nodes[:3]):
                    text = getattr(node, "text", "")
                    parts.append(f"Source {i+1}: {text[:500]}...")
                await _emit_event("tool_search_documents", "completed", {"collection": key, "count": len(nodes)})
                return f"{display_name} Information:\n\n" + "\n\n".join(parts)
            except Exception as e:
                logger.error(f"Error querying {display_name} ({key}): {e}")
                await _emit_event("tool_search_documents", "failed", {"collection": key, "error": str(e)})
                return f"Error retrieving information from {display_name}: {str(e)}"

        return _fn

    # Construct all available tools
    dynamic_tools: Dict[str, FunctionTool] = {}
    for cid, info in meta.items():
        canonical = str(cid)
        display = info.get("collection_name") or info.get("name") or canonical
        # choose stable handle
        handle = canonical_to_alias.get(canonical) or _slugify(display)
        tool_name = f"query_{handle}"
        async_fn = _make_query_fn(handle if handle in get_index_dict() else canonical, display)
        desc = f"Query the {display} collection for information relevant to its domain."
        dynamic_tools[handle] = FunctionTool.from_defaults(async_fn=async_fn, name=tool_name, description=desc)

    # Maintain legacy aliases explicitly if they exist in index dict (ensures backwards compat)
    for alias in ["kfc", "kfcb", "brs", "odpc"]:
        if alias in dynamic_tools:
            continue
        if alias in get_index_dict():
            # create a thin wrapper pointing to alias key
            display = alias.upper()
            async_fn = _make_query_fn(alias, display)
            dynamic_tools[alias] = FunctionTool.from_defaults(
                async_fn=async_fn,
                name=f"query_{alias}",
                description=f"Query the {display} collection."
            )

    # Filtering logic
    def _resolve_to_handle(token: str) -> Optional[str]:
        t = (token or "").strip()
        if not t:
            return None
        lower = t.lower()
        # alias direct
        if lower in dynamic_tools:
            return lower
        # alias -> canonical -> alias
        can = alias_map.get(lower)
        if can and str(can) in canonical_to_alias:
            return canonical_to_alias[str(can)]
        # canonical id direct -> alias or slug handle
        if lower in meta:
            info = meta.get(lower, {})
            name = info.get("collection_name") or info.get("name") or lower
            return canonical_to_alias.get(lower) or _slugify(name)
        # name -> canonical -> alias/slug
        can2 = name_to_canonical.get(lower)
        if can2:
            return canonical_to_alias.get(str(can2)) or _slugify(meta[can2]["collection_name"]) if meta.get(can2) else None
        # canonical id -> alias/slug
        if lower in canonical_to_alias:
            return canonical_to_alias[lower]
        return None

    if agencies is None:
        selected = list(dynamic_tools.values())
    elif isinstance(agencies, str):
        handle = _resolve_to_handle(agencies)
        if handle and handle in dynamic_tools:
            selected = [dynamic_tools[handle]]
        else:
            logger.warning(f"Unknown agency '{agencies}'. Returning all tools.")
            selected = list(dynamic_tools.values())
    elif isinstance(agencies, list):
        selected = []
        for a in agencies:
            handle = _resolve_to_handle(a)
            if handle and handle in dynamic_tools:
                selected.append(dynamic_tools[handle])
            else:
                logger.warning(f"Unknown agency '{a}'. Skipping.")
        if not selected:
            logger.warning("No valid agencies found. Returning all tools.")
            selected = list(dynamic_tools.values())
    else:
        logger.warning(f"Invalid agencies parameter type: {type(agencies)}. Returning all tools.")
        selected = list(dynamic_tools.values())

    logger.info(f"Created {len(selected)} dynamic FunctionTools for agencies: {agencies}")
    return selected


def _derive_bot_name(agencies: Optional[Union[str, List[str]]]) -> str:
    """Return a custom bot name based on the agency filter."""
    base = "GovBot"
    if agencies is None:
        return base
    if isinstance(agencies, str):
        return f"{base}-{agencies.upper()}"
    if isinstance(agencies, list) and agencies:
        suffix = "-".join(a.upper() for a in agencies)
        return f"{base}-{suffix}"
    return base


def build_system_prompt(agencies: Optional[Union[str, List[str]]] = None) -> str:
    """
    Build a system prompt tailored to the provided agency/agencies.
    - Customizes the bot name per agency.
    - Adds a brief agency focus note.
    - Falls back to the original prompt when no agency is specified.
    The returned string still contains the {collections} placeholder for later formatting.
    """
    prompt = SYSTEM_PROMPT
    # Customize name everywhere the base prompt references GovBot
    bot_name = _derive_bot_name(agencies)
    prompt = prompt.replace("GovBot", bot_name)

    # Add agency focus and strict guardrails. Keep the collections placeholder intact.
    if agencies:
        if isinstance(agencies, str):
            agency_key = agencies.upper()
            agency_note = (
                f"\n\nAgency focus: This assistant is specialized for the {agency_key} collection and related services."
                f"\n\nSTRICT AGENCY GUARDRAILS\n"
                f"- Only answer questions that are clearly within the scope of {agency_key} and its official mandate.\n"
                f"- If a question is outside {agency_key}'s scope (or ambiguous), DO NOT answer it. Respond instead with: \"I'm {bot_name}, and I'm specialized in {agency_key}. I can't help with unrelated topics. Please ask about {agency_key}-related services or policies.\"\n"
                f"- Prioritize information from the {agency_key} collection(s). Do not reference other agencies unless explicitly asked to compare with {agency_key}.\n"
            )
        else:
            joined = ", ".join(a.upper() for a in agencies)
            agency_note = (
                f"\n\nAgency focus: This assistant is specialized for the following collections: {joined}."
                f"\n\nSTRICT AGENCY GUARDRAILS\n"
                f"- Only answer questions that are clearly within the scope of these agencies: {joined}.\n"
                f"- If a question is outside these agencies' scope (or ambiguous), DO NOT answer it. Respond instead with: \"I'm {bot_name}, and I'm specialized in {joined}. I can't help with unrelated topics. Please ask about these agencies' services or policies.\"\n"
                f"- Prioritize information from the specified collections only. Do not reference other agencies unless explicitly asked to compare with the specified ones.\n"
            )
        prompt = prompt + agency_note
    return prompt


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
    
    # Build and format the system prompt with agency-specific name/context
    base_prompt = build_system_prompt(agencies)
    
    # Format collections in a readable way (collection name as key instead of ID)
    if collection_dict:
        readable_collections = {}
        for cid, info in collection_dict.items():
            collection_name = info.get("collection_name", cid)
            readable_collections[collection_name] = {
                "description": info.get("collection_description", "")
            }
        collections_text = yaml.dump(readable_collections, default_flow_style=False)
    else:
        collections_text = "No collections available"
    
    formatted_system_prompt = base_prompt.format(collections=collections_text)
    
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
    def process_response(agent_response, retriever_type: str = "unknown", language: Optional[str] = None) -> Output:
        """
        Convert LlamaIndex agent response to our Output format.
        
        Args:
            agent_response: The response from the LlamaIndex agent
            retriever_type: The type of retriever used
            
        Returns:
            Output object with structured response data
        """
        # Extract the main response text
        response_text = (str(agent_response) or "").strip()
        if not response_text:
            response_text = get_no_answer_message(language)

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
    agencies: Optional[Union[str, List[str]]] = None,
    language: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db: Optional[AsyncSession] = None
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
    # Set context for events if provided
    if db and session_id:
        try:
            session_id_context.set(session_id)
            db_context.set(db)
        except Exception:
            pass
    # Emit agent invocation start
    await _emit_event("agent_invocation", "started", {"agencies": agencies if agencies is not None else "all"})
    
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
    
    # Basic scope guard: if message appears entirely off-topic, return out-of-scope message
    off_topic_indicators = [
        "recipe", "football", "movie actor", "dating", "stock tips", "crypto pump"
    ]
    if any(t in message.lower() for t in off_topic_indicators):
        return Output(
            answer=get_out_of_scope_message(language=language),
            sources=[],
            confidence=0.0,
            retriever_type=retriever_type,
            usage=Usage(requests=1, request_tokens=0, response_tokens=0, total_tokens=0),
            recommended_follow_up_questions=[]
        )

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
            response, retriever_type=retriever_type, language=language
        )

        logger.info(f"Successfully processed LlamaIndex agent response for session {session_id}")
        await _emit_event("agent_invocation", "completed", {"agencies": agencies if agencies is not None else "all"})
        return processed_response

    except Exception as e:
        logger.error(f"Error running LlamaIndex agent: {e}")
        await _emit_event("agent_invocation", "failed", {"error": str(e), "agencies": agencies if agencies is not None else "all"})
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
