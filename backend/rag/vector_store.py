"""
rag/vector_store.py — Singleton ChromaDB client + collection accessor.
Separated so both ingestor.py and retriever.py share the same client instance.
"""
from __future__ import annotations

import logging
import chromadb

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_client: chromadb.ClientAPI | None = None
COLLECTION_NAME = "rag_documents"


def get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
        )
        logger.info("ChromaDB client initialised at: %s", settings.chroma_db_path)
    return _client


def get_collection() -> chromadb.Collection:
    """Get-or-create the main document collection."""
    client = get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
