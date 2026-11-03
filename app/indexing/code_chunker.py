# our proposed chunk would store chunk_id, file_path, content, symbol_name, symbol_type, start_line, end_line, parent_id, child_id, metadata

# it has one primary job => convert parsed source code strucutres into code chunk objects
# its input is original source code , file path, parsed file containing extracted symbol and its output is list of structured codechunk objects


# app/indexing/code_chunker.py

from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any

from app.parsing.parser_models import ParsedFile


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


class CodeChunker:

    def chunk_file(
        self,
        file_path: str,
        source_code: str,
        parsed_file: ParsedFile,
    ) -> list[CodeChunk]:

        lines = source_code.splitlines()

        if not lines:
            return []

        symbols = parsed_file.symbols

        # Handle files that contain no extracted symbols.
        if not symbols:
            chunk_id = self._generate_chunk_id(
                file_path,
                "__file__",
                "file",
            )

            return [
                CodeChunk(
                    chunk_id=chunk_id,
                    file_path=file_path,
                    content=source_code,
                    symbol_name=Path(file_path).name,
                    symbol_type="file",
                    start_line=1,
                    end_line=len(lines),
                    metadata={
                        "language": parsed_file.language,
                    },
                )
            ]

        chunks = []
        symbol_to_chunk = {}

        # First pass: create one chunk for each valid symbol.
        for symbol in symbols:

            if (
                symbol.start_line < 1
                or symbol.end_line < symbol.start_line
                or symbol.end_line > len(lines)
            ):
                continue

            content = "\n".join(
                lines[symbol.start_line - 1:symbol.end_line]
            )

            chunk_id = self._generate_chunk_id(
                file_path,
                symbol.qualified_name,
                symbol.kind,
            )

            chunk = CodeChunk(
                chunk_id=chunk_id,
                file_path=file_path,
                content=content,
                symbol_name=symbol.name,
                symbol_type=symbol.kind,
                start_line=symbol.start_line,
                end_line=symbol.end_line,
                metadata={
                    "qualified_name": symbol.qualified_name,
                    "signature": symbol.signature,
                    "docstring": symbol.docstring,
                    "language": parsed_file.language,
                },
            )

            chunks.append(chunk)
            symbol_to_chunk[symbol.qualified_name] = chunk

        # Second pass: establish parent-child relationships.
        for symbol in symbols:

            chunk = symbol_to_chunk.get(symbol.qualified_name)

            if chunk is None:
                continue

            parent_name = symbol.qualified_name.rpartition(".")[0]

            parent_chunk = symbol_to_chunk.get(parent_name)

            if parent_chunk is not None:
                chunk.parent_id = parent_chunk.chunk_id

        # Return parent chunks before their descendants.
        chunks.sort(
            key=lambda chunk: (
                chunk.metadata["qualified_name"].count("."),
                chunk.start_line,
            )
        )

        return chunks

    @staticmethod
    def _generate_chunk_id(
        file_path: str,
        qualified_name: str,
        symbol_type: str,
    ) -> str:

        identity = (
            f"{file_path}:{qualified_name}:{symbol_type}"
        )

        return sha256(
            identity.encode("utf-8")
        ).hexdigest()
