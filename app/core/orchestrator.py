from app.utils.prompts import SYSTEM_PROMPT
from app.core.rag.tool_loader import tools
from llama_index.core import Settings
from pydantic_ai import Agent
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Union
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_core import to_jsonable_python
from app.core.rag.tool_loader import collection_dict
import yaml
import os


#Settings.llm = OpenAI(
#    model="gpt-4o",
#)
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
    accepted_prediction_tokens: int = Field(default=0, description="Number of accepted prediction tokens")
    audio_tokens: int = Field(default=0, description="Number of audio tokens")
    reasoning_tokens: int = Field(default=0, description="Number of reasoning tokens")
    rejected_prediction_tokens: int = Field(default=0, description="Number of rejected prediction tokens")
    cached_tokens: int = Field(default=0, description="Number of cached tokens")


class Usage(BaseModel):
    """Usage information from the model response."""
    requests: int = Field(description="Number of requests made")
    request_tokens: int = Field(description="Number of tokens in the request")
    response_tokens: int = Field(description="Number of tokens in the response")
    total_tokens: int = Field(description="Total number of tokens used")
    details: UsageDetails = Field(description="Additional usage details")


class FollowUpQuestion(BaseModel):
    """Represents a recommended follow-up question."""
    question: str = Field(
        description="The recommended follow-up question for the user",
        min_length=1
    )
    
    relevance_score: Optional[float] = Field(
        default=None,
        description="Relevance score indicating how closely the question relates to the user's original query",
        ge=0.0,
        le=1.0
    )

class Output(BaseModel):
    """
    Structured output format for agent responses with source attribution and metadata.
    """
    answer: str = Field(
        description="The comprehensive answer to the user's question",
        min_length=1
    )
    
    sources: List[Source] = Field(
        description="List of sources that provided information for the answer",
        default_factory=list
    )
    
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0 indicating reliability of the answer",
        ge=0.0,
        le=1.0
    )
    
    retriever_type: str = Field(
        description="Identifier for the knowledge collection that was used for retrieval"
    )
    
    usage: Optional[Usage] = Field(
        default=None,
        description="Token usage information from the model response"
    )

    recommended_follow_up_questions: List[FollowUpQuestion] = Field(
        default_factory=list,
        description="List of recommended follow-up questions based on the user's query"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The Kenya Film Commission (KFC) plays a crucial role in developing and promoting the film industry in Kenya. It provides various services including...",
                "sources": [
                    {
                        "title": "Kenya Film Commission Overview", 
                        "url": "https://kenyafilm.go.ke/about-us",
                        "snippet": "The Kenya Film Commission (KFC) is mandated to develop, promote and market the film industry locally and internationally."
                    },
                    {
                        "title": "Film Industry Guidelines", 
                        "url": "https://kenyafilm.go.ke/guidelines",
                        "snippet": "KFC provides financial support, technical assistance, and marketing opportunities to filmmakers in Kenya."
                    }
                ],
                "confidence": 0.95,
                "retriever_type": "kfc",
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


def generate_agent() -> Agent[None, Output]:
    """
    Generate an agent for the OpenAI model with the specified system prompt and retrievers.
    
    Returns:
        Initialized agent
    """

    collection_yml = yaml.dump(collection_dict, default_flow_style=False)
    # Initialize the agent with the system prompt and retrievers
    agent = Agent(
        model='openai:gpt-4o',
        system_prompt=SYSTEM_PROMPT.format(collections=collection_yml),
        tools=tools,
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

    
    result1.usage().__dict__

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



    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIModel
    import os
    from dotenv import load_dotenv
    load_dotenv()



    base_url = os.getenv("RUNPOD_BASE_URL")
    api_key = os.getenv("RUNPOD_API_KEY")
    # Example model name, replace with your

    MODEL_NAME = "microsoft/Phi-4-mini-instruct"

    model = OpenAIModel(
        model_name=MODEL_NAME,
        base_url=base_url,
        api_key=api_key
    )

    agent = Agent(  
        model=model,
        system_prompt='Be concise, reply with one sentence.',  
    )

    result = agent.run_sync('Where does "hello world" come from?')  
    print(result.data)





