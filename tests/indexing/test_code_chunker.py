
import pytest

from app.indexing.chunk_models import CodeChunk
from app.indexing.hierarchy import ChunkHierarchy


def create_chunk(chunk_id, parent_id=None):
    return CodeChunk(
        chunk_id=chunk_id,
        file_path="payment.py",
        content="def example(): pass",
        symbol_name=chunk_id,
        symbol_type="function",
        start_line=1,
        end_line=5,
        parent_id=parent_id
    )


def test_add_parent_and_child():

    hierarchy = ChunkHierarchy()

    parent = create_chunk("class_1")
    child = create_chunk("method_1", "class_1")

    hierarchy.add_chunk(parent)
    hierarchy.add_chunk(child)

    assert hierarchy.get_parent("method_1") == parent
    assert child in hierarchy.get_children("class_1")


def test_get_descendants():

    hierarchy = ChunkHierarchy()

    parent = create_chunk("class_1")
    child = create_chunk("method_1", "class_1")
    nested = create_chunk("nested_1", "method_1")

    hierarchy.add_chunk(parent)
    hierarchy.add_chunk(child)
    hierarchy.add_chunk(nested)

    descendants = hierarchy.get_descendants("class_1")

    assert len(descendants) == 2
    assert nested in descendants


def test_duplicate_chunk_id():

    hierarchy = ChunkHierarchy()

    hierarchy.add_chunk(create_chunk("chunk_1"))

    with pytest.raises(ValueError):
        hierarchy.add_chunk(create_chunk("chunk_1"))


def test_missing_parent():

    hierarchy = ChunkHierarchy()

    with pytest.raises(ValueError):
        hierarchy.add_chunk(
            create_chunk("child_1", "missing_parent")
        )
