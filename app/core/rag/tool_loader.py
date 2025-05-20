import chromadb
import os
from typing import Dict, List, Any, Callable
from app.utils.prompts import QUERY_ENGINE_PROMPT
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.schema import NodeWithScore
from chromadb.config import Settings as ChromaSettings

## add logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
# Load environment variables from .env file

from opentelemetry.instrumentation.llamaindex import LlamaIndexInstrumentor
LlamaIndexInstrumentor().instrument()

load_dotenv()


collection_dict: Dict[str, Dict[str, str]] = {
    "kfc":{
        "collection_name": "Kenya Film Commission",
        "collection_description": "Kenya Film Commission is a government agency responsible for promoting and facilitating the growth of the film industry in Kenya. It provides support to filmmakers, promotes Kenya as a filming destination, and works to develop local talent and infrastructure.",
    },
    "kfcb":{
        "collection_name": "Kenya Film Classification Board",
        "collection_description": "The Kenya Film Classification Board (KFCB) is a government agency responsible for regulating the film and broadcast industry in Kenya. It ensures that films and broadcasts comply with the law, promotes local content, and protects children from harmful content.",
    }
}


logger.info("Loading ChromaDB client")
# Initialize the ChromaDB client
remote_db: chromadb.HttpClient = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST", "localhost"),
    port=int(os.getenv("CHROMA_PORT", "8050")),
    settings=ChromaSettings(
        chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
        chroma_client_auth_credentials=f"{os.getenv('CHROMA_USERNAME')}:{os.getenv('CHROMA_PASSWORD')}")
)


def load_indexes() -> Dict[str, VectorStoreIndex]:
    """
    Load indexes from ChromaDB and create retrievers for each collection.
    
    This function creates vector store indexes for each collection defined in the
    collection_dict. It first retrieves or creates the collection from ChromaDB,
    then sets up a vector store and an index for each collection.
    
    Returns:
        Dict[str, VectorStoreIndex]: Dictionary of collection names mapped to their 
                                     corresponding vector store indexes
    """
    logger.info("Loading indexes from ChromaDB")

    index_dict: Dict[str, VectorStoreIndex] = {}

    for name, entry in collection_dict.items():
        collection = remote_db.get_or_create_collection(
            name=name
        )

        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store,
        )
        
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
        )
        index_dict[name] = index
        logger.info(f"Loaded index for {entry['collection_name']}")
    
    return index_dict

index_dict: Dict[str, VectorStoreIndex] = load_indexes()

async def query_kfc(query: str) -> List[NodeWithScore]:
    """
    Query the Kenya Film Commission collection.
    
    This function takes a query string, uses the KFC retriever to find relevant
    documents from the Kenya Film Commission collection, and returns the results.
    
    Args:
        query (str): The query string to search for in the KFC collection
    
    Returns:
        List[NodeWithScore]: A list of retrieved nodes with their relevance scores
    """
    logger.info("Querying Kenya Film Commission collection")

    index = index_dict["kfc"]
    retriever = index.as_retriever()  

    return await retriever.aretrieve(query)


async def query_kfcb(query: str) -> List[NodeWithScore]:
    """
    Query the Kenya Film Classification Board collection.
    
    This function takes a query string, uses the KFCB retriever to find relevant
    documents from the Kenya Film Classification Board collection, and returns the results.
    
    Args:
        query (str): The query string to search for in the KFCB collection
    
    Returns:
        List[NodeWithScore]: A list of retrieved nodes with their relevance scores
    """
    logger.info("Querying Kenya Film Classification Board collection")

    index = index_dict["kfcb"]
    retriever = index.as_retriever()  

    return await retriever.aretrieve(query)


tools: List[Callable] = [
    query_kfc,
    query_kfcb
]