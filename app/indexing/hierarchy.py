
class ChunkHierarchy:

    def __init__(self):
        self.chunks = {}

    def add_chunk(self, chunk):

        if chunk.chunk_id in self.chunks:
            raise ValueError(
                f"Duplicate chunk ID: {chunk.chunk_id}"
            )

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

        if chunk.parent_id is not None:
            parent.child_ids.append(chunk.chunk_id)

    def get_chunk(self, chunk_id):
        return self.chunks.get(chunk_id)

    def get_parent(self, chunk_id):

        chunk = self.get_chunk(chunk_id)

        if chunk is None or chunk.parent_id is None:
            return None

        return self.get_chunk(chunk.parent_id)

    def get_children(self, chunk_id):

        chunk = self.get_chunk(chunk_id)

        if chunk is None:
            return []

        return [
            self.chunks[child_id]
            for child_id in chunk.child_ids
            if child_id in self.chunks
        ]

    def get_descendants(self, chunk_id):

        descendants = []

        def traverse(current_id):

            for child in self.get_children(current_id):

                descendants.append(child)

                traverse(child.chunk_id)

        traverse(chunk_id)

        return descendants
