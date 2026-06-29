"""
router/query_router.py — Intelligent query routing via LLM classifier.

Classification:
  RAG    → question is about uploaded documents/text/policies
  SQL    → question is about data, counts, metrics, aggregations, trends
  Hybrid → question requires both document context and structured data

Routing:
  RAG    → rag/chain.py
  SQL    → sql_agent/agent.py
  Hybrid → call both, merge answers
"""
from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from config import get_settings
from models.schemas import QueryResult, SourceRef
from rag.chain import query_rag
from sql_agent.agent import query_sql

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── Classifier Prompt ────────────────────────────────────────────────────────
_CLASSIFIER_SYSTEM = """You are a query routing classifier for an analytics assistant.

Given a user question, classify it as EXACTLY ONE of these labels:
- RAG    → The question is about documents, text, policies, reports, or requires reading uploaded files.
- SQL    → The question is about counts, metrics, aggregations, trends, or querying structured data (customers, orders, events, churn).
- Hybrid → The question requires BOTH document context AND data from the database.

Rules:
1. Reply with ONLY the label: RAG, SQL, or Hybrid. Nothing else.
2. Default to SQL if the question mentions numbers, counts, or database concepts.
3. Default to RAG if it mentions "document", "policy", "report", "uploaded", "file".
4. Use Hybrid when context from both is needed.

Examples:
Q: "What is our refund policy?"           → RAG
Q: "How many customers churned last month?" → SQL
Q: "What does the report say about churn rates?" → Hybrid
"""


def classify_query(question: str) -> str:
    """
    Call LLM to classify query into RAG | SQL | Hybrid.
    Falls back to 'RAG' on error.
    """
    try:
        llm = ChatGroq(
            model=settings.model_name,
            groq_api_key=settings.groq_api_key,
            temperature=0.0,
            max_tokens=10,
        )
        response = llm.invoke([
            SystemMessage(content=_CLASSIFIER_SYSTEM),
            HumanMessage(content=f"Question: {question}\nLabel:"),
        ])
        label = response.content.strip().upper()
        # Normalise
        if label.startswith("SQL"):
            return "SQL"
        elif label.startswith("HYBRID"):
            return "Hybrid"
        else:
            return "RAG"
    except Exception as e:
        logger.warning("Classifier failed (%s), defaulting to RAG", e)
        return "RAG"


def route_query(question: str, session_id: str = "default") -> QueryResult:
    """
    Classify the question and route to the appropriate pipeline.

    Args:
        question:   Natural language user question.
        session_id: Session key for memory isolation.

    Returns:
        QueryResult with mode label attached.
    """
    mode = classify_query(question)
    logger.info("Query classified as: %s | Question: %s", mode, question[:80])

    if mode == "SQL":
        return query_sql(question, session_id)

    elif mode == "Hybrid":
        return _hybrid_query(question, session_id)

    else:  # RAG (default)
        return query_rag(question, session_id)


def _hybrid_query(question: str, session_id: str) -> QueryResult:
    """
    Run both RAG and SQL, then merge answers with a synthesis prompt.
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = ChatGroq(
        model=settings.model_name,
        groq_api_key=settings.groq_api_key,
        temperature=0.1,
        max_tokens=1024,
    )

    # Run both pipelines concurrently (sequentially here for simplicity)
    rag_result = query_rag(question, session_id=f"{session_id}_rag")
    sql_result = query_sql(question, session_id=f"{session_id}_sql")

    # Merge
    merge_prompt = f"""You are a senior analyst. Combine these two answers into one coherent response:

DOCUMENT CONTEXT ANSWER:
{rag_result.answer}

DATA ANALYSIS ANSWER:
{sql_result.answer}

Write a unified answer that integrates both perspectives. Be concise (4–6 sentences max).
Cite document sources where relevant."""

    merge_response = llm.invoke([
        SystemMessage(content="You are a precise analyst combining document and data insights."),
        HumanMessage(content=merge_prompt),
    ])

    combined_answer = merge_response.content.strip()
    all_sources = rag_result.sources + sql_result.sources

    return QueryResult(
        answer=combined_answer,
        mode="Hybrid",
        sources=all_sources,
        sql_query=sql_result.sql_query,
        raw_rows=sql_result.raw_rows,
        confidence=round((rag_result.confidence + sql_result.confidence) / 2, 3),
    )
