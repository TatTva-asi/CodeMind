
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.indexing.embedding_index import EmbeddingIndex


@dataclass
class RetrievalResult:
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    score: float
    retriever: str


class DenseRetriever:
    def __init__(self, index: EmbeddingIndex):
        self.index = index

    def search(
        self,
        query: str,
        top_k: int = 10,
        where: dict | None = None,
    ) -> list[RetrievalResult]:

        if not query.strip():
            raise ValueError("Query cannot be empty")

        if top_k <= 0:
            raise ValueError("top_k must be positive")

        query_embedding = self.index.model.encode_query(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        collection = self.index.collection

        if collection.count() == 0:
            return []

        result = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=min(top_k, collection.count()),
            where=where,
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        retrieved = []

        ids = result["ids"][0]
        documents = result["documents"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]

        for chunk_id, document, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances,
        ):
            # Chroma cosine distance = 1 - cosine similarity.
            similarity = 1.0 - float(distance)

            retrieved.append(
                RetrievalResult(
                    chunk_id=chunk_id,
                    text=document,
                    metadata=metadata or {},
                    score=similarity,
                    retriever="dense",
                )
            )

        return retrieved
