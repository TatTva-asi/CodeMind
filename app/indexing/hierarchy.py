
# app/indexing/hierarchy.py

# we have functions like add_chunk(), get_chunk(), get_parent(), get_children(), get_descendents() we used iterative stack based traversal rather than recursive traversal

from app.indexing.code_chunker import CodeChunk


class ChunkHierarchy:

    def __init__(self):
        self.chunks: dict[str, CodeChunk] = {}

    def add_chunk(self, chunk: CodeChunk) -> None:

        if chunk.chunk_id in self.chunks:
            raise ValueError(
                f"Duplicate chunk ID: {chunk.chunk_id}"
            )

        parent = None

        if chunk.parent_id is not None:

            parent = self.chunks.get(chunk.parent_id)

            if parent is None:
                raise ValueError(
                    f"Parent chunk not found: {chunk.parent_id}"
                )

            if chunk.chunk_id in parent.child_ids:
                raise ValueError(
                    f"Child already registered: {chunk.chunk_id}"
                )

        self.chunks[chunk.chunk_id] = chunk

        if parent is not None:
            parent.child_ids.append(chunk.chunk_id)

    def get_chunk(self, chunk_id: str) -> CodeChunk | None:
        return self.chunks.get(chunk_id)

    def get_parent(self, chunk_id: str) -> CodeChunk | None:

        chunk = self.get_chunk(chunk_id)

        if chunk is None or chunk.parent_id is None:
            return None

        return self.get_chunk(chunk.parent_id)

    def get_children(self, chunk_id: str) -> list[CodeChunk]:

        chunk = self.get_chunk(chunk_id)

        if chunk is None:
            return []

        return [
            self.chunks[child_id]
            for child_id in chunk.child_ids
            if child_id in self.chunks
        ]

    def get_descendants(self, chunk_id: str) -> list[CodeChunk]:

        if chunk_id not in self.chunks:
            return []

        descendants = []
        visited = set()
        stack = list(reversed(
            self.chunks[chunk_id].child_ids
        ))

        while stack:

            current_id = stack.pop()

            if current_id in visited:
                continue

            visited.add(current_id)

            current_chunk = self.chunks.get(current_id)

            if current_chunk is None:
                continue

            descendants.append(current_chunk)

            stack.extend(
                reversed(current_chunk.child_ids)
            )

        return descendants
