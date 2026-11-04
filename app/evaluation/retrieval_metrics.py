
from __future__ import annotations


def recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    if k <= 0:
        raise ValueError("k must be positive")

    if not relevant_ids:
        return 0.0

    retrieved = set(retrieved_ids[:k])

    return len(retrieved & relevant_ids) / len(relevant_ids)


def reciprocal_rank(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> float:
    if not relevant_ids:
        return 0.0

    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant_ids:
            return 1.0 / rank

    return 0.0


def make_recall_evaluator(k: int):
    def evaluator(inputs, outputs, reference_outputs):
        relevant = set(
            reference_outputs["relevant_chunk_ids"]
        )

        retrieved = outputs["chunk_ids"]

        return {
            "key": f"recall_at_{k}",
            "score": recall_at_k(retrieved, relevant, k),
        }

    return evaluator


def mrr_evaluator(inputs, outputs, reference_outputs):
    relevant = set(
        reference_outputs["relevant_chunk_ids"]
    )

    retrieved = outputs["chunk_ids"]

    return {
        "key": "mrr",
        "score": reciprocal_rank(retrieved, relevant),
    }
