
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CodeChunkRecord:
    chunk_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.chunk_id.strip():
            raise ValueError("chunk_id cannot be empty")

        if not self.text.strip():
            raise ValueError(
                f"Chunk {self.chunk_id} has empty text"
            )

    @classmethod
    def from_object(cls, chunk: Any) -> "CodeChunkRecord":
        """
        Adapter for existing CodeMind chunk objects.

        Supports dictionaries and objects with common field names.
        Adjust this adapter if your Chunk model uses different names.
        """

        def read(obj, *names, default=None):
            for name in names:
                if isinstance(obj, dict) and name in obj:
                    return obj[name]
                if hasattr(obj, name):
                    return getattr(obj, name)
            return default

        chunk_id = read(chunk, "chunk_id", "id")
        text = read(chunk, "text", "content", "code")

        metadata = read(chunk, "metadata", default={}) or {}

        if not isinstance(metadata, dict):
            metadata = vars(metadata)

        metadata = dict(metadata)

        # Preserve useful source information when stored
        # directly on the existing chunk object.
        for key in (
            "file_path",
            "language",
            "symbol_name",
            "start_line",
            "end_line",
            "parent_id",
            "chunk_type",
        ):
            value = read(chunk, key)
            if value is not None:
                metadata.setdefault(key, value)

        if chunk_id is None or text is None:
            raise ValueError(
                "Chunk must expose an ID and text/content/code"
            )

        return cls(
            chunk_id=str(chunk_id),
            text=str(text),
            metadata=metadata,
        )
