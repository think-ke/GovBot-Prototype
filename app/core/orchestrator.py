from app.utils.prompts import SYSTEM_PROMPT
from app.core.rag.tool_loader import tools
from llama_index.core import Settings
from pydantic_ai import Agent
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from pydantic import BaseModel
from typing import List, Optional, Any
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_core import to_jsonable_python
from app.core.rag.tool_loader import collection_dict

Settings.llm = OpenAI(
    model="gpt-4o",
)

Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small", embed_batch_size=100
)


class Output(BaseModel):
    answer: str
    sources: list
    confidence: float
    retriever_type: str
    recommended_follow_up_questions: Optional[List[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The Kenya Film Commission (KFC) plays a crucial role in developing and promoting the film industry in Kenya. It provides various services including...",
                "sources": [
                    {"title": "Kenya Film Commission Overview", "url": "https://kenyafilm.go.ke/about-us"},
                    {"title": "Film Industry Guidelines", "url": "https://kenyafilm.go.ke/guidelines"}
                ],
                "confidence": 0.95,
                "retriever_type": "kfc",  # Changed from "hybrid" to a valid collection ID
                "recommended_follow_up_questions": [
                    "What financial incentives does the Kenya Film Commission offer?",
                    "How can I register a film production company in Kenya?",
                    "What are the film shooting requirements in Kenya?"
                ]
            }
        }


def generate_agent() -> Agent:
    """
    Generate an agent for the OpenAI model with the specified system prompt and retrievers.
    
    Returns:
        Initialized agent
    """
    # Initialize the agent with the system prompt and retrievers
    agent = Agent(
        model = 'openai:gpt-4o',
        instructions=SYSTEM_PROMPT.format(collections=str(collection_dict)),  
        tools=tools,
        verbose=True,
        output_type=Output
    )
    
    return agent


if __name__ == "__main__":
    # Example usage
    agent = generate_agent()

    # Example 1: Starting a new conversation
    result1 = agent.run_sync(
        "What is the role of the Kenya Film Commission in the film industry?"
    )
    print("First response:", result1.output.answer)
    
    # Save message history after the first exchange
    history_step_1 = result1.all_messages()
    
    # Convert the history to serializable Python objects
    history_as_python_objects = to_jsonable_python(history_step_1)
    
    # In a real app, you would store history_as_python_objects in the database
    # Then when continuing the conversation, you would:
    
    # 1. Load the serialized history from the database
    # 2. Convert it back to ModelMessage objects using ModelMessagesTypeAdapter
    same_history_as_step_1 = ModelMessagesTypeAdapter.validate_python(history_as_python_objects)
    
    # 3. Use the history when running the agent for the follow-up message
    result2 = agent.run_sync(
        "Tell me more about its support for filmmakers.",
        message_history=same_history_as_step_1
    )
    
    print("\nFollow-up response (with history):", result2.output.answer)
    
    # Compare with a response without history context
    result3 = agent.run_sync(
        "Tell me more about its support for filmmakers."
    )
    
    print("\nSame question without history:", result3.output.answer)
    
    # The output with history should be more contextually appropriate





