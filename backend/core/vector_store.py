"""ChromaDB vector store — persistent document embeddings and retrieval."""

import logging
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.config import settings
from backend.core.llm_client import get_embeddings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "documents"

# ---------------------------------------------------------------------------
# Singleton ChromaDB client with custom embedding function
# ---------------------------------------------------------------------------

class _SiliconFlowEmbeddingFn:
    """ChromaDB-compatible embedding function backed by SiliconFlow API."""

    def __call__(self, input: List[str]) -> List[List[float]]:
        return get_embeddings(input)


_client: Optional[chromadb.ClientAPI] = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        persist_dir = str(Path(settings.CHROMA_DIR).resolve())
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def _get_collection() -> chromadb.Collection:
    client = _get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_SiliconFlowEmbeddingFn(),
        metadata={"hnsw:space": "cosine"},
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def add_documents(chunks: List, doc_name: str) -> int:
    """Add Langchain Document chunks to the vector store.

    Existing chunks for the same source document are removed first.

    Returns:
        Number of chunks added.
    """
    if not chunks:
        return 0

    collection = _get_collection()

    # Deduplicate — remove old chunks for this source
    _remove_by_source(collection, doc_name)

    ids = [f"{_hash_name(doc_name)}_{c.metadata['chunk_index']}" for c in chunks]
    texts = [c.page_content for c in chunks]
    metadatas = [c.metadata for c in chunks]

    collection.add(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
    )
    logger.info("Added %d chunks for '%s'", len(chunks), doc_name)
    return len(chunks)


def similarity_search(
    query: str,
    k: int | None = None,
) -> List:
    """Retrieve top-k most similar document chunks for a query string.

    Returns:
        List of dicts: {"document": str, "metadata": dict, "distance": float}
    """
    if k is None:
        k = settings.TOP_K_RETRIEVAL

    collection = _get_collection()
    try:
        results = collection.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        logger.error("Query failed: %s", exc)
        return []

    if not results["ids"] or not results["ids"][0]:
        return []

    out: list = []
    for i in range(len(results["ids"][0])):
        out.append({
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return out


def list_documents() -> List[dict]:
    """Return a summary of indexed documents."""
    collection = _get_collection()
    try:
        data = collection.get(include=["metadatas"])
    except Exception:
        return []

    if not data["metadatas"]:
        return []

    # Group by source
    grouped: dict = {}
    for meta in data["metadatas"]:
        src = meta["source"]
        if src not in grouped:
            grouped[src] = {
                "name": src,
                "doc_id": meta["doc_id"],
                "chunk_count": 0,
                "last_indexed": "",
            }
        grouped[src]["chunk_count"] += 1

    return list(grouped.values())


def delete_document(doc_name: str) -> bool:
    """Delete all chunks for a given document name."""
    collection = _get_collection()
    return _remove_by_source(collection, doc_name)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _remove_by_source(collection: chromadb.Collection, doc_name: str) -> bool:
    try:
        existing = collection.get(
            where={"source": doc_name},
            include=["metadatas"],
        )
    except Exception:
        return False

    if existing["ids"]:
        collection.delete(ids=existing["ids"])
        logger.info("Removed %d old chunks for '%s'", len(existing["ids"]), doc_name)
    return True


def _hash_name(name: str) -> str:
    import hashlib
    return hashlib.md5(name.encode()).hexdigest()[:8]
