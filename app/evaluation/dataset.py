
import json
import os
from pathlib import Path

from langsmith import Client


DATASET_NAME = "codemind-code-retrieval-v1"


def load_examples(path: str):
    examples = []

    with Path(path).open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            item = json.loads(line)

            query = item.get("query")
            relevant_ids = item.get("relevant_chunk_ids")

            if not isinstance(query, str) or not query.strip():
                raise ValueError(
                    f"Invalid query on line {line_number}"
                )

            if not isinstance(relevant_ids, list) or not relevant_ids:
                raise ValueError(
                    f"Missing relevant_chunk_ids on line {line_number}"
                )

            examples.append(
                {
                    "inputs": {"query": query},
                    "outputs": {
                        "relevant_chunk_ids": relevant_ids
                    },
                }
            )

    if not examples:
        raise ValueError("Evaluation dataset is empty")

    return examples


def create_dataset(path: str):
    if not os.getenv("LANGSMITH_API_KEY"):
        raise RuntimeError("LANGSMITH_API_KEY is not configured")

    client = Client()

    existing = list(
        client.list_datasets(dataset_name=DATASET_NAME)
    )

    if existing:
        raise RuntimeError(
            f"Dataset '{DATASET_NAME}' already exists. "
            "Use a new versioned dataset name or update it deliberately."
        )

    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description=(
            "Ground-truth benchmark for CodeMind code retrieval. "
            "Each example contains a query and relevant chunk IDs."
        ),
    )

    examples = load_examples(path)

    for example in examples:
        client.create_example(
            inputs=example["inputs"],
            outputs=example["outputs"],
            dataset_id=dataset.id,
        )

    print(f"Created dataset: {DATASET_NAME}")
    print(f"Examples: {len(examples)}")


if __name__ == "__main__":
    create_dataset("data/retrieval_eval.jsonl")
