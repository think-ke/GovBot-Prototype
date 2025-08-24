import chromadb
import os
from typing import Dict, List, Any, Callable, Optional
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

from llama_index.embeddings.openai import OpenAIEmbedding

load_dotenv()


collection_dict: Dict[str, Dict[str, str]] = {
    "kfc":{
        "collection_name": "Kenya Film Commission",
        "collection_description": "Kenya Film Commission is a government agency responsible for promoting and facilitating the growth of the film industry in Kenya. It provides support to filmmakers, promotes Kenya as a filming destination, and works to develop local talent and infrastructure.",
    },
    "kfcb":{
        "collection_name": "Kenya Film Classification Board",
        "collection_description": "The Kenya Film Classification Board (KFCB) is a government agency responsible for regulating the film and broadcast industry in Kenya. It ensures that films and broadcasts comply with the law, promotes local content, and protects children from harmful content.",
    },
    "brs":{
        "collection_name": "Business Registration Service",
        "collection_description": "The Business Registration Service (BRS) is a government agency responsible for registering and regulating businesses in Kenya. It provides services such as business name registration, company registration, and issuance of certificates.",
    },
    "odpc":{
        "collection_name": "Office of the Data Protection Commissioner",
        "collection_description": "The Office of the Data Protection Commissioner (ODPC) is a government agency responsible for overseeing data protection and privacy in Kenya. It ensures compliance with data protection laws and promotes awareness of data rights.",
    }
}


logger.info("ChromaDB client will be initialized on first use")

# ChromaDB client will be initialized lazily
remote_db: Optional[chromadb.HttpClient] = None

def get_chroma_client() -> chromadb.HttpClient:
    """Get or create ChromaDB client connection."""
    global remote_db
    if remote_db is None:
        logger.info("Initializing ChromaDB client")
        remote_db = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=int(os.getenv("CHROMA_PORT", "8050")),
            settings=ChromaSettings(
                chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
                chroma_client_auth_credentials=f"{os.getenv('CHROMA_USERNAME')}:{os.getenv('CHROMA_PASSWORD')}")
        )
    return remote_db


embed_model = OpenAIEmbedding(
    model="text-embedding-3-small", embed_batch_size=100
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
    
    # Get the ChromaDB client
    client = get_chroma_client()

    for name, entry in collection_dict.items():
        collection = client.get_or_create_collection(
            name=name
        )

        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store,
        )
        
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=embed_model,
        )
        index_dict[name] = index
        logger.info(f"Loaded index for {entry['collection_name']}")
    
    return index_dict

# Index dictionary will be loaded lazily
index_dict: Optional[Dict[str, VectorStoreIndex]] = None

def get_index_dict() -> Dict[str, VectorStoreIndex]:
    """Get or create the index dictionary."""
    global index_dict
    if index_dict is None:
        index_dict = load_indexes()
    return index_dict

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

    indexes = get_index_dict()
    index = indexes["kfc"]
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

    indexes = get_index_dict()
    index = indexes["kfcb"]
    retriever = index.as_retriever()  

    return await retriever.aretrieve(query)


async def query_brs(query: str) -> List[NodeWithScore]:
    """
    Query the Business Registration Service collection.
    """
    logger.info("Querying Business Registration Service collection")

    indexes = get_index_dict()
    index = indexes["brs"]
    retriever = index.as_retriever()  

    return await retriever.aretrieve(query)

async def query_odpc(query: str) -> List[NodeWithScore]:
    """
    Query the Office of the Data Protection Commissioner collection.
    """
    logger.info("Querying Office of the Data Protection Commissioner collection")

    indexes = get_index_dict()
    index = indexes["odpc"]
    retriever = index.as_retriever()  

    return await retriever.aretrieve(query)




tools: List[Callable] = [
    query_kfc,
    query_kfcb,
    query_brs,
    query_odpc
]