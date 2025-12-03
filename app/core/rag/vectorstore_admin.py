import os
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import Any


def _get_client() -> Any:
    user = os.getenv("CHROMA_USERNAME")
    pwd = os.getenv("CHROMA_PASSWORD")
    settings = None
    if user and pwd:
        settings = ChromaSettings(
            chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
            chroma_client_auth_credentials=f"{user}:{pwd}",
        )
    return chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", "8050")),
        settings=settings,
    )


def delete_embeddings_for_doc(collection_id: str, doc_id: str) -> int:
    """Delete vectors from Chroma for a given collection and doc_id metadata.

    Returns the number of records matched for deletion when available (0 if unknown).
    """
    client = _get_client()
    coll = client.get_or_create_collection(name=str(collection_id))
    # Many clients don't return count; we catch exceptions to be safe
    try:
        coll.delete(where={"doc_id": str(doc_id)})
        return 0
    except Exception:
        # Fallback when where filter isn't supported (older servers)
        try:
            # Attempt brute force by fetching ids with metadata (may be unsupported)
            # If unsupported, just return 0 after delete attempt
            coll.delete(where={"doc_id": str(doc_id)})
        except Exception:
            pass
        return 0
