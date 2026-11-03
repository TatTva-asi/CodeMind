
import tempfile
import unittest
from pathlib import Path

from app.ingestion.file_scanner import FileScanner


class TestFileScanner(unittest.TestCase):

    def test_scanner_discovers_files_and_directories(self):

        with tempfile.TemporaryDirectory() as temp:

            root = Path(temp)

            (root / "app").mkdir()
            (root / "tests").mkdir()
            (root / ".venv").mkdir()

            (root / "app" / "main.py").touch()
            (root / "tests" / "test_main.py").touch()
            (root / ".venv" / "ignored.py").touch()
            (root / "README.md").touch()

            scanner = FileScanner(root)
            result = scanner.scan()

            files = {
                path.as_posix()
                for path in result.files
            }

            directories = {
                path.as_posix()
                for path in result.directories
            }

            self.assertIn("app/main.py", files)
            self.assertIn("tests/test_main.py", files)
            self.assertIn("README.md", files)

            self.assertNotIn(".venv/ignored.py", files)
            self.assertNotIn(".venv", directories)

            self.assertIn("app", directories)
            self.assertIn("tests", directories)

    def test_invalid_repository_path(self):

        with self.assertRaises(FileNotFoundError):
            FileScanner("nonexistent_repository")


if __name__ == "__main__":
    unittest.main()
