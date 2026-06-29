"""
rag/retriever.py — Semantic retrieval from ChromaDB.

Returns top-k chunks with full metadata for citation rendering.
"""
from __future__ import annotations

import logging
from typing import List

from langchain_core.documents import Document

from config import get_settings
from rag.vector_store import get_collection

logger = logging.getLogger(__name__)
settings = get_settings()


def _has_valid_openai_key() -> bool:
    """Return True only if the key looks like a real API key, not a placeholder."""
    key = settings.openai_api_key
    return (
        bool(key)
        and not key.startswith("your_")
        and not key.startswith("sk-your")
        and key != "sk-"
        and len(key) > 20
    )


def _get_embedding_function():
    """Mirror the embedding function used in ingestor (must match!)."""
    if _has_valid_openai_key():
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                model=settings.embedding_model,
                openai_api_key=settings.openai_api_key,
            )
        except Exception:
            pass

    # Try new langchain_huggingface package first, fall back to community
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def retrieve(query: str, k: int | None = None) -> List[Document]:
    """
    Query ChromaDB for top-k semantically similar chunks.

    Args:
        query: User's natural language question.
        k:     Number of chunks to return (defaults to settings.retriever_k).

    Returns:
        List of LangChain Documents with metadata: doc_name, page, chunk_id, snippet.
    """
    top_k = k or settings.retriever_k
    embedding_fn = _get_embedding_function()
    collection = get_collection()

    query_embedding = embedding_fn.embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count() or top_k),
        include=["documents", "metadatas", "distances"],
    )

    docs: List[Document] = []
    if not results["documents"] or not results["documents"][0]:
        logger.warning("No documents found in ChromaDB for query: %s", query[:60])
        return docs

    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        meta["snippet"] = text[:200]          # short excerpt for citation
        meta["similarity_score"] = round(1 - dist, 4)   # cosine → similarity
        docs.append(Document(page_content=text, metadata=meta))

    logger.debug("Retrieved %d chunks for query (top score: %.4f)", len(docs), docs[0].metadata["similarity_score"] if docs else 0)
    return docs
