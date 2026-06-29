"""
sql_agent/agent.py — Text-to-SQL agent using Groq LLM.

Flow:
  NL question
    → inject schema into system prompt
    → LLM generates SQL
    → guardrails.validate_sql()
    → execute on read-only SQLite
    → LLM formats result as human insight
    → return QueryResult(mode="SQL")
"""
from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


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

from langchain_groq import ChatGroq

from config import get_settings
from models.schemas import QueryResult, SourceRef
from sql_agent.guardrails import execute_safe
from sql_agent.schema_loader import get_schema_string

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── Session Memory ───────────────────────────────────────────────────────────
_sql_memories: dict[str, _SimpleWindowMemory] = {}


def _get_memory(session_id: str) -> _SimpleWindowMemory:
    if session_id not in _sql_memories:
        _sql_memories[session_id] = _SimpleWindowMemory(k=settings.memory_window_k)
    return _sql_memories[session_id]


# ─── LLM ──────────────────────────────────────────────────────────────────────
def _get_llm() -> ChatGroq:
    return ChatGroq(
        model=settings.model_name,
        groq_api_key=settings.groq_api_key,
        temperature=0.0,   # deterministic SQL generation
        max_tokens=512,
    )


# ─── SQL Extraction ───────────────────────────────────────────────────────────
def _extract_sql(text: str) -> str:
    """Pull the SQL out of LLM response (handles ```sql ... ``` blocks)."""
    # Try fenced code block first
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback: look for SELECT ... pattern
    match = re.search(r"((?:WITH|SELECT)\s+.+)", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


# ─── SQL Generation Prompt ────────────────────────────────────────────────────
_SQL_GEN_SYSTEM = """You are a precise SQLite query generator.

SCHEMA:
{schema}

RULES:
1. Generate ONLY a single SELECT (or WITH ... SELECT) statement.
2. NEVER use DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, CREATE, REPLACE.
3. Use exact table and column names from the schema above.
4. For aggregations, always include meaningful column aliases.
5. If the question requires a date range, use SQLite date functions.
6. Output ONLY the SQL query, wrapped in ```sql ... ``` fences. No explanation.

Conversation context:
{chat_history}
"""

# ─── Result Formatting Prompt ─────────────────────────────────────────────────
_FORMAT_SYSTEM = """You are a data analyst explaining query results.

Given a user question and the raw SQL results, write a concise, insightful 
answer in plain English. Highlight trends, totals, or notable findings.
Keep it to 3–5 sentences max. Do not repeat the raw data row-by-row.
"""


def query_sql(question: str, session_id: str = "default") -> QueryResult:
    """
    Run the full Text-to-SQL pipeline.

    Args:
        question:   Natural language question about the data.
        session_id: Per-user conversation memory key.

    Returns:
        QueryResult with answer, mode="SQL", sql_query, and optional raw_rows.
    """
    schema = get_schema_string()
    llm = _get_llm()
    memory = _get_memory(session_id)

    # Build chat history string
    history_msgs = memory.load_memory_variables({}).get("chat_history", [])
    history_str = "\n".join(
        f"{'Human' if m.type == 'human' else 'Assistant'}: {m.content}"
        for m in history_msgs
    ) if history_msgs else ""

    # ── Step 1: Generate SQL ──────────────────────────────────────────────────
    sql_system = _SQL_GEN_SYSTEM.format(schema=schema, chat_history=history_str)
    gen_response = llm.invoke([
        SystemMessage(content=sql_system),
        HumanMessage(content=f"Question: {question}\n\nSQL:"),
    ])
    raw_sql_text = gen_response.content.strip()
    generated_sql = _extract_sql(raw_sql_text)
    logger.info("Generated SQL: %s", generated_sql[:200])

    # ── Step 2: Validate + Execute ────────────────────────────────────────────
    rows = execute_safe(generated_sql)   # raises HTTPException on violation
    logger.info("SQL returned %d rows", len(rows))

    # ── Step 3: Format as insight ─────────────────────────────────────────────
    rows_preview = rows[:20]  # send at most 20 rows to formatter to stay in tokens
    rows_json = json.dumps(rows_preview, indent=2, default=str)

    format_response = llm.invoke([
        SystemMessage(content=_FORMAT_SYSTEM),
        HumanMessage(
            content=(
                f"Question: {question}\n\n"
                f"SQL executed:\n```sql\n{generated_sql}\n```\n\n"
                f"Results ({len(rows)} rows total, showing first {len(rows_preview)}):\n{rows_json}\n\n"
                "Answer:"
            )
        ),
    ])
    answer = format_response.content.strip()

    # ── Step 4: Save to memory ────────────────────────────────────────────────
    memory.save_context({"input": question}, {"output": answer})

    return QueryResult(
        answer=answer,
        mode="SQL",
        sql_query=generated_sql,
        raw_rows=rows[:100],  # cap rows returned in API response
        confidence=0.9 if rows else 0.4,
    )
