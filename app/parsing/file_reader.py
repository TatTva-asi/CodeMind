
from dataclasses import dataclass
from pathlib import Path

from app.parsing.content_classifier import ContentClassifier


@dataclass
class FileContent:
    path: str
    content: str | None
    encoding: str | None
    size_bytes: int
    status: str
    error: str | None = None


class FileReader:

    def __init__(
        self,
        max_file_size=2 * 1024 * 1024,
        sample_size=8192
    ):
        self.max_file_size = max_file_size
        self.sample_size = sample_size

        self.classifier = ContentClassifier()

    def read(self, file_path: str | Path) -> FileContent:

        path = Path(file_path)

        try:
            size = path.stat().st_size

            # Reject excessively large files.
            if size > self.max_file_size:
                return FileContent(
                    str(path), None, None, size,
                    "too_large"
                )

            with path.open("rb") as file:

                raw_data = file.read(
                    self.max_file_size + 1
                )

            # Protect against files changing during reading.
            if len(raw_data) > self.max_file_size:
                return FileContent(
                    str(path), None, None, len(raw_data),
                    "too_large"
                )

            classification = self.classifier.classify(
                path,
                raw_data[:self.sample_size]
            )

            if classification.category == "binary":
                return FileContent(
                    str(path), None, None, size,
                    "binary"
                )

            if classification.category == "unknown":
                return FileContent(
                    str(path), None, None, size,
                    "unsupported_encoding"
                )

            # Decode UTF-8, supporting an optional BOM.
            try:
                content = raw_data.decode("utf-8-sig")

            except UnicodeDecodeError:
                return FileContent(
                    str(path), None, None, size,
                    "unsupported_encoding"
                )

            return FileContent(
                str(path),
                content,
                "utf-8",
                size,
                "success"
            )

        except OSError as exc:
            return FileContent(
                str(path), None, None, 0,
                "error", str(exc)
            )
