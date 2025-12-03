# LlamaIndex Orchestrator Documentation

## Overview

The GovStack system has transitioned from Pydantic-AI to LlamaIndex FunctionAgent for improved RAG (Retrieval-Augmented Generation) capabilities and better tool integration. This document outlines the LlamaIndex orchestrator implementation and its features.

## Architecture

### Core Components

1. **LlamaIndex FunctionAgent**: Main AI agent for processing user queries
2. **RAG Tools**: Document and webpage search capabilities
3. **Compatibility Layer**: Maintains backward compatibility with existing APIs
4. **Settings Configuration**: LLM and embedding model configuration

### File Structure
```
app/core/
├── llamaindex_orchestrator.py     # Main LlamaIndex implementation
├── compatibility_orchestrator.py  # Backward compatibility wrapper
├── orchestrator.py               # Legacy interface (deprecated)
└── rag/
    └── tool_loader.py           # RAG tool loading and configuration
```

## LlamaIndex Implementation

### Settings Configuration

```python
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.llms.groq import Groq
from llama_index.embeddings.openai import OpenAIEmbedding

# Configure embedding model
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small", 
    embed_batch_size=100
)

# Configure LLM based on environment
if os.getenv("GROQ_MODEL_NAME") is None:
    Settings.llm = OpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY")
    )
else:
    groq_model_name = os.getenv('GROQ_MODEL_NAME', 'llama-3.3-70b-versatile')
    Settings.llm = Groq(
        model=groq_model_name, 
        api_key=os.getenv("GROQ_API_KEY")
    )
```

### Response Models

The system uses Pydantic models for structured responses:

```python
class Source(BaseModel):
    """Represents a source of information referenced in the answer."""
    title: str = Field(description="Title of the source document or webpage")
    url: Optional[str] = Field(default=None, description="URL if available")
    snippet: str = Field(description="Relevant excerpt from the source")
    score: Optional[float] = Field(default=None, description="Relevance score")

class UsageDetails(BaseModel):
    """Detailed token usage information."""
    accepted_prediction_tokens: int = 0
    audio_tokens: int = 0
    reasoning_tokens: int = 0
    rejected_prediction_tokens: int = 0
    cached_tokens: int = 0

class Usage(BaseModel):
    """Token usage and cost information."""
    requests: int = Field(description="Number of requests made")
    request_tokens: int = Field(description="Tokens used in requests")
    response_tokens: int = Field(description="Tokens used in responses")
    total_tokens: int = Field(description="Total tokens used")
    details: UsageDetails = Field(description="Detailed usage breakdown")

class FollowUpQuestion(BaseModel):
    """Suggested follow-up question."""
    question: str = Field(description="The follow-up question text")
    category: Optional[str] = Field(default=None, description="Question category")

class Output(BaseModel):
    """Main response output model."""
    answer: str = Field(description="The AI assistant's answer")
    sources: List[Source] = Field(default_factory=list, description="Sources used")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    retriever_type: str = Field(description="Type of retriever used")
    recommended_follow_up_questions: List[FollowUpQuestion] = Field(
        default_factory=list, 
        description="Suggested follow-up questions"
    )
    usage: Usage = Field(description="Token usage information")
```

### RAG Tools

The system includes specialized tools for querying different document collections:

```python
async def query_kfc_tool(query: str) -> str:
    """Query Kenya Film Commission documents."""
    
async def query_kfcb_tool(query: str) -> str:
    """Query Kenya Film Classification Board documents."""
    
async def query_brs_tool(query: str) -> str:
    """Query Business Registration Service documents."""
    
async def query_odpc_tool(query: str) -> str:
    """Query Office of the Data Protection Commissioner documents."""
```

### Tool Configuration

```python
def create_llamaindex_tools() -> List[FunctionTool]:
    """Create LlamaIndex function tools for RAG queries."""
    tools = []
    
    # Create tools for each collection
    tools.append(FunctionTool.from_defaults(
        fn=query_kfc_tool,
        name="query_kfc",
        description="Query Kenya Film Commission documents and guidelines"
    ))
    
    tools.append(FunctionTool.from_defaults(
        fn=query_kfcb_tool,
        name="query_kfcb", 
        description="Query Kenya Film Classification Board regulations and procedures"
    ))
    
    # ... additional tools
    
    return tools
```

### Agent Creation

```python
def generate_llamaindex_agent() -> FunctionAgent:
    """Create and configure the LlamaIndex FunctionAgent."""
    tools = create_llamaindex_tools()
    
    agent = FunctionAgent.from_tools(
        tools=tools,
        llm=Settings.llm,
        system_prompt=SYSTEM_PROMPT,
        verbose=True
    )
    
    return agent
```

## Compatibility Layer

To maintain backward compatibility with existing APIs, a compatibility wrapper is provided:

### CompatibilityAgent

```python
class CompatibilityAgent:
    """Compatibility wrapper for LlamaIndex agent."""
    
    def __init__(self):
        self.agent = generate_llamaindex_agent()
    
    async def run(self, message: str, message_history=None) -> CompatibilityResponse:
        """Run agent with compatibility interface."""
        return await run_llamaindex_agent(
            message=message,
            chat_history=message_history
        )
    
    def run_sync(self, message: str, message_history=None) -> CompatibilityResponse:
        """Synchronous version for backward compatibility."""
        import asyncio
        return asyncio.run(self.run(message, message_history))
```

### Message Conversion

The system includes utilities to convert between different message formats:

```python
def convert_pydantic_ai_messages_to_llamaindex(messages: List[ModelMessage]) -> List[ChatMessage]:
    """Convert Pydantic-AI messages to LlamaIndex format."""
    
def convert_chat_history_to_llamaindex(chat_history: List[Dict[str, Any]]) -> List[ChatMessage]:
    """Convert chat history from database to LlamaIndex format."""
```

## Usage Examples

### Basic Usage

```python
from app.core.llamaindex_orchestrator import run_llamaindex_agent

# Simple query
result = await run_llamaindex_agent(
    message="What services does the Kenya Film Commission provide?",
    session_id="session-123"
)

print(result.answer)
print(f"Sources found: {len(result.sources)}")
print(f"Confidence: {result.confidence}")
```

### With Chat History

```python
from llama_index.core.base.llms.types import ChatMessage

# Load previous conversation
chat_history = [
    ChatMessage(role="user", content="Tell me about business registration"),
    ChatMessage(role="assistant", content="Business registration in Kenya...")
]

# Continue conversation
result = await run_llamaindex_agent(
    message="What are the fees for this?",
    chat_history=chat_history,
    session_id="session-123"
)
```

### Compatibility Mode

```python
from app.core.compatibility_orchestrator import generate_agent

# Use legacy interface
agent = generate_agent()
result = agent.run_sync("What is the Data Protection Act?")

# Access response data
print(result.answer)
print(result.sources)
print(result.usage)
```

## Configuration

### Environment Variables

```bash
# LLM Configuration
OPENAI_API_KEY="your-openai-key"
GROQ_API_KEY="your-groq-key"  # Optional, for Groq models
GROQ_MODEL_NAME="llama-3.3-70b-versatile"  # Optional

# Vector Store Configuration
CHROMA_HOST="localhost"
CHROMA_PORT="8000"
CHROMA_USERNAME="admin"
CHROMA_PASSWORD="password"
```

### Collection Configuration

```python
collection_dict = {
    "kfc": {
        "collection_name": "Kenya Film Commission",
        "collection_description": "Kenya Film Commission documents..."
    },
    "kfcb": {
        "collection_name": "Kenya Film Classification Board", 
        "collection_description": "KFCB regulations and procedures..."
    },
    "brs": {
        "collection_name": "Business Registration Service",
        "collection_description": "Business registration documents..."
    },
    "odpc": {
        "collection_name": "Office of the Data Protection Commissioner",
        "collection_description": "Data protection laws and guidelines..."
    }
}
```

## Performance Considerations

### Caching
- Vector embeddings are cached in ChromaDB
- Model responses can be cached for repeated queries
- Collection metadata is cached to reduce database queries

### Optimization
- Batch embedding processing for multiple documents
- Parallel tool execution where possible
- Smart retrieval limiting to prevent token overflow

### Monitoring
- Token usage tracking for cost management
- Response time monitoring
- Error rate tracking
- Tool usage analytics

## Troubleshooting

### Common Issues

1. **Missing Collections**: Ensure ChromaDB collections are properly indexed
2. **API Key Issues**: Verify OpenAI/Groq API keys are valid
3. **Performance**: Check ChromaDB connection and indexing status
4. **Memory**: Monitor token usage to prevent context overflow

### Debug Mode

```python
# Enable verbose logging
Settings.llm.verbose = True

# Check collection status
from app.core.rag.tool_loader import get_collection_stats
stats = await get_collection_stats()
print(f"Collections available: {stats}")
```

### Error Handling

```python
try:
    result = await run_llamaindex_agent(message="test")
except Exception as e:
    logger.error(f"Agent execution failed: {e}")
    # Handle error appropriately
```

## Migration Guide

### From Pydantic-AI

1. **Update imports**:
   ```python
   # Old
   from app.core.orchestrator import generate_agent
   
   # New
   from app.core.llamaindex_orchestrator import run_llamaindex_agent
   ```

2. **Update function calls**:
   ```python
   # Old
   agent = generate_agent()
   result = agent.run_sync(message)
   
   # New
   result = await run_llamaindex_agent(message)
   ```

3. **Response handling remains the same** due to compatibility layer

### Testing Migration

```python
# Test both implementations
from app.core.compatibility_orchestrator import generate_agent as compat_agent
from app.core.llamaindex_orchestrator import run_llamaindex_agent

# Compare responses
old_result = compat_agent().run_sync("test query")
new_result = await run_llamaindex_agent("test query")

assert old_result.answer == new_result.answer
```

## Future Enhancements

1. **Multi-modal Support**: Add image and audio processing capabilities
2. **Custom Tools**: Framework for domain-specific tool development
3. **Advanced RAG**: Implement graph-based and hybrid retrieval
4. **Model Fine-tuning**: Integration with custom-trained models
5. **Streaming Responses**: Real-time response streaming
6. **Tool Chaining**: Complex multi-step reasoning workflows
