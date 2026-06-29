"""
eval/rag_eval.py — RAGAS evaluation for the RAG pipeline.

Metrics:
  - faithfulness:       Are claims in the answer supported by the retrieved context?
  - answer_relevancy:   Is the answer relevant to the question?
  - context_precision:  Are the retrieved chunks actually useful?

Results are appended to eval_results.json.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
RESULTS_PATH = Path("eval_results.json")
TEST_CASES_PATH = Path(__file__).parent / "test_cases.json"


def run_rag_eval() -> dict[str, Any]:
    """
    Run RAGAS evaluation against all RAG test cases.
    Returns dict with metric scores and per-question breakdown.
    """
    logger.info("Starting RAG evaluation...")

    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            faithfulness,
        )
    except ImportError:
        return {
            "error": "RAGAS not installed. Run: pip install ragas datasets",
            "status": "skipped",
        }

    # Load test cases
    test_cases = json.loads(TEST_CASES_PATH.read_text())["rag"]

    # Run RAG pipeline for each question
    from rag.chain import query_rag
    from rag.retriever import retrieve

    questions, answers, contexts, ground_truths = [], [], [], []

    for case in test_cases:
        q = case["question"]
        try:
            result = query_rag(q, session_id="eval_rag")
            retrieved_docs = retrieve(q)
            questions.append(q)
            answers.append(result.answer)
            contexts.append([d.page_content for d in retrieved_docs] or case.get("contexts", [""]))
            ground_truths.append(case["ground_truth"])
            logger.debug("Evaluated: %s", q[:60])
        except Exception as e:
            logger.warning("Skipping case (error: %s): %s", e, q[:60])

    if not questions:
        return {"error": "No test cases could be evaluated", "status": "failed"}

    # Build HuggingFace Dataset
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })

    # Run RAGAS
    try:
        score = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision],
        )
        scores_dict = score.to_pandas().mean(numeric_only=True).to_dict()
    except Exception as e:
        logger.error("RAGAS evaluation failed: %s", e)
        scores_dict = {"error": str(e)}

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "RAG",
        "n_cases": len(questions),
        "metrics": {k: round(float(v), 4) for k, v in scores_dict.items() if not isinstance(v, str)},
        "status": "success",
    }

    _save_results("rag", result)
    logger.info("RAG eval complete: %s", result["metrics"])
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
