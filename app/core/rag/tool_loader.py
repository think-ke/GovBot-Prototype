import chromadb
import os
from datetime import datetime, timezone
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


CollectionIndexHandle = Dict[str, Any]

# Lazy per-collection cache keyed by canonical collection id
collection_index_handles: Dict[str, CollectionIndexHandle] = {}


def load_indexes() -> Dict[str, VectorStoreIndex]:
    """Compatibility shim for legacy importers that expect eager loading."""
    return refresh_collection_indexes()


def get_index_dict() -> Dict[str, VectorStoreIndex]:
    if not collection_index_handles:
        load_indexes()

    index_map: Dict[str, VectorStoreIndex] = {
        canonical_id: handle["index"]
        for canonical_id, handle in collection_index_handles.items()
    }

    alias_map = get_alias_map()
    for alias, canonical in alias_map.items():
        if canonical in collection_index_handles:
            index_map[alias] = collection_index_handles[canonical]["index"]

    return index_map


def refresh_collections(collection_id: Optional[str] = None) -> Dict[str, VectorStoreIndex]:
    """Refresh vector indexes.

    Args:
        collection_id: Optional canonical or alias identifier. When provided, only the
            targeted collection is rebuilt; otherwise every collection is refreshed.
    """

    return refresh_collection_indexes(collection_id)


def refresh_collection_indexes(collection_id: Optional[str] = None) -> Dict[str, VectorStoreIndex]:
    logger.info("Refreshing %sindex cache", "targeted " if collection_id else "global ")

    if collection_id:
        canonical_id = _resolve_collection_identifier(collection_id)
        if canonical_id is None:
            logger.warning("Requested refresh for unknown collection '%s'", collection_id)
            return get_index_dict()

        metadata = get_collection_metadata()
        if canonical_id not in metadata:
            logger.info("Metadata missing for '%s'; reloading collections", canonical_id)
            _reload_collection_metadata()
            metadata = get_collection_metadata()

        if canonical_id not in metadata:
            logger.error("Unable to refresh index for unknown collection '%s'", canonical_id)
            return get_index_dict()

        collection_index_handles[canonical_id] = _build_collection_index_handle(canonical_id)
        return get_index_dict()

    _reload_collection_metadata()
    collection_index_handles.clear()
    metadata = get_collection_metadata()
    for canonical_id in metadata.keys():
        collection_index_handles[canonical_id] = _build_collection_index_handle(canonical_id)

    return get_index_dict()


def _build_collection_index_handle(canonical_id: str) -> CollectionIndexHandle:
    client: Any = get_chroma_client()
    chroma_coll = client.get_or_create_collection(name=str(canonical_id))
    vs = ChromaVectorStore(chroma_collection=chroma_coll)
    StorageContext.from_defaults(vector_store=vs)
    index = VectorStoreIndex.from_vector_store(vector_store=vs, embed_model=embed_model)

    metadata = get_collection_metadata().get(str(canonical_id), {})
    handle: CollectionIndexHandle = {
        "index": index,
        "collection_id": str(canonical_id),
        "collection_name": metadata.get("collection_name"),
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
    }
    logger.info(
        "Loaded index for %s (%s)",
        metadata.get("collection_name", canonical_id),
        canonical_id,
    )
    return handle


def _reload_collection_metadata() -> None:
    global collection_dict
    collection_dict = None
    _ = get_collection_metadata()


def _resolve_collection_identifier(identifier: str) -> Optional[str]:
    if not identifier:
        return None

    metadata = get_collection_metadata()
    if identifier in metadata:
        return identifier

    alias_map = get_alias_map()
    canonical = alias_map.get(identifier)
    if canonical:
        return canonical

    return identifier if identifier in metadata else None


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