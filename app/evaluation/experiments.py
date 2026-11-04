import os


from langsmith import evaluate
from dotenv import load_dotenv

load_dotenv()
from app.indexing.embedding_index import EmbeddingIndex
from app.retrieval.dense import DenseRetriever
from app.retrieval.bm25 import BM25Retriever

from app.evaluation.retrieval_metrics import (
    make_recall_evaluator,
    mrr_evaluator,
)


DATASET_NAME = "codemind-code-retrieval-v1"


def run_experiment(retriever, retriever_name: str):
    def target(inputs: dict):
        results = retriever.search(
            query=inputs["query"],
            top_k=20,
        )

        return {
            "chunk_ids": [
                result.chunk_id for result in results
            ],
            "scores": [
                result.score for result in results
            ],
        }

    evaluators = [
        make_recall_evaluator(1),
        make_recall_evaluator(5),
        make_recall_evaluator(10),
        mrr_evaluator,
    ]

    return evaluate(
        target,
        data=DATASET_NAME,
        evaluators=evaluators,
        experiment_prefix=f"codemind-{retriever_name}",
        max_concurrency=1,
    )


def main():
    # Dense experiment
    embedding_index = EmbeddingIndex()
    dense_retriever = DenseRetriever(embedding_index)

    dense_results = run_experiment(
        dense_retriever,
        "dense",
    )

    print("Dense experiment completed:")
    print(dense_results)

    # BM25 experiment
    bm25_retriever = BM25Retriever()

    if bm25_retriever.bm25 is None:
        raise RuntimeError(
            "BM25 index is empty. Build the lexical index first."
        )

    bm25_results = run_experiment(
        bm25_retriever,
        "bm25",
    )

    print("BM25 experiment completed:")
    print(bm25_results)


if __name__ == "__main__":
    main()
