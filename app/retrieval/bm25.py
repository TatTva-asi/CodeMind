
from __future__ import annotations

import json
import os
import re
import tempfile

from pathlib import Path
from dataclasses import dataclass
from typing import Any

from rank_bm25 import BM25Okapi

from app.retrieval.records import CodeChunkRecord
from app.retrieval.dense import RetrievalResult


_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+")


def tokenize_code(text: str) -> list[str]:
    """
    Preserve identifiers and split them into useful components.
    """
    tokens = []

    for raw in _TOKEN_PATTERN.findall(text):
        normalized = raw.lower()
        tokens.append(normalized)

        # snake_case and other underscore-separated identifiers
        parts = [part for part in normalized.split("_") if part]
        tokens.extend(parts)

        # CamelCase identifiers
        camel_parts = _CAMEL_BOUNDARY.sub(" ", raw).lower().split()
        tokens.extend(camel_parts)

        # Dotted and namespace-qualified names are naturally
        # separated by the token pattern.
    
    return tokens


@dataclass(frozen=True)
class LexicalRecord:
    chunk_id: str
    text: str
    metadata: dict[str, Any]


class BM25Retriever:
    def __init__(
        self,
        persist_path: str = "./storage/bm25/index.json",
        k1: float = 1.5,
        b: float = 0.75,
        exact_match_boost: float = 1.0,
    ):
        self.persist_path = Path(persist_path)
        self.k1 = k1
        self.b = b
        self.exact_match_boost = exact_match_boost

        self.records: list[LexicalRecord] = []
        self.tokenized_corpus: list[list[str]] = []
        self.bm25: BM25Okapi | None = None

        if self.persist_path.exists():
            self.load()

    def build(self, chunks: list[Any]) -> int:
        records = [
            chunk if isinstance(chunk, CodeChunkRecord)
            else CodeChunkRecord.from_object(chunk)
            for chunk in chunks
        ]

        ids = [record.chunk_id for record in records]

        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate chunk IDs in BM25 input")

        self.records = [
            LexicalRecord(
                chunk_id=record.chunk_id,
                text=record.text,
                metadata=record.metadata,
            )
            for record in records
        ]

        self._rebuild()
        self.save()

        return len(self.records)

    def _rebuild(self) -> None:
        self.tokenized_corpus = [
            tokenize_code(
                record.text
                + " "
                + " ".join(
                    str(value)
                    for key, value in record.metadata.items()
                    if key in {
                        "symbol_name",
                        "file_path",
                        "language",
                        "chunk_type",
                    }
                )
            )
            for record in self.records
        ]

        self.bm25 = (
            BM25Okapi(
                self.tokenized_corpus,
                k1=self.k1,
                b=self.b,
            )
            if self.tokenized_corpus
            else None
        )

    def save(self) -> None:
        self.persist_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "schema_version": 1,
            "k1": self.k1,
            "b": self.b,
            "records": [
                {
                    "chunk_id": record.chunk_id,
                    "text": record.text,
                    "metadata": record.metadata,
                }
                for record in self.records
            ],
        }

        # Atomic replacement prevents partially written indexes.
        fd, temporary_path = tempfile.mkstemp(
            dir=self.persist_path.parent,
            suffix=".tmp",
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(payload, file, ensure_ascii=False)

            os.replace(temporary_path, self.persist_path)

        finally:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)

    def load(self) -> None:
        with self.persist_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            payload = json.load(file)

        if payload.get("schema_version") != 1:
            raise ValueError("Unsupported BM25 index schema")

        self.records = [
            LexicalRecord(
                chunk_id=item["chunk_id"],
                text=item["text"],
                metadata=item.get("metadata", {}),
            )
            for item in payload["records"]
        ]

        self._rebuild()

    @staticmethod
    def _exact_match(
        query: str,
        record: LexicalRecord,
    ) -> bool:
        normalized_query = query.strip().lower()

        if not normalized_query:
            return False

        symbol = str(
            record.metadata.get("symbol_name", "")
        ).lower()

        if symbol and normalized_query == symbol:
            return True

        # Exact identifier match inside the source text.
        identifiers = {
            token.lower()
            for token in _TOKEN_PATTERN.findall(record.text)
        }

        return normalized_query in identifiers

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[RetrievalResult]:

        if not query.strip():
            raise ValueError("Query cannot be empty")

        if top_k <= 0:
            raise ValueError("top_k must be positive")

        if self.bm25 is None:
            return []

        query_tokens = tokenize_code(query)

        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        ranked = []

        for index, (record, score) in enumerate(
            zip(self.records, scores)
        ):
            exact = self._exact_match(query, record)

            # Exact symbol matches sort ahead of ordinary BM25
            # matches. The score remains available for analysis.
            adjusted_score = float(score)

            if exact:
                adjusted_score += self.exact_match_boost

            ranked.append(
                (
                    exact,
                    adjusted_score,
                    float(score),
                    index,
                    record,
                )
            )

        ranked.sort(
            key=lambda item: (
                item[0],
                item[1],
                -item[3],
            ),
            reverse=True,
        )

        results = []

        for exact, adjusted, raw_score, _, record in ranked[:top_k]:
            results.append(
                RetrievalResult(
                    chunk_id=record.chunk_id,
                    text=record.text,
                    metadata=record.metadata,
                    score=adjusted,
                    retriever="bm25",
                )
            )

        return results
