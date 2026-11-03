
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CodeChunk:

    chunk_id: str
    file_path: str

    content: str

    symbol_name: str
    symbol_type: str

    start_line: int
    end_line: int

    parent_id: str | None = None
    child_ids: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)
