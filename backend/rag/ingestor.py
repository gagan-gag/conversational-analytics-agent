"""
rag/ingestor.py — Document ingestion pipeline.

Supports: PDF (PyMuPDF), CSV (pandas), plain-text (.txt / .md)
Pipeline:
  1. Extract raw text per page/row
  2. Chunk with RecursiveCharacterTextSplitter using tiktoken token counts
  3. Embed via OpenAI text-embedding-3-small (falls back to sentence-transformers)
  4. Upsert into ChromaDB with rich metadata
"""
from __future__ import annotations

import hashlib
import io
import logging
from pathlib import Path
from typing import List

import fitz  # PyMuPDF
import pandas as pd
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from config import get_settings
from rag.vector_store import get_collection

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── Tokenizer ────────────────────────────────────────────────────────────────
_ENCODING = tiktoken.get_encoding("cl100k_base")


def _token_len(text: str) -> int:
    return len(_ENCODING.encode(text))


_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    length_function=_token_len,
    separators=["\n\n", "\n", " ", ""],
)


# ─── Text Extractors ──────────────────────────────────────────────────────────

def _extract_pdf(file_bytes: bytes) -> List[dict]:
    """Return list of {text, page} dicts, one per PDF page."""
    pages = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append({"text": text, "page": page_num})
    return pages


def _extract_csv(file_bytes: bytes, filename: str) -> List[dict]:
    """Convert CSV rows to a readable string representation."""
    df = pd.read_csv(io.BytesIO(file_bytes))
    # Convert to markdown-like string for chunking
    text = df.to_string(index=False)
    return [{"text": text, "page": None}]


def _extract_txt(file_bytes: bytes) -> List[dict]:
    text = file_bytes.decode("utf-8", errors="replace").strip()
    return [{"text": text, "page": None}]


# ─── Embedder ─────────────────────────────────────────────────────────────────

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
    """Return embedding function; OpenAI preferred, sentence-transformers as fallback."""
    if _has_valid_openai_key():
        try:
            from langchain_openai import OpenAIEmbeddings
            logger.info("Using OpenAI embeddings: %s", settings.embedding_model)
            return OpenAIEmbeddings(
                model=settings.embedding_model,
                openai_api_key=settings.openai_api_key,
            )
        except Exception as e:
            logger.warning("OpenAI embeddings failed (%s), falling back to sentence-transformers", e)

    # Try new langchain_huggingface package first, fall back to community
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    logger.info("Using sentence-transformers: all-MiniLM-L6-v2")
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


# ─── Main Ingestion Function ──────────────────────────────────────────────────

def ingest_document(file_bytes: bytes, filename: str) -> dict:
    """
    Full ingestion pipeline.

    Args:
        file_bytes: Raw file content.
        filename:   Original filename (used to detect type and as doc_name).

    Returns:
        dict with keys: chunks_stored, doc_name, status
    """
    suffix = Path(filename).suffix.lower()
    doc_name = Path(filename).name

    # 1. Extract text
    if suffix == ".pdf":
        pages = _extract_pdf(file_bytes)
    elif suffix == ".csv":
        pages = _extract_csv(file_bytes, filename)
    elif suffix in (".txt", ".md"):
        pages = _extract_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Supported: PDF, CSV, TXT, MD")

    # 2. Split into chunks
    all_docs: List[Document] = []
    for item in pages:
        chunks = _SPLITTER.split_text(item["text"])
        for idx, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(
                f"{doc_name}:{item['page']}:{idx}:{chunk[:40]}".encode()
            ).hexdigest()
            all_docs.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": filename,
                        "doc_name": doc_name,
                        "page": item["page"],
                        "chunk_id": chunk_id,
                        "chunk_index": idx,
                    },
                )
            )

    if not all_docs:
        return {"chunks_stored": 0, "doc_name": doc_name, "status": "no_content"}

    # 3. Embed & store in ChromaDB
    embedding_fn = _get_embedding_function()
    collection = get_collection()

    texts = [d.page_content for d in all_docs]
    metadatas = [d.metadata for d in all_docs]
    ids = [d.metadata["chunk_id"] for d in all_docs]
    embeddings = embedding_fn.embed_documents(texts)

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    logger.info("Ingested %d chunks from '%s'", len(all_docs), doc_name)
    return {
        "chunks_stored": len(all_docs),
        "doc_name": doc_name,
        "status": "success",
    }
