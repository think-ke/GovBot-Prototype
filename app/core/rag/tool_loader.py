import chromadb
import os
from typing import Dict, List, Any, Callable, Optional
from app.utils.prompts import QUERY_ENGINE_PROMPT
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.schema import NodeWithScore
from chromadb.config import Settings as ChromaSettings

# logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from opentelemetry.instrumentation.llamaindex import LlamaIndexInstrumentor
from llama_index.embeddings.openai import OpenAIEmbedding

load_dotenv()
LlamaIndexInstrumentor().instrument()


# Legacy fallback collections
LEGACY_COLLECTIONS: Dict[str, Dict[str, str]] = {
    "kfc": {"collection_name": "Kenya Film Commission", "collection_description": ""},
    "kfcb": {"collection_name": "Kenya Film Classification Board", "collection_description": ""},
    "brs": {"collection_name": "Business Registration Service", "collection_description": ""},
    "odpc": {"collection_name": "Office of the Data Protection Commissioner", "collection_description": ""},
}

# Cached metadata and alias map
collection_dict: Optional[Dict[str, Dict[str, str]]] = None
_alias_to_canonical: Dict[str, str] = {}

remote_db: Optional[Any] = None


def get_chroma_client() -> Any:
    global remote_db
    if remote_db is None:
        logger.info("Initializing ChromaDB client")
        user = os.getenv("CHROMA_USERNAME")
        pwd = os.getenv("CHROMA_PASSWORD")
        settings = None
        if user and pwd:
            settings = ChromaSettings(
                chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
                chroma_client_auth_credentials=f"{user}:{pwd}",
            )
        remote_db = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=int(os.getenv("CHROMA_PORT", "8050")),
            settings=settings,
        )
    return remote_db


embed_model = OpenAIEmbedding(model="text-embedding-3-small", embed_batch_size=100)


def _get_sync_db_url() -> Optional[str]:
    url = os.getenv("DATABASE_URL")
    if not url:
        return None
    return url.replace("+asyncpg", "")


def _load_collections_from_db() -> Dict[str, Dict[str, str]]:
    url = _get_sync_db_url()
    if not url:
        _alias_to_canonical.clear()
        for k in LEGACY_COLLECTIONS.keys():
            _alias_to_canonical[k] = k
        return dict(LEGACY_COLLECTIONS)
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT id, name, description FROM collections")).fetchall()
        data: Dict[str, Dict[str, str]] = {}
        for cid, name, desc in rows:
            data[str(cid)] = {"collection_name": name, "collection_description": desc or ""}
        name_to_id = {v["collection_name"]: k for k, v in data.items()}
        aliases = {
            "kfc": "Kenya Film Commission",
            "kfcb": "Kenya Film Classification Board",
            "brs": "Business Registration Service",
            "odpc": "Office of the Data Protection Commissioner",
        }
        _alias_to_canonical.clear()
        for alias, display in aliases.items():
            can = name_to_id.get(display)
            if can:
                _alias_to_canonical[alias] = can
        if not data:
            for k in LEGACY_COLLECTIONS.keys():
                _alias_to_canonical[k] = k
            return dict(LEGACY_COLLECTIONS)
        return data
    except Exception as e:
        logger.error(f"Failed to load collections from DB: {e}")
        _alias_to_canonical.clear()
        for k in LEGACY_COLLECTIONS.keys():
            _alias_to_canonical[k] = k
        return dict(LEGACY_COLLECTIONS)


def get_collection_metadata() -> Dict[str, Dict[str, str]]:
    global collection_dict
    if collection_dict is None:
        collection_dict = _load_collections_from_db()
        logger.info(f"Loaded {len(collection_dict)} collections for RAG tools")
    return collection_dict


def load_indexes() -> Dict[str, VectorStoreIndex]:
    logger.info("Loading indexes from ChromaDB")
    idx: Dict[str, VectorStoreIndex] = {}
    client: Any = get_chroma_client()

    meta = get_collection_metadata()
    # canonical indexes
    for canonical_id, entry in meta.items():
        chroma_coll = client.get_or_create_collection(name=str(canonical_id))
        vs = ChromaVectorStore(chroma_collection=chroma_coll)
        StorageContext.from_defaults(vector_store=vs)
        index = VectorStoreIndex.from_vector_store(vector_store=vs, embed_model=embed_model)
        idx[str(canonical_id)] = index
        logger.info(f"Loaded index for {entry['collection_name']} ({canonical_id})")

    # alias pointers
    for alias, canonical in _alias_to_canonical.items():
        if str(canonical) in idx:
            idx[alias] = idx[str(canonical)]
    return idx


# lazy index cache
index_dict: Optional[Dict[str, VectorStoreIndex]] = None


def get_index_dict() -> Dict[str, VectorStoreIndex]:
    global index_dict
    if index_dict is None:
        index_dict = load_indexes()
    return index_dict


def refresh_collections() -> Dict[str, VectorStoreIndex]:
    """Invalidate caches and reload collections + indexes.

    Returns the fresh index dictionary.
    """
    global collection_dict, index_dict
    logger.info("Refreshing collection metadata and indexes")
    collection_dict = None
    index_dict = None
    # Force reload
    _ = get_collection_metadata()
    return get_index_dict()


def get_alias_map() -> Dict[str, str]:
    """Expose alias->canonical mapping for consumers (read-only copy)."""
    # Ensure aliases are computed at least once
    _ = get_collection_metadata()
    return dict(_alias_to_canonical)


async def query_kfc(query: str) -> List[NodeWithScore]:
    indexes = get_index_dict()
    retriever = indexes["kfc"].as_retriever()
    return await retriever.aretrieve(query)


async def query_kfcb(query: str) -> List[NodeWithScore]:
    indexes = get_index_dict()
    retriever = indexes["kfcb"].as_retriever()
    return await retriever.aretrieve(query)


async def query_brs(query: str) -> List[NodeWithScore]:
    indexes = get_index_dict()
    retriever = indexes["brs"].as_retriever()
    return await retriever.aretrieve(query)


async def query_odpc(query: str) -> List[NodeWithScore]:
    indexes = get_index_dict()
    retriever = indexes["odpc"].as_retriever()
    return await retriever.aretrieve(query)


tools: List[Callable] = [query_kfc, query_kfcb, query_brs, query_odpc]

# Ensure collection_dict is populated for modules that read it directly
try:
    if collection_dict is None:
        collection_dict = _load_collections_from_db()
except Exception as _e:
    # Fallback to legacy if anything goes wrong
    collection_dict = dict(LEGACY_COLLECTIONS)