#        RepositoryManifest
#        │
#        ├── repository_path
#        ├── generated_at
#        ├── total_files
#        ├── total_directories
#        ├── language_summary
#        │
#        └── files[]
#            ├── path
#            ├── language
#            ├── category
#            ├── size
#            └── hash



import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class FileMetadata:
    path: str
    language: str
    category: str
    is_programming_language: bool
    size_bytes: int
    sha256: str


@dataclass
class RepositoryManifest:
    repository_path: str
    generated_at: str
    total_files: int
    total_directories: int
    language_summary: dict[str, int]
    files: list[FileMetadata] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    def save(self, output_path: str | Path):

        output_path = Path(output_path)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(
                self.to_dict(),
                file,
                indent=4
            )


class ManifestGenerator:

    def __init__(self, language_detector, file_hasher):
        self.language_detector = language_detector
        self.file_hasher = file_hasher

    def generate(self, root: Path, scan_result):

        files_metadata = []
        language_summary = {}
        errors = list(scan_result.errors)

        for relative_path in scan_result.files:

            absolute_path = root / relative_path

            try:
                language_info = self.language_detector.detect(
                    relative_path
                )

                file_hash = self.file_hasher.hash_file(
                    absolute_path
                )

                size = absolute_path.stat().st_size

                metadata = FileMetadata(
                    path=relative_path.as_posix(),
                    language=language_info.language,
                    category=language_info.category,
                    is_programming_language=(
                        language_info.is_programming_language
                    ),
                    size_bytes=size,
                    sha256=file_hash
                )

                files_metadata.append(metadata)

                language = language_info.language

                language_summary[language] = (
                    language_summary.get(language, 0) + 1
                )

            except OSError as exc:
                errors.append(
                    f"{relative_path}: {exc}"
                )

        return RepositoryManifest(
            repository_path=str(root),
            generated_at=datetime.now(
                timezone.utc
            ).isoformat(),
            total_files=len(files_metadata),
            total_directories=len(scan_result.directories),
            language_summary=language_summary,
            files=files_metadata,
            errors=errors
        )
