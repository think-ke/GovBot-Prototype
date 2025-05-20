import chromadb
import os
from app.utils.prompts import QUERY_ENGINE_PROMPT
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from chromadb.config import Settings

## add logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
# Load environment variables from .env file

load_dotenv()


collection_dict = {
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
remote_db = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST", "localhost"),
    port=int(os.getenv("CHROMA_PORT", "8050")),
  settings=Settings(
      chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
      chroma_client_auth_credentials=f"{os.getenv('CHROMA_USERNAME')}:{os.getenv('CHROMA_PASSWORD')}")
)

retrievers = []
for collection_name, entry  in collection_dict.items():
    collection = remote_db.get_or_create_collection(
        name=collection_name
    )
    prompt = QUERY_ENGINE_PROMPT.format(
        collection_name=entry["collection_name"],
        collection_description=entry["collection_description"]
    )

    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store,
    )
    
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
    )
    retriever = index.as_retriever()

    retrievers.append(retriever.aretrieve) 
