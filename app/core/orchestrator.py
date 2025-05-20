from app.utils.prompts import SYSTEM_PROMPT
from app.core.rag.tool_loader import retrievers
from llama_index.core import Settings
from pydantic_ai import Agent
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from pydantic import BaseModel
from typing import List, Optional, Any
from pydantic_ai.messages import ModelMessage

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


def generate_agent() -> Agent:
    """
    Generate an agent for the OpenAI model with the specified system prompt and retrievers.
    
    Returns:
        Initialized agent
    """
    # Initialize the agent with the system prompt and retrievers
    agent = Agent(
        'openai:gpt-4o',
        instructions=SYSTEM_PROMPT,  
        tools=retrievers,
        verbose=True,
        output_type=Output
    )
    
    return agent


if __name__ == "__main__":
    # Example usage
    agent = generate_agent()

    # Run the agent with a sample query using a synchronous method
    result = agent.run_sync(
        "What is the role of the Kenya Film Commission in the film industry?"
    )
    print(result.output)

    # Run the agent with a sample query using an asynchronous method
    # result = await agent.run(
    #     "What is the role of the Kenya Film Commission in the film industry?",
    #     chat_history=[],
    # )

    # The output will be an instance of the Output model





