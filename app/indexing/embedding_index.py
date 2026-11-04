
from __future__ import annotations

import os
from typing import Iterable, Any

import chromadb
from sentence_transformers import SentenceTransformer

from app.retrieval.records import CodeChunkRecord


class EmbeddingIndex:
    def __init__(
        self,
        model_name: str | None = None,
        persist_directory: str | None = None,
        collection_name: str | None = None,
        batch_size: int = 32,
        device: str | None = None,
    ):
        self.model_name = (
            model_name
            or os.getenv(
                "CODEMIND_EMBEDDING_MODEL",
                "Qwen/Qwen3-Embedding-0.6B",
            )
        )

        self.persist_directory = (
            persist_directory
            or os.getenv(
                "CODEMIND_CHROMA_PATH",
                "./storage/chroma",
            )
        )

        self.collection_name = (
            collection_name
            or os.getenv(
                "CODEMIND_CHROMA_COLLECTION",
                "codemind_code_chunks",
            )
        )

        self.batch_size = batch_size

        if batch_size <= 0:
            raise ValueError("batch_size must be positive")

        self.model = SentenceTransformer(
            self.model_name,
            device=device,
        )

        self.client = chromadb.PersistentClient(
            path=self.persist_directory
        )

        self.embedding_dimension = (
            self.model.get_embedding_dimension()
        )

        if not self.embedding_dimension:
            raise RuntimeError(
                "Could not determine embedding dimension"
            )

        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "hnsw:space": "cosine",
                "embedding_model": self.model_name,
                "embedding_dimension": self.embedding_dimension,
                "schema_version": "1",
            },
        )

        metadata = collection.metadata or {}

        stored_model = metadata.get("embedding_model")
        stored_dimension = metadata.get("embedding_dimension")

        if stored_model and stored_model != self.model_name:
            raise ValueError(
                "Embedding model mismatch. "
                f"Collection uses {stored_model}, "
                f"but configured model is {self.model_name}. "
                "Create a new collection and re-index."
            )

        if (
            stored_dimension is not None
            and int(stored_dimension) != self.embedding_dimension
        ):
            raise ValueError(
                "Embedding dimension mismatch. "
                "Create a new collection and re-index."
            )

        return collection

    @staticmethod
    def _chroma_metadata(metadata: dict[str, Any]) -> dict:
        """
        Chroma metadata supports scalar values.
        Convert nested values to strings rather than silently
        dropping source metadata.
        """
        result = {}

        for key, value in metadata.items():
            if value is None:
                continue

            if isinstance(value, (str, int, float, bool)):
                result[key] = value
            else:
                result[key] = str(value)

        return result or {"record_type": "code_chunk"}

    def _encode_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode_document(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return embeddings.tolist()

    def add_chunks(
        self,
        chunks: Iterable[Any],
    ) -> int:
        """
        Upsert chunks in batches.

        Existing IDs are updated; new IDs are inserted.
        Returns the number of processed chunks.
        """
        records = [
            chunk if isinstance(chunk, CodeChunkRecord)
            else CodeChunkRecord.from_object(chunk)
            for chunk in chunks
        ]

        if not records:
            return 0

        seen = set()
        for record in records:
            if record.chunk_id in seen:
                raise ValueError(
                    f"Duplicate chunk ID in batch: {record.chunk_id}"
                )
            seen.add(record.chunk_id)

        processed = 0

        for start in range(0, len(records), self.batch_size):
            batch = records[start:start + self.batch_size]

            ids = [record.chunk_id for record in batch]
            documents = [record.text for record in batch]

            embeddings = self._encode_documents(documents)

            metadatas = [
                self._chroma_metadata(record.metadata)
                for record in batch
            ]

            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            processed += len(batch)

        return processed

    def delete_chunks(self, chunk_ids: list[str]) -> None:
        if chunk_ids:
            self.collection.delete(ids=chunk_ids)

    def count(self) -> int:
        return self.collection.count()

    def reset_collection(self) -> None:
        """
        Destructive operation. Only call for an intentional
        complete rebuild.
        """
        self.client.delete_collection(self.collection_name)
        self.collection = self._get_or_create_collection()
