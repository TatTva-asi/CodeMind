
from pathlib import Path

from app.ingestion.ignore_rules import IgnoreRules
from app.ingestion.file_scanner import FileScanner
from app.ingestion.language_detector import LanguageDetector
from app.ingestion.hasher import FileHasher
from app.ingestion.manifest import ManifestGenerator


class RepositoryIngestor:

    def __init__(
        self,
        repository_path,
        extra_ignore_patterns=None
    ):

        self.root = Path(repository_path).resolve()

        if not self.root.exists():
            raise FileNotFoundError(
                f"Repository not found: {self.root}"
            )

        if not self.root.is_dir():
            raise NotADirectoryError(
                f"Expected a repository directory: {self.root}"
            )

        self.ignore_rules = IgnoreRules(
            extra_patterns=extra_ignore_patterns
        )

        self.scanner = FileScanner(
            self.root,
            self.ignore_rules
        )

        self.language_detector = LanguageDetector()
        self.file_hasher = FileHasher()

        self.manifest_generator = ManifestGenerator(
            self.language_detector,
            self.file_hasher
        )

    def ingest(self, manifest_path=None):

        print("Starting repository ingestion...")

        # Stage 1: Discover files.
        scan_result = self.scanner.scan()

        print(f"Discovered {len(scan_result.files)} files")

        # Stage 2: Generate repository metadata.
        manifest = self.manifest_generator.generate(
            self.root,
            scan_result
        )

        print("Repository ingestion completed.")
        print(f"Total files: {manifest.total_files}")
        print(f"Total directories: {manifest.total_directories}")

        # Stage 3: Optionally save manifest.
        if manifest_path is not None:
            manifest.save(manifest_path)
            print(f"Manifest saved to: {manifest_path}")

        return manifest
