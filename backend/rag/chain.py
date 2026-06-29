"""
rag/chain.py — LangChain retrieval chain with conversation memory.

Flow:
  user question
    → retrieve top-5 chunks
    → stuff into LLM context with system prompt
    → generate grounded answer citing sources by name/page
    → return QueryResult with SourceRef list
"""
from __future__ import annotations

import logging
from typing import List

from langchain_core.messages import HumanMessage, AIMessage


class _SimpleWindowMemory:
    """Minimal drop-in for ConversationBufferWindowMemory (removed in recent LangChain)."""

    def __init__(self, k: int = 5):
        self._k = k
        self._messages: list = []

    def load_memory_variables(self, _: dict) -> dict:
        return {"chat_history": self._messages[-(self._k * 2):]}

    def save_context(self, inputs: dict, outputs: dict) -> None:
        human_text = inputs.get("input", inputs.get("question", ""))
        ai_text = outputs.get("output", outputs.get("answer", ""))
        self._messages.append(HumanMessage(content=human_text))
        self._messages.append(AIMessage(content=ai_text))

    def clear(self) -> None:
        self._messages.clear()

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_groq import ChatGroq

from config import get_settings
from models.schemas import QueryResult, SourceRef
from rag.retriever import retrieve

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── System Prompt ────────────────────────────────────────────────────────────
_SYSTEM_TEMPLATE = """You are a precise document analyst assistant.

STRICT RULES:
1. Answer ONLY using the provided context below. Do not use outside knowledge.
2. If the answer is not found in the context, respond exactly:
   "I don't have enough information in the uploaded documents to answer this."
3. Always cite your sources using this format: [doc_name, page X] or [doc_name] if no page.
4. Be concise but thorough. Use bullet points for multi-part answers.
5. Never fabricate facts, statistics, or quotes.

CONTEXT:
{context}
"""

_HUMAN_TEMPLATE = """Conversation so far:
{chat_history}

Question: {question}
Answer:"""


# ─── Session Memory Store ─────────────────────────────────────────────────────
_session_memories: dict[str, _SimpleWindowMemory] = {}


def _get_memory(session_id: str) -> _SimpleWindowMemory:
    if session_id not in _session_memories:
        _session_memories[session_id] = _SimpleWindowMemory(k=settings.memory_window_k)
    return _session_memories[session_id]


# ─── LLM ──────────────────────────────────────────────────────────────────────
def _get_llm() -> ChatGroq:
    return ChatGroq(
        model=settings.model_name,
        groq_api_key=settings.groq_api_key,
        temperature=0.1,
        max_tokens=1024,
    )


# ─── Core Query Function ──────────────────────────────────────────────────────
def query_rag(question: str, session_id: str = "default") -> QueryResult:
    """
    Run the full RAG pipeline for a user question.

    Args:
        question:   Natural language question.
        session_id: Used to maintain per-user conversation memory.

    Returns:
        QueryResult with answer, mode="RAG", and source citations.
    """
    # 1. Retrieve relevant chunks
    docs: List[Document] = retrieve(question)

    if not docs:
        return QueryResult(
            answer="No documents have been uploaded yet. Please use the file upload to add documents first.",
            mode="RAG",
            confidence=0.0,
        )

    # 2. Build context string
    context_parts = []
    for doc in docs:
        meta = doc.metadata
        page_info = f", page {meta['page']}" if meta.get("page") else ""
        context_parts.append(
            f"[Source: {meta.get('doc_name', 'unknown')}{page_info}]\n{doc.page_content}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # 3. Build prompt
    llm = _get_llm()
    memory = _get_memory(session_id)
    chat_history = memory.load_memory_variables({}).get("chat_history", [])

    # Format chat history as string
    history_str = ""
    if chat_history:
        history_str = "\n".join(
            f"{'Human' if m.type == 'human' else 'Assistant'}: {m.content}"
            for m in chat_history
        )

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(_SYSTEM_TEMPLATE),
        HumanMessagePromptTemplate.from_template(_HUMAN_TEMPLATE),
    ])

    messages = prompt.format_messages(
        context=context,
        chat_history=history_str,
        question=question,
    )

    # 4. Call LLM
    response = llm.invoke(messages)
    answer = response.content.strip()

    # 5. Save to memory
    memory.save_context({"input": question}, {"answer": answer})

    # 6. Build source refs
    sources = []
    seen_ids = set()
    for doc in docs:
        meta = doc.metadata
        chunk_id = meta.get("chunk_id", "")
        if chunk_id not in seen_ids:
            seen_ids.add(chunk_id)
            sources.append(
                SourceRef(
                    doc_name=meta.get("doc_name", "unknown"),
                    page=meta.get("page"),
                    chunk_id=chunk_id,
                    snippet=meta.get("snippet", doc.page_content[:150]),
                )
            )

    return QueryResult(
        answer=answer,
        mode="RAG",
        sources=sources,
        confidence=round(docs[0].metadata.get("similarity_score", 0.8), 3) if docs else 0.0,
    )


def clear_session(session_id: str) -> None:
    """Clear memory for a session (e.g., on new conversation)."""
    if session_id in _session_memories:
        _session_memories[session_id].clear()
        logger.info("Cleared memory for session: %s", session_id)
