
import pytest

from app.indexing.code_chunker import CodeChunker
from app.indexing.hierarchy import ChunkHierarchy
from app.parsing.parser_models import ParsedFile, Symbol


@pytest.fixture
def source_code():
    return '''class UserService:
    def authenticate(self, username):
        return self.get_user(username)

    def get_user(self, username):
        return username
'''


@pytest.fixture
def parsed_file():
    symbols = [
        Symbol(
            name="UserService",
            qualified_name="UserService",
            kind="class",
            start_line=1,
            end_line=6,
            signature="UserService",
            docstring=None,
            decorators=[],
            parameters=[],
            return_annotation=None,
        ),
        Symbol(
            name="authenticate",
            qualified_name="UserService.authenticate",
            kind="method",
            start_line=2,
            end_line=3,
            signature="authenticate(self, username)",
            docstring=None,
            decorators=[],
            parameters=[],
            return_annotation=None,
        ),
        Symbol(
            name="get_user",
            qualified_name="UserService.get_user",
            kind="method",
            start_line=5,
            end_line=6,
            signature="get_user(self, username)",
            docstring=None,
            decorators=[],
            parameters=[],
            return_annotation=None,
        ),
    ]

    return ParsedFile(
        file_path="user_service.py",
        language="python",
        symbols=symbols,
        imports=[],
        status="success",
        error=None,
    )


@pytest.fixture
def chunks(source_code, parsed_file):
    chunker = CodeChunker()

    return chunker.chunk_file(
        file_path="user_service.py",
        source_code=source_code,
        parsed_file=parsed_file,
    )


def test_chunker_creates_expected_chunks(chunks):
    assert len(chunks) == 3

    names = {chunk.symbol_name for chunk in chunks}

    assert names == {
        "UserService",
        "authenticate",
        "get_user",
    }


def test_chunker_preserves_source_content(chunks):
    authenticate = next(
        chunk for chunk in chunks
        if chunk.symbol_name == "authenticate"
    )

    assert "self.get_user(username)" in authenticate.content


def test_chunker_preserves_line_ranges(chunks):
    authenticate = next(
        chunk for chunk in chunks
        if chunk.symbol_name == "authenticate"
    )

    assert authenticate.start_line == 2
    assert authenticate.end_line == 3


def test_chunk_ids_are_unique(chunks):
    chunk_ids = [chunk.chunk_id for chunk in chunks]

    assert len(chunk_ids) == len(set(chunk_ids))


def test_chunk_ids_are_deterministic(
    source_code,
    parsed_file,
):
    chunker = CodeChunker()

    first = chunker.chunk_file(
        "user_service.py",
        source_code,
        parsed_file,
    )

    second = chunker.chunk_file(
        "user_service.py",
        source_code,
        parsed_file,
    )

    assert [c.chunk_id for c in first] == [
        c.chunk_id for c in second
    ]


def test_parent_child_relationships(chunks):
    class_chunk = next(
        chunk for chunk in chunks
        if chunk.symbol_name == "UserService"
    )

    authenticate = next(
        chunk for chunk in chunks
        if chunk.symbol_name == "authenticate"
    )

    get_user = next(
        chunk for chunk in chunks
        if chunk.symbol_name == "get_user"
    )

    assert authenticate.parent_id == class_chunk.chunk_id
    assert get_user.parent_id == class_chunk.chunk_id


def test_hierarchy_add_and_get(chunks):
    hierarchy = ChunkHierarchy()

    for chunk in chunks:
        hierarchy.add_chunk(chunk)

    class_chunk = next(
        chunk for chunk in chunks
        if chunk.symbol_name == "UserService"
    )

    retrieved = hierarchy.get_chunk(class_chunk.chunk_id)

    assert retrieved is class_chunk


def test_hierarchy_get_parent(chunks):
    hierarchy = ChunkHierarchy()

    for chunk in chunks:
        hierarchy.add_chunk(chunk)

    authenticate = next(
        chunk for chunk in chunks
        if chunk.symbol_name == "authenticate"
    )

    parent = hierarchy.get_parent(authenticate.chunk_id)

    assert parent is not None
    assert parent.symbol_name == "UserService"


def test_hierarchy_get_children(chunks):
    hierarchy = ChunkHierarchy()

    for chunk in chunks:
        hierarchy.add_chunk(chunk)

    class_chunk = next(
        chunk for chunk in chunks
        if chunk.symbol_name == "UserService"
    )

    children = hierarchy.get_children(class_chunk.chunk_id)

    assert {child.symbol_name for child in children} == {
        "authenticate",
        "get_user",
    }


def test_hierarchy_get_descendants(chunks):
    hierarchy = ChunkHierarchy()

    for chunk in chunks:
        hierarchy.add_chunk(chunk)

    class_chunk = next(
        chunk for chunk in chunks
        if chunk.symbol_name == "UserService"
    )

    descendants = hierarchy.get_descendants(
        class_chunk.chunk_id
    )

    assert len(descendants) == 2


def test_duplicate_chunk_is_rejected(chunks):
    hierarchy = ChunkHierarchy()

    hierarchy.add_chunk(chunks[0])

    with pytest.raises(ValueError):
        hierarchy.add_chunk(chunks[0])


def test_missing_parent_is_rejected(chunks):
    hierarchy = ChunkHierarchy()

    child = next(
        chunk for chunk in chunks
        if chunk.symbol_name == "authenticate"
    )

    with pytest.raises(ValueError):
        hierarchy.add_chunk(child)


