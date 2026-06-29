"""
main.py — FastAPI application entry point.

Mounts all routers, enables CORS, seeds the SQLite DB at startup,
and initialises ChromaDB.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from models.schemas import (
    ChatRequest,
    EvalRequest,
    IngestResult,
    QueryResult,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()


# ─── Startup / Shutdown ───────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed DB and warm up ChromaDB on startup."""
    logger.info("🚀 Starting Conversational Analytics Agent SAGA...")

    # 1. Ensure data directory exists
    Path(settings.chroma_db_path).mkdir(parents=True, exist_ok=True)
    Path(settings.sqlite_db_path).parent.mkdir(parents=True, exist_ok=True)

    # 2. Seed SQLite if not present
    if not Path(settings.sqlite_db_path).exists():
        logger.info("Seeding SQLite analytics database...")
        from data.seed_db import seed
        seed(Path(settings.sqlite_db_path))
    else:
        logger.info("SQLite DB found at: %s", settings.sqlite_db_path)

    # 3. Warm up ChromaDB client
    from rag.vector_store import get_collection
    col = get_collection()
    logger.info("ChromaDB ready — %d documents in collection", col.count())

    yield

    logger.info("👋 Shutting down...")


# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Conversational Analytics Agent",
    description="Query documents and SQL databases in natural language",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # CRA / alternate
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health():
    from rag.vector_store import get_collection
    col = get_collection()
    return {
        "status": "ok",
        "model": settings.model_name,
        "chroma_docs": col.count(),
        "db": settings.sqlite_db_path,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# RAG ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/rag/ingest", response_model=IngestResult, tags=["RAG"])
async def rag_ingest(file: UploadFile = File(...)):
    """
    Upload a document (PDF, CSV, or TXT/MD) for ingestion into ChromaDB.
    Returns chunk count and status.
    """
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    content = await file.read()

    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed: {settings.max_upload_size_mb} MB",
        )

    from rag.ingestor import ingest_document
    result = ingest_document(content, file.filename or "upload")
    return IngestResult(**result)


@app.post("/rag/query", response_model=QueryResult, tags=["RAG"])
async def rag_query(request: ChatRequest):
    """Query uploaded documents using RAG (bypasses router)."""
    from rag.chain import query_rag
    return query_rag(request.message, request.session_id)


# ═══════════════════════════════════════════════════════════════════════════════
# SQL ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/sql/query", response_model=QueryResult, tags=["SQL"])
async def sql_query(request: ChatRequest):
    """Query the analytics SQLite database in natural language (bypasses router)."""
    from sql_agent.agent import query_sql
    return query_sql(request.message, request.session_id)


# ═══════════════════════════════════════════════════════════════════════════════
# CHAT ROUTE (ROUTER)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/chat", response_model=QueryResult, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Main conversational endpoint.
    Automatically classifies and routes the question to RAG, SQL, or Hybrid.
    Maintains per-session conversation memory (last 5 turns).
    """
    from router.query_router import route_query
    return route_query(request.message, request.session_id)


@app.delete("/chat/{session_id}", tags=["Chat"])
async def clear_session(session_id: str):
    """Clear conversation memory for a session."""
    from rag.chain import clear_session as rag_clear
    rag_clear(session_id)
    return {"cleared": session_id}


# ═══════════════════════════════════════════════════════════════════════════════
# EVAL ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/eval/run", tags=["Eval"])
async def run_eval(request: EvalRequest):
    """
    Run evaluation suite (rag | sql | all).
    Results written to eval_results.json.
    Warning: This is slow — runs LLM calls for every test case.
    """
    results = {}

    if request.mode in ("rag", "all"):
        from eval.rag_eval import run_rag_eval
        results["rag"] = run_rag_eval()

    if request.mode in ("sql", "all"):
        from eval.sql_eval import run_sql_eval
        results["sql"] = run_sql_eval()

    return results


@app.get("/eval/results", tags=["Eval"])
async def get_eval_results():
    """Return the latest eval_results.json."""
    results_path = Path("eval_results.json")
    if not results_path.exists():
        raise HTTPException(404, "No eval results found. Run POST /eval/run first.")
    import json
    return json.loads(results_path.read_text())


# ─── Schema route ─────────────────────────────────────────────────────────────
@app.get("/sql/schema", tags=["SQL"])
async def get_schema():
    """Return the human-readable database schema."""
    from sql_agent.schema_loader import get_schema_string
    return {"schema": get_schema_string()}
