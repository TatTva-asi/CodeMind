
import hashlib
from pathlib import Path


class FileHasher:

    def __init__(self, algorithm="sha256", chunk_size=65536):
        self.algorithm = algorithm
        self.chunk_size = chunk_size

    def hash_file(self, file_path: str | Path) -> str:

        file_path = Path(file_path)

        hasher = hashlib.new(self.algorithm)

        with file_path.open("rb") as file:

            while chunk := file.read(self.chunk_size):
                hasher.update(chunk)

        return hasher.hexdigest()
