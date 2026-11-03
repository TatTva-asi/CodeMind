
import hashlib
import tempfile
import unittest
from pathlib import Path

from app.ingestion.hasher import FileHasher


class TestFileHasher(unittest.TestCase):

    def test_hash_is_deterministic(self):

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "test.py"
            path.write_bytes(b"print('hello')")

            hasher = FileHasher()

            hash1 = hasher.hash_file(path)
            hash2 = hasher.hash_file(path)

            self.assertEqual(hash1, hash2)

    def test_changed_content_changes_hash(self):

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "test.py"

            hasher = FileHasher()

            path.write_bytes(b"hello")
            hash1 = hasher.hash_file(path)

            path.write_bytes(b"hello world")
            hash2 = hasher.hash_file(path)

            self.assertNotEqual(hash1, hash2)

    def test_matches_standard_sha256(self):

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "test.py"
            content = b"CodeMind"

            path.write_bytes(content)

            expected = hashlib.sha256(content).hexdigest()

            self.assertEqual(
                FileHasher().hash_file(path),
                expected
            )


if __name__ == "__main__":
    unittest.main()
