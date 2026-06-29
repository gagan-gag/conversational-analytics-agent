"""
eval/sql_eval.py — NL→SQL accuracy evaluation.

For each test case:
  1. Send the natural language question to the SQL agent
  2. Compare the generated SQL semantically (normalised comparison)
  3. Execute both expected and generated SQL, compare result shapes/values
  4. Log accuracy % to eval_results.json
"""
from __future__ import annotations

import json
import logging
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
RESULTS_PATH = Path("eval_results.json")
TEST_CASES_PATH = Path(__file__).parent / "test_cases.json"


def _normalise_sql(sql: str) -> str:
    """Normalise SQL for comparison: lowercase, collapse whitespace, strip semicolons."""
    sql = sql.lower().strip().rstrip(";")
    sql = re.sub(r"\s+", " ", sql)
    sql = re.sub(r"\s*,\s*", ", ", sql)
    return sql


def _exec_sql(sql: str, db_path: str) -> list[dict]:
    """Execute SQL on SQLite, return rows as list of dicts."""
    try:
        uri = f"file:{db_path}?mode=ro"
        con = sqlite3.connect(uri, uri=True)
        con.row_factory = sqlite3.Row
        cur = con.execute(sql + " LIMIT 500")
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        con.close()
        return rows
    except Exception as e:
        logger.debug("SQL exec error: %s | %s", e, sql[:80])
        return []


def _results_match(expected_rows: list, generated_rows: list, result_type: str) -> bool:
    """
    Compare expected vs generated results.
    Uses shape matching for multi_row, value matching for single_value.
    """
    if not expected_rows and not generated_rows:
        return True
    if not expected_rows or not generated_rows:
        return False

    if result_type == "single_value":
        # Compare first cell
        try:
            ev = list(expected_rows[0].values())[0]
            gv = list(generated_rows[0].values())[0]
            # Allow 5% tolerance for floats
            if isinstance(ev, (int, float)) and isinstance(gv, (int, float)):
                return abs(float(ev) - float(gv)) / (abs(float(ev)) + 1e-9) < 0.05
            return str(ev).strip() == str(gv).strip()
        except Exception:
            return False

    elif result_type == "single_row":
        if len(generated_rows) < 1:
            return False
        # Compare column count matches
        return len(expected_rows[0]) == len(generated_rows[0])

    else:  # multi_row
        # Check same number of columns and at least some rows
        if not expected_rows or not generated_rows:
            return False
        return len(expected_rows[0]) == len(generated_rows[0])


def run_sql_eval() -> dict[str, Any]:
    """
    Run all 30 NL→SQL test cases.
    Returns accuracy metrics and per-case breakdown.
    """
    from config import get_settings
    settings = get_settings()

    logger.info("Starting SQL evaluation (%s)...", settings.sqlite_db_path)

    if not Path(settings.sqlite_db_path).exists():
        return {
            "error": f"SQLite DB not found at {settings.sqlite_db_path}. Run data/seed_db.py first.",
            "status": "failed",
        }

    test_cases = json.loads(TEST_CASES_PATH.read_text())["sql"]

    from sql_agent.agent import query_sql

    total = len(test_cases)
    passed_sql_match = 0
    passed_result_match = 0
    case_results = []

    for i, case in enumerate(test_cases):
        q = case["question"]
        expected_sql = case["expected_sql"]
        result_type = case.get("expected_result_type", "multi_row")

        try:
            # Generate SQL via agent
            agent_result = query_sql(q, session_id="eval_sql")
            generated_sql = agent_result.sql_query or ""

            # 1. SQL normalisation match
            sql_match = _normalise_sql(expected_sql) == _normalise_sql(generated_sql)

            # 2. Execute both and compare results
            expected_rows = _exec_sql(expected_sql, settings.sqlite_db_path)
            generated_rows = _exec_sql(generated_sql, settings.sqlite_db_path) if generated_sql else []
            result_match = _results_match(expected_rows, generated_rows, result_type)

            if sql_match:
                passed_sql_match += 1
            if result_match:
                passed_result_match += 1

            case_results.append({
                "question": q,
                "expected_sql": expected_sql,
                "generated_sql": generated_sql,
                "sql_exact_match": sql_match,
                "result_match": result_match,
                "status": "pass" if result_match else "fail",
            })

            logger.debug(
                "[%d/%d] %s | SQL match: %s | Result match: %s",
                i + 1, total, q[:50], sql_match, result_match,
            )

        except Exception as e:
            logger.warning("Case %d failed: %s | Error: %s", i + 1, q[:60], e)
            case_results.append({
                "question": q,
                "expected_sql": expected_sql,
                "generated_sql": "",
                "sql_exact_match": False,
                "result_match": False,
                "status": "error",
                "error": str(e),
            })

    sql_accuracy = round(100 * passed_sql_match / total, 2)
    result_accuracy = round(100 * passed_result_match / total, 2)

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "SQL",
        "n_cases": total,
        "metrics": {
            "sql_exact_match_accuracy_pct": sql_accuracy,
            "result_match_accuracy_pct": result_accuracy,
            "passed_sql_match": passed_sql_match,
            "passed_result_match": passed_result_match,
        },
        "cases": case_results,
        "status": "success",
    }

    _save_results("sql", result)
    logger.info(
        "SQL eval complete: SQL accuracy=%.1f%%, Result accuracy=%.1f%%",
        sql_accuracy, result_accuracy,
    )
    return result


def _save_results(key: str, data: dict) -> None:
    existing = {}
    if RESULTS_PATH.exists():
        try:
            existing = json.loads(RESULTS_PATH.read_text())
        except Exception:
            pass
    existing[key] = data
    RESULTS_PATH.write_text(json.dumps(existing, indent=2))
