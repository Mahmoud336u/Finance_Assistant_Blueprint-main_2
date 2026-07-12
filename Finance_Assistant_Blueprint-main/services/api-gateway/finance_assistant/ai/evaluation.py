"""Meridian AI — RAGAS Evaluation Pipeline.

Automated evaluation of RAG quality using the RAGAS framework.
Measures:
- Faithfulness: Are answers grounded in the retrieved context?
- Answer Relevancy: Is the answer relevant to the question?
- Context Precision: Are the retrieved chunks precise/relevant?
- Context Recall: Are all needed facts retrieved?

Per blueprint Section 17.2 — AI Quality Monitoring.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..logging import get_logger

logger = get_logger(__name__)


@dataclass
class EvalSample:
    """A single evaluation sample for the RAGAS pipeline."""

    question: str
    answer: str
    contexts: list[str]
    ground_truth: str | None = None


@dataclass
class EvalResult:
    """Results from a RAGAS evaluation run."""

    faithfulness: float = 0.0
    answer_relevancy: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0
    num_samples: int = 0
    evaluated_at: str = ""
    details: list[dict] = field(default_factory=list)

    @property
    def overall_score(self) -> float:
        """Weighted average of all metrics."""
        if self.num_samples == 0:
            return 0.0
        return (
            self.faithfulness * 0.3
            + self.answer_relevancy * 0.3
            + self.context_precision * 0.2
            + self.context_recall * 0.2
        )

    @property
    def is_passing(self) -> bool:
        """Check if the evaluation meets minimum quality thresholds."""
        return (
            self.faithfulness >= 0.8
            and self.answer_relevancy >= 0.7
            and self.overall_score >= 0.75
        )


# ============================================================
# Built-in Financial Evaluation Dataset
# ============================================================

EVAL_DATASET: list[EvalSample] = [
    EvalSample(
        question="What is the 50/30/20 budgeting rule?",
        answer="",  # To be filled by the RAG pipeline
        contexts=[],  # To be filled by the retriever
        ground_truth=(
            "The 50/30/20 rule divides after-tax income into needs (50%), "
            "wants (30%), and savings (20%)."
        ),
    ),
    EvalSample(
        question="How do I set up an emergency fund?",
        answer="",
        contexts=[],
        ground_truth=(
            "An emergency fund should cover 3-6 months of essential expenses, "
            "kept in a high-yield savings account for easy access."
        ),
    ),
    EvalSample(
        question="What is compound interest?",
        answer="",
        contexts=[],
        ground_truth=(
            "Compound interest is interest calculated on the initial principal "
            "and also on the accumulated interest of previous periods."
        ),
    ),
    EvalSample(
        question="What is a good debt-to-income ratio?",
        answer="",
        contexts=[],
        ground_truth=(
            "A good debt-to-income ratio is below 36%, with no more than 28% "
            "going toward housing costs. Above 43% is generally considered risky."
        ),
    ),
    EvalSample(
        question="How does a credit score work?",
        answer="",
        contexts=[],
        ground_truth=(
            "Credit scores range from 300-850 and are based on payment history (35%), "
            "amounts owed (30%), length of credit history (15%), credit mix (10%), "
            "and new credit (10%)."
        ),
    ),
]


async def run_evaluation(
    eval_fn,
    samples: list[EvalSample] | None = None,
) -> EvalResult:
    """Run a RAGAS-style evaluation on the RAG pipeline.

    Args:
        eval_fn: An async function that takes a question (str) and returns
                 a tuple of (answer: str, contexts: list[str]).
        samples: Optional custom evaluation dataset. Defaults to built-in dataset.

    Returns:
        EvalResult with scores across all metrics.
    """
    dataset = samples or EVAL_DATASET
    results: list[dict] = []

    for sample in dataset:
        try:
            answer, contexts = await eval_fn(sample.question)
            sample.answer = answer
            sample.contexts = contexts

            # Score individual sample
            faith = _score_faithfulness(answer, contexts)
            relevance = _score_answer_relevancy(answer, sample.question)
            precision = _score_context_precision(contexts, sample.question)
            recall = _score_context_recall(
                contexts, sample.ground_truth
            ) if sample.ground_truth else 0.5

            results.append({
                "question": sample.question,
                "faithfulness": faith,
                "answer_relevancy": relevance,
                "context_precision": precision,
                "context_recall": recall,
            })

        except Exception as exc:
            await logger.aerror(
                "Evaluation sample failed",
                question=sample.question,
                error=str(exc),
            )
            results.append({
                "question": sample.question,
                "error": str(exc),
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "context_precision": 0.0,
                "context_recall": 0.0,
            })

    # Aggregate
    n = len(results)
    if n == 0:
        return EvalResult(evaluated_at=datetime.now(timezone.utc).isoformat())

    avg = lambda key: sum(r.get(key, 0) for r in results) / n  # noqa: E731

    eval_result = EvalResult(
        faithfulness=round(avg("faithfulness"), 4),
        answer_relevancy=round(avg("answer_relevancy"), 4),
        context_precision=round(avg("context_precision"), 4),
        context_recall=round(avg("context_recall"), 4),
        num_samples=n,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
        details=results,
    )

    await logger.ainfo(
        "RAGAS evaluation complete",
        overall_score=eval_result.overall_score,
        faithfulness=eval_result.faithfulness,
        answer_relevancy=eval_result.answer_relevancy,
        is_passing=eval_result.is_passing,
        num_samples=n,
    )

    return eval_result


# ============================================================
# Scoring Functions (simplified RAGAS-compatible metrics)
# ============================================================


def _score_faithfulness(answer: str, contexts: list[str]) -> float:
    """Score how faithful the answer is to the provided contexts.

    Simple heuristic: what fraction of sentences in the answer
    can be traced to the context?
    """
    if not answer or not contexts:
        return 0.0

    combined_context = " ".join(contexts).lower()
    sentences = [s.strip() for s in answer.split(".") if len(s.strip()) > 10]

    if not sentences:
        return 0.5

    grounded = 0
    for sentence in sentences:
        # Check if key terms from the sentence appear in context
        words = set(sentence.lower().split())
        context_words = set(combined_context.split())
        overlap = words & context_words
        # If > 40% of significant words overlap, consider it grounded
        significant_words = {w for w in words if len(w) > 3}
        if significant_words:
            ratio = len(overlap & significant_words) / len(significant_words)
            if ratio > 0.4:
                grounded += 1

    return grounded / len(sentences)


def _score_answer_relevancy(answer: str, question: str) -> float:
    """Score how relevant the answer is to the question.

    Simple heuristic: keyword overlap between question and answer.
    """
    if not answer or not question:
        return 0.0

    q_words = {w.lower() for w in question.split() if len(w) > 3}
    a_words = {w.lower() for w in answer.split() if len(w) > 3}

    if not q_words:
        return 0.5

    overlap = q_words & a_words
    return min(len(overlap) / len(q_words), 1.0)


def _score_context_precision(contexts: list[str], question: str) -> float:
    """Score how precise/relevant the retrieved contexts are.

    Higher score = more contexts are relevant to the question.
    """
    if not contexts:
        return 0.0

    q_words = {w.lower() for w in question.split() if len(w) > 3}
    relevant = 0

    for ctx in contexts:
        ctx_words = {w.lower() for w in ctx.split() if len(w) > 3}
        overlap = q_words & ctx_words
        if len(overlap) >= 2:  # At least 2 overlapping keywords
            relevant += 1

    return relevant / len(contexts)


def _score_context_recall(contexts: list[str], ground_truth: str) -> float:
    """Score how much of the ground truth is covered by contexts.

    Higher score = ground truth facts are present in retrieved context.
    """
    if not contexts or not ground_truth:
        return 0.0

    gt_words = {w.lower() for w in ground_truth.split() if len(w) > 3}
    combined = " ".join(contexts).lower()
    combined_words = set(combined.split())

    if not gt_words:
        return 0.5

    found = gt_words & combined_words
    return len(found) / len(gt_words)
