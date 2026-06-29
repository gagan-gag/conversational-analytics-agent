"""
models/schemas.py — Shared Pydantic models for request/response contracts.
"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    """A single source citation returned with RAG answers."""
    doc_name: str
    page: Optional[int] = None
    chunk_id: str
    snippet: str = Field(default="", description="Short excerpt from the chunk")


class ChatMessage(BaseModel):
    """Single turn in the conversation."""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    mode: Optional[str] = Field(
        default=None,
        description="RAG | SQL | Hybrid — set by the system on assistant turns",
    )
    sources: List[SourceRef] = []


class ChatRequest(BaseModel):
    """Body for POST /chat."""
    message: str
    session_id: str = "default"
    history: List[ChatMessage] = []


class QueryResult(BaseModel):
    """Unified response from any query path."""
    answer: str
    mode: str = Field(..., description="RAG | SQL | Hybrid")
    sources: List[SourceRef] = []
    sql_query: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    raw_rows: Optional[List[dict]] = Field(
        default=None,
        description="Optional tabular data for SQL answers",
    )


class IngestResult(BaseModel):
    """Response from POST /rag/ingest."""
    chunks_stored: int
    doc_name: str
    status: str


class EvalRequest(BaseModel):
    """Body for POST /eval/run."""
    mode: str = Field(default="all", description="rag | sql | all")
